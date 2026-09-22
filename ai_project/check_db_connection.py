import socket
import psycopg2
import yaml
import os
from dotenv import load_dotenv

load_dotenv()

def check_db_connections():
    print("=" * 60)
    print("[DIAGNOSTIC] NEML OPSGUARDIAN DATABASE CONNECTIVITY TEST")
    print("=" * 60)

    if not os.path.exists("config.yaml"):
        print("[ERROR] config.yaml not found!")
        return

    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    databases = config.get("databases", [])
    if not databases:
        print("[WARNING] No databases defined in config.yaml!")
        return

    for idx, db in enumerate(databases, 1):
        name = db.get("name", "Unknown DB")
        host = db.get("host", "")
        port = int(db.get("port", 5432))
        dbname = db.get("dbname", "")
        user = db.get("user", "")
        password = db.get("password", "")

        # Resolve password environment variables if configured
        if password.startswith("${") and password.endswith("}"):
            env_var = password[2:-1]
            password = os.environ.get(env_var, "")
            print(f"\n[{idx}] Testing Database: {name}")
            print(f"    Resolved password from env: ${env_var}")
        else:
            # Check env override
            env_key = f"DB_PASSWORD_{name.replace(' ', '_').upper()}"
            env_val = os.environ.get(env_key) or os.environ.get("DB_PASSWORD")
            if env_val:
                password = env_val
                print(f"\n[{idx}] Testing Database: {name}")
                print(f"    Using password from environment override: {env_key}")
            else:
                print(f"\n[{idx}] Testing Database: {name}")
                print(f"    Using password from config.yaml: {password}")

        print(f"    Target: {user}@{host}:{port}/{dbname}")

        # Step 1: TCP Port check
        try:
            with socket.create_connection((host, port), timeout=4):
                print("    [SUCCESS] Step 1: TCP Port Reachable")
        except Exception as e:
            print(f"    [FAIL] Step 1 FAILED: TCP connection to {host}:{port} timed out or was refused -> {e}")
            print("       -> Note: For AWS RDS, verify that the Security Group allows inbound connections from this IP.")
            continue

        # Step 2: Establish connection
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                dbname=dbname,
                user=user,
                password=password,
                connect_timeout=4
            )
            conn.close()
            print("    [SUCCESS] Step 2: PostgreSQL Database Authentication SUCCESSFUL!")
        except psycopg2.OperationalError as e:
            print(f"    [FAIL] Step 2 FAILED: PostgreSQL connection error -> {e}")
        except Exception as e:
            print(f"    [FAIL] Step 2 FAILED: Unexpected error -> {e}")

if __name__ == "__main__":
    check_db_connections()
