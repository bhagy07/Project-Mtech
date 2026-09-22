# Project-Mtech
OpsGuardian
An autonomous, Agentic AI-driven infrastructure monitoring and incident diagnosis system built in Python. Designed for multi-server enterprise environments running Angular Frontends, Java Spring Boot Microservices, and PostgreSQL Databases.

🌟 Key Features
Multi-Server Infrastructure Probing: Asynchronously checks HTTP health endpoints (/actuator/health or Angular web roots) and PostgreSQL database connections across separate IPs (172.20.32.168, etc.).
Incremental Remote SSH Log Tailing: Streams newly appended log lines over SSH using line offset tracking without re-reading entire log files.
Cognitive Root Cause Analysis (RCA): Powered by Google GenAI, the AI Agent analyzes stack traces, filters log noise, classifies severity, explains root cause, and provides step-by-step developer fix instructions.
Anti-Spam Email Alerting Engine: Sends formatted HTML emails with collapsible stack traces and automated rate-limiting to prevent alert storms.
🏗️ Tech Stack & AI Architecture
Category	Component / Technology	Purpose
UI Framework	Streamlit (>=1.31.0)	Enterprise operations dashboard & log viewer
Agentic AI SDK	Google GenAI Python SDK (google-genai >= 0.1.1)	Cognitive RCA & structured error classification
LLM Reasoning Model	Gemini 3.5 Flash (gemini-3.5-flash)	Zero-shot log analysis, severity assignment & fix generation
Embedding Models	None (Direct In-Context Stream) / Optional: text-embedding-004	Real-time logs are streamed directly to context window
Vector Database	None (Stateful In-Memory Stream) / Optional: pgvector (PostgreSQL)	Dynamic SSH offset tracking & Pydantic in-memory state
Orchestration / Scheduler	APScheduler (>=3.10.4 - AsyncIOScheduler)	Asynchronous non-blocking background monitoring cycles
Data Schema & Validation	Pydantic V2 (>=2.6.0)	Structured JSON outputs & type-safe RCA incident schemas
Remote Transport (SSH/SFTP)	Paramiko (>=3.4.0)	SSH key authentication, remote log inspection & file tailing
HTTP Probe	HTTPX (>=0.27.0)	Asynchronous Spring Boot Actuator health endpoint probing
Database Driver	Psycopg2-binary (>=2.9.9)	PostgreSQL TCP handshake & connection pool health verification
📂 Architecture & Project Structure
ai_project/
├── config.yaml                # Infrastructure inventory, SSH keys & SMTP credentials
├── main_agent.py              # Main Autonomous Scheduler Loop
├── test_agent.py              # Dry-run simulator for testing AI RCA locally
├── requirements.txt           # Python dependencies
├── agent/
│   ├── ai_diagnostician.py    # GenAI Agent for cognitive incident analysis
│   └── notifier.py            # Anti-Spam HTML Email Engine
└── tools/
    ├── health_checker.py      # HTTP & PostgreSQL connectivity probe
    └── log_fetcher.py         # Remote SSH log tailer with offset tracking
🚀 Getting Started
1. Prerequisites
Python 3.10+
Google Gemini API Key (GEMINI_API_KEY)
2. Environment Setup
# Clone the repository
git clone https://codecommit.neml.in/funds/ump_npg/ai_project.git
cd ai_project

# Install dependencies
pip install -r requirements.txt

# Export your Gemini API Key (obtain from https://aistudio.google.com/app/apikey)
export GEMINI_API_KEY="AIzaSy_YOUR_API_KEY_HERE"
3. Dry-Run Simulator (Testing)
Run the built-in simulator to test how the AI Agent analyzes a PostgreSQL connection pool exhaustion stack trace:

python test_agent.py
4. Configuration
Edit config.yaml to map your actual servers, log file paths, SSH keys, and SMTP server:

services:
  - name: "Payment Microservice"
    type: "SPRING_BOOT"
    host: "172.20.32.168"
    health_url: "http://172.20.32.168:8081/actuator/health"
    ssh_user: "deploy"
    ssh_key_path: "/keys/id_rsa"
    log_path: "/var/log/payment-service/application.log"
5. Launch Modern Streamlit UI Dashboard
python -m streamlit run app.py
Access the rich visual dashboard at http://localhost:8501

6. Launch Autonomous Background OpsGuardian Monitor
python main_agent.py
🔐 Portal Authentication & User Roles
NeML OpsGuardian includes built-in role-based access control configured in config.yaml:

Username	Default Password	Role	Description
devops	devops@neml123	DevOps Engineer	Full access to live tailing, SSH offsets, and service configurations.
developer	dev@neml123	Developer	Log inspection, date-based querying, and GenAI RCA diagnostics.
admin	admin@neml123	Administrator	Full infrastructure control and user credentials management.
Credentials and users can be dynamically updated from Tab 4 (Dynamic Configurator) or directly inside config.yaml.

🛠️ Security Best Practices
SSH Key Auth: Always use passwordless SSH keys (/keys/id_rsa) instead of plaintext passwords.
Environment Variables: Pass sensitive SMTP passwords and API keys via environment variables or secret managers.
