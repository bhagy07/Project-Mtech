import paramiko
import yaml
import os

def read_remote_nohups():
    print("=" * 70)
    print("[LOGS] READING REAL-TIME NOHUP LOGS FROM SERVERS")
    print("=" * 70)

    if not os.path.exists("config.yaml"):
        print("[ERROR] config.yaml not found!")
        return

    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    services = config.get("services", [])
    if not services:
        print("[WARNING] No services defined in config.yaml!")
        return

    for idx, srv in enumerate(services, 1):
        name = srv.get("name", "Unknown Service")
        host = srv.get("host", "")
        port = int(srv.get("ssh_port", 22))
        user = srv.get("ssh_user", "spotuser")
        key_path = srv.get("ssh_key_path", "")
        
        # We target the first configured log path (which is the nohup.out file)
        log_paths = srv.get("log_paths", [])
        nohup_path = log_paths[0] if log_paths else srv.get("log_path", "")

        if not nohup_path:
            print(f"\n[{idx}] {name} ({host}): No log path configured.")
            continue

        print(f"\n[{idx}] Connecting to {name} ({user}@{host}:{port})...")
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            if key_path and os.path.exists(key_path):
                ssh.connect(hostname=host, port=port, username=user, key_filename=key_path, timeout=6)
            else:
                ssh.connect(hostname=host, port=port, username=user, timeout=6)

            print(f"    [SUCCESS] SSH Connection established!")
            print(f"    Reading last 20 lines from remote path: {nohup_path}")
            print("-" * 70)

            # Run tail -n 20 to read remote nohup.out
            cmd = f"tail -n 20 {nohup_path}"
            stdin, stdout, stderr = ssh.exec_command(cmd)
            
            log_output = stdout.read().decode("utf-8", errors="ignore").strip()
            err_output = stderr.read().decode("utf-8", errors="ignore").strip()

            if log_output:
                print(log_output)
            elif err_output:
                print(f"[REMOTE ERROR] {err_output}")
            else:
                print("[INFO] Log file is currently empty.")

            print("-" * 70)
            ssh.close()

        except Exception as e:
            print(f"    [FAIL] Failed to connect or read logs -> {e}")

if __name__ == "__main__":
    read_remote_nohups()
