import paramiko
import yaml
import socket
import os

def check_server_connections():
    print("=" * 60)
    print("[DIAGNOSTIC] NEML OPSGUARDIAN SSH / SFTP KEY CONNECTIVITY TEST")
    print("=" * 60)

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
        log_paths = srv.get("log_paths", [srv.get("log_path")])

        print(f"\n[{idx}] Testing Target: {name}")
        print(f"    Target Host: {user}@{host}:{port}")
        print(f"    Key Path: {key_path}")

        # 1. Test TCP Socket Connectivity to Port 22
        try:
            with socket.create_connection((host, port), timeout=4):
                print("    [SUCCESS] Step 1: TCP Port 22 Reachable")
        except Exception as e:
            print(f"    [FAIL] Step 1 FAILED: Cannot connect to {host}:{port} -> {e}")
            continue

        # 2. Inspect SSH Key Format (.ppk vs OpenSSH)
        if not key_path or not os.path.exists(key_path):
            print(f"    [WARNING] Step 2: Private key file '{key_path}' does NOT exist locally!")
            print("       -> Will attempt standard SSH agent / default key auth...")
        else:
            if key_path.endswith(".ppk"):
                print("    [INFO] Key Format: PuTTY (.ppk) detected.")
                print("       Note: Paramiko requires OpenSSH format keys.")
                print("       Convert .ppk to OpenSSH using PuTTYgen: Conversions -> Export OpenSSH Key.")

        # 3. Test SSH Authentication
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            if key_path and os.path.exists(key_path) and not key_path.endswith(".ppk"):
                ssh.connect(hostname=host, port=port, username=user, key_filename=key_path, timeout=5)
            else:
                ssh.connect(hostname=host, port=port, username=user, timeout=5)

            print(f"    [SUCCESS] Step 2: SSH Authentication SUCCESSFUL for {user}@{host}!")

            # 4. Verify Remote Log Paths
            print("    [INFO] Step 3: Verifying Remote Log File Paths:")
            for path in log_paths:
                if not path:
                    continue
                cmd = f"ls -la {path} 2>/dev/null | head -n 1"
                stdin, stdout, stderr = ssh.exec_command(cmd)
                out = stdout.read().decode().strip()
                if out:
                    print(f"       [FOUND] {path} -> ({out})")
                else:
                    print(f"       [NOT FOUND / EMPTY] {path}")

            ssh.close()

        except paramiko.AuthenticationException:
            print(f"    [FAIL] Step 2 FAILED: Authentication Failed for user '{user}' with key '{key_path}'.")
            print("       -> Verify that your public key is added to remote ~/.ssh/authorized_keys on the server.")
        except Exception as e:
            print(f"    [FAIL] Step 2 FAILED: SSH connection error -> {e}")

if __name__ == "__main__":
    check_server_connections()
