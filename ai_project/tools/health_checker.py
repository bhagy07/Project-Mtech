import httpx
import socket
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

try:
    import psycopg2
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False
    logger.warning("psycopg2 module not found. Falling back to TCP socket connectivity checks for PostgreSQL.")

class HealthCheckerTool:
    """Probes HTTP Actuator endpoints, Angular URLs, and PostgreSQL databases."""

    @staticmethod
    async def check_service_health(service_cfg: Dict[str, Any]) -> Dict[str, Any]:
        url = service_cfg["health_url"]
        name = service_cfg["name"]
        host = service_cfg["host"]

        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(url)
                is_up = response.status_code == 200
                return {
                    "target": name,
                    "type": service_cfg.get("type", "HTTP"),
                    "host": host,
                    "status": "UP" if is_up else "DOWN",
                    "details": f"HTTP Status: {response.status_code}"
                }
            except Exception as e:
                return {
                    "target": name,
                    "type": service_cfg.get("type", "HTTP"),
                    "host": host,
                    "status": "DOWN",
                    "details": f"Connection Failed: {str(e)}"
                }

    @staticmethod
    def check_postgres_health(db_cfg: Dict[str, Any]) -> Dict[str, Any]:
        name = db_cfg["name"]
        host = db_cfg["host"]
        port = int(db_cfg.get("port", 5432))

        import os
        password = db_cfg.get("password", "")
        if password and password.startswith("${") and password.endswith("}"):
            env_var = password[2:-1]
            password = os.environ.get(env_var, "")

        # 1. Verify TCP socket connection to database host & port
        try:
            with socket.create_connection((host, port), timeout=2.5):
                pass
        except Exception as sock_err:
            return {"target": name, "type": "POSTGRESQL", "host": host, "status": "DOWN", "details": f"Endpoint unreachable on port {port}: {sock_err}"}

        # 2. If password is supplied and psycopg2 available, run full query ping
        if HAS_PSYCOPG2 and password:
            try:
                conn = psycopg2.connect(
                    host=host,
                    port=port,
                    dbname=db_cfg.get("dbname", "postgres"),
                    user=db_cfg.get("user", "postgres"),
                    password=password,
                    connect_timeout=3
                )
                conn.close()
                return {"target": name, "type": "POSTGRESQL", "host": host, "status": "UP", "details": "Active DB connection (Query Ping OK)"}
            except Exception as e:
                # If error is merely no password or auth, but TCP port answered
                err_str = str(e)
                if "no password supplied" in err_str or "password authentication failed" in err_str:
                    return {"target": name, "type": "POSTGRESQL", "host": host, "status": "UP", "details": "Port 5432 Reachable & Connected (Auth Required)"}
                return {"target": name, "type": "POSTGRESQL", "host": host, "status": "DOWN", "details": err_str}
        else:
            return {"target": name, "type": "POSTGRESQL", "host": host, "status": "UP", "details": f"Port {port} Active & Connected"}

    @staticmethod
    def check_tomcat_health(service_cfg: Dict[str, Any]) -> Dict[str, Any]:
        """
        Probes Apache Tomcat process status over SSH and verifies Frontend AngularJS web app HTTP response.
        """
        name = service_cfg["name"]
        host = service_cfg["host"]
        ssh_user = service_cfg.get("ssh_user", "spotuser")
        ssh_key = service_cfg.get("ssh_key_path")
        port = int(service_cfg.get("ssh_port", 22))
        frontend_url = service_cfg.get("health_url") or service_cfg.get("frontend_url", "")
        tomcat_service_name = service_cfg.get("tomcat_service_name", "tomcat")

        # 1. Check HTTP frontend response if URL is provided
        http_status_detail = "No URL"
        http_ok = True
        if frontend_url:
            try:
                r = httpx.get(frontend_url, timeout=3.5, follow_redirects=True)
                if r.status_code in [200, 302, 304]:
                    http_status_detail = f"HTTP {r.status_code} OK"
                else:
                    http_status_detail = f"HTTP {r.status_code}"
                    http_ok = False
            except Exception as ex:
                http_status_detail = f"HTTP Failed: {str(ex)[:35]}"
                http_ok = False

        # 2. Check Tomcat process over SSH
        import paramiko, os
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        tomcat_process_running = False
        ssh_details = ""
        try:
            if ssh_key and os.path.exists(ssh_key):
                ssh.connect(hostname=host, port=port, username=ssh_user, key_filename=ssh_key, timeout=5)
            else:
                ssh.connect(hostname=host, port=port, username=ssh_user, timeout=5)

            # Check if tomcat / catalina process is running
            cmd_ps = "ps aux | grep -iE 'org.apache.catalina.startup.Bootstrap|[t]omcat' | grep -v grep"
            stdin, stdout, stderr = ssh.exec_command(cmd_ps)
            ps_out = stdout.read().decode("utf-8", errors="ignore").strip()

            if ps_out:
                tomcat_process_running = True
                ssh_details = "Tomcat Process: RUNNING"
            else:
                # Try systemctl status
                cmd_sys = f"systemctl is-active {tomcat_service_name} 2>/dev/null"
                stdin, stdout, stderr = ssh.exec_command(cmd_sys)
                sys_out = stdout.read().decode("utf-8", errors="ignore").strip()
                if sys_out == "active":
                    tomcat_process_running = True
                    ssh_details = f"Systemd {tomcat_service_name}: ACTIVE"
                else:
                    tomcat_process_running = False
                    ssh_details = "Tomcat Process: STOPPED"

            ssh.close()
        except Exception as e:
            ssh_details = f"SSH Check: {str(e)[:35]}"

        # Overall Status
        if tomcat_process_running or (http_ok and frontend_url and "Failed" not in http_status_detail):
            status = "UP"
        else:
            status = "DOWN"

        return {
            "target": name,
            "type": "ANGULARJS_TOMCAT",
            "host": host,
            "status": status,
            "tomcat_running": tomcat_process_running,
            "http_status": http_status_detail,
            "details": f"{ssh_details} | {http_status_detail}"
        }

    @staticmethod
    def check_service_health_sync(service_cfg: Dict[str, Any]) -> Dict[str, Any]:
        """
        Checks Spring Boot microservice process health over SSH using ps -ef | grep <jar/name> and HTTP/TCP probe.
        """
        import paramiko, os
        name = service_cfg.get("name", "Unknown")
        host = service_cfg["host"]
        port = int(service_cfg.get("ssh_port", 22))
        ssh_user = service_cfg.get("ssh_user", "spotuser")
        ssh_key = service_cfg.get("ssh_key_path", "")
        health_url = service_cfg.get("health_url", "")
        app_path = service_cfg.get("app_path", "").strip()

        # 1. HTTP Probe if Actuator URL is configured
        if health_url:
            try:
                r = httpx.get(health_url, timeout=3.0)
                if r.status_code == 200:
                    return {"target": name, "host": host, "status": "UP", "details": f"HTTP {r.status_code} OK (Actuator)"}
            except Exception:
                pass

        # 2. Process check over SSH (ps -ef | grep <name or .jar>)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            if ssh_key and os.path.exists(ssh_key):
                ssh.connect(hostname=host, port=port, username=ssh_user, key_filename=ssh_key, timeout=5)
            else:
                ssh.connect(hostname=host, port=port, username=ssh_user, timeout=5)

            jar_search = name.replace(" ", "")
            cmd_ps = f"ps -ef | grep -iE '{jar_search}|{app_path}|\\.jar' | grep -v grep"
            stdin, stdout, stderr = ssh.exec_command(cmd_ps)
            ps_lines = [l.strip() for l in stdout.readlines() if l.strip()]
            ssh.close()

            if ps_lines:
                return {"target": name, "host": host, "status": "UP", "details": f"Process Active: {ps_lines[0][:60]}"}
            else:
                return {"target": name, "host": host, "status": "DOWN", "details": "No matching process found running on host"}
        except Exception as ex:
            return {"target": name, "host": host, "status": "DOWN", "details": f"SSH check error: {str(ex)[:35]}"}

    @staticmethod
    def restart_remote_service(service_cfg: Dict[str, Any], custom_cmd: str = None) -> Dict[str, Any]:
        """
        Executes a remote service restart command over SSH and verifies post-restart health.
        Human-in-the-Loop: Intended to be invoked ONLY after explicit human approval in UI.
        """
        import paramiko, os, time
        name = service_cfg.get("name", "Unknown Service")
        host = service_cfg["host"]
        port = int(service_cfg.get("ssh_port", 22))
        ssh_user = service_cfg.get("ssh_user", "spotuser")
        ssh_key = service_cfg.get("ssh_key_path", "")
        srv_type = service_cfg.get("type", "SPRING_BOOT")
        app_path = service_cfg.get("app_path", "").strip()

        # Determine restart command
        cmd = custom_cmd.strip() if custom_cmd and custom_cmd.strip() else service_cfg.get("restart_cmd")
        if not cmd:
            # Extract port from health_url or default
            srv_port = "8080"
            health_url = service_cfg.get("health_url", "")
            if health_url:
                import urllib.parse
                try:
                    parsed = urllib.parse.urlparse(health_url)
                    if parsed.port:
                        srv_port = str(parsed.port)
                except Exception:
                    pass

            is_angular_tomcat = srv_type in ["ANGULARJS_TOMCAT", "ANGULARJS", "TOMCAT", "STANDALONE_TOMCAT", "FRONTEND_WEB"]
            jar_name_hint = name.replace(" ", "")

            if is_angular_tomcat:
                # Angular / Tomcat service: kill port & process first, then run ./startup.sh
                if app_path:
                    cmd = f"cd {app_path} && (PORT={srv_port}; PID=$(lsof -ti :$PORT 2>/dev/null || ps -ef | grep -iE 'tomcat|catalina|{jar_name_hint}|{app_path}' | grep -v grep | awk '{{print $2}}'); [ -n \"$PID\" ] && kill -9 $PID 2>/dev/null || fuser -k -9 $PORT/tcp 2>/dev/null || true); sleep 2; ([ -f ./startup.sh ] && ./startup.sh || ([ -f startup.sh ] && sh startup.sh || (/opt/tomcat/bin/startup.sh 2>/dev/null || sudo systemctl restart tomcat)))"
                else:
                    cmd = f"(PORT={srv_port}; PID=$(lsof -ti :$PORT 2>/dev/null || ps -ef | grep -iE 'tomcat|catalina' | grep -v grep | awk '{{print $2}}'); [ -n \"$PID\" ] && kill -9 $PID 2>/dev/null || fuser -k -9 $PORT/tcp 2>/dev/null || true); sleep 2; ./startup.sh"
            else:
                # Spring Boot / Microservice: kill port & ps -ef process first, then run ./start.sh
                if app_path:
                    cmd = f"cd {app_path} && (PORT={srv_port}; PID=$(lsof -ti :$PORT 2>/dev/null || ps -ef | grep -iE '{jar_name_hint}|{app_path}|\\.jar' | grep -v grep | awk '{{print $2}}'); [ -n \"$PID\" ] && kill -9 $PID 2>/dev/null || fuser -k -9 $PORT/tcp 2>/dev/null || true); sleep 2; ([ -f ./start.sh ] && ./start.sh || ([ -f start.sh ] && sh start.sh || nohup java -jar *.jar > nohup.out 2>&1 &))"
                else:
                    cmd = f"(PORT={srv_port}; PID=$(lsof -ti :$PORT 2>/dev/null || ps -ef | grep -iE '{jar_name_hint}|\\.jar' | grep -v grep | awk '{{print $2}}'); [ -n \"$PID\" ] && kill -9 $PID 2>/dev/null || fuser -k -9 $PORT/tcp 2>/dev/null || true); sleep 2; ./start.sh"

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            if ssh_key and os.path.exists(ssh_key):
                ssh.connect(hostname=host, port=port, username=ssh_user, key_filename=ssh_key, timeout=8)
            else:
                ssh.connect(hostname=host, port=port, username=ssh_user, timeout=8)

            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
            out_str = stdout.read().decode("utf-8", errors="ignore").strip()
            err_str = stderr.read().decode("utf-8", errors="ignore").strip()
            ssh.close()

            # Wait briefly for process to initialize before probing
            time.sleep(2)

            # Probe health
            if srv_type in ["ANGULARJS_TOMCAT", "TOMCAT", "STANDALONE_TOMCAT", "FRONTEND_WEB"]:
                post_health = HealthCheckerTool.check_tomcat_health(service_cfg)
            else:
                post_health = HealthCheckerTool.check_service_health_sync(service_cfg)

            return {
                "success": True,
                "service_name": name,
                "host": host,
                "cmd_executed": cmd,
                "stdout": out_str,
                "stderr": err_str,
                "post_health": post_health,
                "msg": f"Restart command executed on {host}. Post-restart status: {post_health.get('status', 'UNKNOWN')}"
            }
        except Exception as e:
            return {
                "success": False,
                "service_name": name,
                "host": host,
                "cmd_executed": cmd,
                "stdout": "",
                "stderr": str(e),
                "post_health": {"status": "UNKNOWN", "details": str(e)},
                "msg": f"Failed executing restart on {host}: {e}"
            }

    @staticmethod
    def stop_remote_service(service_cfg: Dict[str, Any], custom_cmd: str = None) -> Dict[str, Any]:
        """
        Executes a remote service kill/stop command over SSH and verifies that the process is terminated.
        Human-in-the-Loop: Intended to be invoked ONLY after explicit human approval in UI.
        """
        import paramiko, os, time
        name = service_cfg.get("name", "Unknown Service")
        host = service_cfg["host"]
        port = int(service_cfg.get("ssh_port", 22))
        ssh_user = service_cfg.get("ssh_user", "spotuser")
        ssh_key = service_cfg.get("ssh_key_path", "")
        srv_type = service_cfg.get("type", "SPRING_BOOT")
        app_path = service_cfg.get("app_path", "")

        cmd = custom_cmd.strip() if custom_cmd and custom_cmd.strip() else service_cfg.get("stop_cmd")
        if not cmd:
            # Extract port from health_url or default
            srv_port = "8080"
            health_url = service_cfg.get("health_url", "")
            if health_url:
                import urllib.parse
                try:
                    parsed = urllib.parse.urlparse(health_url)
                    if parsed.port:
                        srv_port = str(parsed.port)
                except Exception:
                    pass

            is_angular_tomcat = srv_type in ["ANGULARJS_TOMCAT", "ANGULARJS", "TOMCAT", "STANDALONE_TOMCAT", "FRONTEND_WEB"]

            if is_angular_tomcat:
                # Kill port / tomcat process or run shutdown.sh
                if app_path:
                    cmd = f"cd {app_path} && (PORT={srv_port}; PID=$(lsof -ti :$PORT 2>/dev/null || fuser $PORT/tcp 2>/dev/null | awk '{{print $1}}'); [ -n \"$PID\" ] && kill -9 $PID 2>/dev/null || fuser -k -9 $PORT/tcp 2>/dev/null || pkill -9 -u {ssh_user} -f 'tomcat|catalina|{app_path}' 2>/dev/null || true); ([ -f ./shutdown.sh ] && ./shutdown.sh 2>/dev/null || (/opt/tomcat/bin/shutdown.sh 2>/dev/null || true))"
                else:
                    cmd = f"(PORT={srv_port}; PID=$(lsof -ti :$PORT 2>/dev/null || fuser $PORT/tcp 2>/dev/null | awk '{{print $1}}'); [ -n \"$PID\" ] && kill -9 $PID 2>/dev/null || fuser -k -9 $PORT/tcp 2>/dev/null || pkill -9 -u {ssh_user} -f 'tomcat|catalina' 2>/dev/null || true)"
            else:
                # Microservice: kill port first or run stop.sh
                if app_path:
                    cmd = f"cd {app_path} && ([ -f ./stop.sh ] && ./stop.sh 2>/dev/null || ([ -f stop.sh ] && sh stop.sh 2>/dev/null || true)); (PORT={srv_port}; PID=$(lsof -ti :$PORT 2>/dev/null || fuser $PORT/tcp 2>/dev/null | awk '{{print $1}}'); [ -n \"$PID\" ] && kill -9 $PID 2>/dev/null || fuser -k -9 $PORT/tcp 2>/dev/null || pkill -9 -u {ssh_user} -f '{app_path}' 2>/dev/null || true)"
                else:
                    cmd = f"(PORT={srv_port}; PID=$(lsof -ti :$PORT 2>/dev/null || fuser $PORT/tcp 2>/dev/null | awk '{{print $1}}'); [ -n \"$PID\" ] && kill -9 $PID 2>/dev/null || fuser -k -9 $PORT/tcp 2>/dev/null || pkill -9 -u {ssh_user} -f '{name}' 2>/dev/null || true)"

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            if ssh_key and os.path.exists(ssh_key):
                ssh.connect(hostname=host, port=port, username=ssh_user, key_filename=ssh_key, timeout=8)
            else:
                ssh.connect(hostname=host, port=port, username=ssh_user, timeout=8)

            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
            out_str = stdout.read().decode("utf-8", errors="ignore").strip()
            err_str = stderr.read().decode("utf-8", errors="ignore").strip()
            ssh.close()

            time.sleep(2)

            # Probe health to confirm service is down
            if srv_type in ["ANGULARJS_TOMCAT", "TOMCAT", "STANDALONE_TOMCAT", "FRONTEND_WEB"]:
                post_health = HealthCheckerTool.check_tomcat_health(service_cfg)
            else:
                post_health = HealthCheckerTool.check_service_health_sync(service_cfg)

            is_stopped = (post_health.get("status") == "DOWN")

            return {
                "success": True,
                "service_name": name,
                "host": host,
                "cmd_executed": cmd,
                "stdout": out_str,
                "stderr": err_str,
                "post_health": post_health,
                "is_stopped": is_stopped,
                "msg": f"Kill/Stop command executed on {host}. Status: {'STOPPED (DOWN)' if is_stopped else post_health.get('status')}"
            }
        except Exception as e:
            return {
                "success": False,
                "service_name": name,
                "host": host,
                "cmd_executed": cmd,
                "stdout": "",
                "stderr": str(e),
                "post_health": {"status": "UNKNOWN", "details": str(e)},
                "is_stopped": False,
                "msg": f"Failed executing kill/stop on {host}: {e}"
            }

