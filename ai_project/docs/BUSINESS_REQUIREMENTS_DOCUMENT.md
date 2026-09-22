# Business Requirements Document (BRD)
## Autonomous SRE Observability & GenAI Incident Remediation Platform
**Product Name:** NeML OpsGuardian  
**Organization:** National e-Markets Limited (NeML)  
**Document Version:** 1.0  
**Status:** Approved & Implemented  
**Date:** September 2026  

---

## 1. Executive Summary

In mission-critical electronic commodity trading and financial settlement environments, system downtime or delayed incident response directly translates to financial loss, operational bottlenecks, and regulatory impact. **NeML OpsGuardian** is an enterprise-grade, autonomous Site Reliability Engineering (SRE) and observability platform designed to proactively monitor distributed microservices, databases, and web gateways, automate real-time log ingestion across heterogeneous remote servers, and execute instant GenAI-powered Root Cause Analysis (RCA) with automated incident alerting.

---

## 2. Problem Statement

### 2.1 Current Operational Challenges
1. **Dispersed Server Infrastructure & Log Fragmentation:**
   - Multiple backend nodes (172.26.6.171, 172.26.6.168, 172.80.10.213, etc.) maintain log files across distinct directories (`/code/`, `/logs/Trading/`, date-wise subdirectories like `07-Sep-26/`, user-specific trader files).
   - SRE engineers must manually SSH into multiple Linux instances to tail logs and grep for errors.

2. **High Mean Time to Detect (MTTD) & Mean Time to Resolve (MTTR):**
   - When a microservice (e.g., Payment Gateway, NPG_UMP, or Scheduler) experiences degradation, identifying the exact stack trace, affected user, and root cause requires manual log correlation across heterogeneous date formats and gigabytes of output.

3. **Alert Fatigue & Delayed Notification:**
   - Conventional monitoring either overwhelms engineers with false alarms or fails to alert when silent application-level exceptions occur inside `nohup.out` or trader batch logs.

4. **Lack of Automated SRE Expertise During Off-Hours:**
   - Non-business hours incidents require on-call escalation without immediate actionable remediation recommendations.

---

## 3. Proposed Solution

**NeML OpsGuardian** establishes an autonomous, non-intrusive monitoring fabric across NeML’s server cluster:
- **Continuous SSH Log Streamer:** Line-offset tracking daemon that consumes only delta log updates over secure SSH/SFTP with negligible CPU/memory footprint on host servers.
- **Multi-Format Enterprise Date Engine:** Automated discovery of rotated and date-stamped logs (`dd-MMM-yy`, `YYYY-MM-DD`, `DD-MM-YYYY`, Syslog, unpadded timestamps).
- **GenAI Diagnostic Reasoner:** Leverages Google Gemini LLM with Pydantic structured output models to extract error summaries, determine severity, isolate the affected component, identify root causes, and provide step-by-step remediation fixes.
- **Enterprise Notification Hub:** Throttled SMTP alerting system dispatching executive HTML email reports to SRE teams.
- **Unified Command Portal:** Interactive Streamlit SRE console offering real-time health matrices, live log tailing, trader folder exploration, and on-demand AI RCA.

---

## 4. Key Business Requirements

| ID | Requirement Category | Requirement Description | Priority |
| :--- | :--- | :--- | :--- |
| **BR-01** | **Infrastructure Health** | Real-time TCP/SSH reachability, Tomcat process validation, and PostgreSQL port probes across all nodes. | High |
| **BR-02** | **Multi-Path Log Ingestion** | Dynamic discovery and ingestion of logs across standard files (`nohup.out`), date-based folders (`07-Sep-26`), and trader paths. | Critical |
| **BR-03** | **Zero-Intrusion Footprint** | Avoid heavy server agents; perform all remote diagnostics via lightweight SSH/SFTP streaming. | Critical |
| **BR-04** | **Autonomous AI RCA** | Automatically analyze error traces using GenAI to produce structured diagnosis and exact resolution steps. | Critical |
| **BR-05** | **Static Asset Filtering** | Prevent false positives by filtering out frontend bundles (`.js`, `.css`, `.map`, `.html`) from error scans. | Medium |
| **BR-06** | **Incident Alerting & Throttling** | Dispatch HTML incident emails with severity flags and rate-limiting (throttling) to prevent alert flooding. | High |
| **BR-07** | **Interactive SRE Portal** | Centralized web dashboard with KPI metric cards, date filters, live tailing, and one-click log downloads. | High |

---

## 5. System Architecture & Modules

### Detailed Module Breakdown

#### Module 1: Infrastructure Health Matrix (`tools/health_checker.py`)
- Executes parallel background probes across:
  - **Spring Boot Services:** Active host SSH status and log streaming viability.
  - **Web & Tomcat Gateways:** Process existence validation via `ps aux | grep Bootstrap`.
  - **Databases:** Direct TCP socket connection probe on port `5432` for PostgreSQL nodes.

#### Module 2: Distributed Log Streamer & Multi-Path Engine (`tools/log_fetcher.py`)
- Tracks log read offsets (`self.offsets`) to stream newly generated lines incrementally.
- Expands dynamic date tokens (`{DATE:dd-MMM-yy}`, `{DATE:yyyy-MM-dd}`, `{TODAY}`).
- Discovers user/trader folders (e.g. `/logs/UMPeMandi/users/KT1114/`) with direct log access and custom keyword filtering.
- Automatically excludes static web/Angular assets (`.js`, `.css`, `.map`, `.html`).

#### Module 3: GenAI Autonomous Diagnostic Agent (`agent/ai_diagnostician.py`)
- Pre-filters logs using regex heuristics (`ERROR`, `Exception`, `NullPointerException`, `Timeout`, `500`).
- Prompts Google Gemini LLM using strict Pydantic schemas:
  - `has_critical_issue` (boolean)
  - `severity` (CRITICAL, HIGH, MEDIUM, LOW)
  - `affected_component` (subsystem identifier)
  - `error_summary` (one-sentence executive headline)
  - `root_cause_analysis` (technical explanation)
  - `recommended_fix` (numbered actionable resolution steps)

#### Module 4: Incident Notification & Alert Throttler (`agent/notifier.py`)
- Dispatches styled, responsive HTML emails to on-call engineers via SSL/TLS SMTP.
- Enforces per-service alert throttling (e.g. 1 alert per 30 minutes) to prevent notification fatigue.

#### Module 5: SRE Command Center & Web Portal (`app.py`)
- High-level KPI status cards (Monitored Services, Database Nodes, System Status %, Active Alerts).
- Sub-tab categorization: `⚙️ Microservices`, `🅰️ Frontend & Web`, `🗄️ Databases`.
- 1-Click diagnostic popups, log downloads, and manual AI RCA trigger.

---

## 6. Technology Stack, Frameworks & Databases

| Layer | Component / Technology | Purpose |
| :--- | :--- | :--- |
| **Language & Runtime** | Python 3.10+, `asyncio` | Asynchronous concurrent background execution |
| **User Interface** | Streamlit 1.30+ | High-performance operational dashboard |
| **Remote Connectivity** | Paramiko (SSH2 / SFTP) | Agentless remote server log ingestion & process probing |
| **AI / LLM Reasoner** | Google Gemini (1.5 Flash / Pro) | Structured SRE Root Cause Analysis & Fix Generation |
| **Data Validation** | Pydantic v2 | Strict JSON schema enforcement for AI outputs |
| **Task Scheduling** | APScheduler (AsyncIOScheduler) | Periodic 30-second autonomous polling cycles |
| **Configuration** | PyYAML | Declarative service, credentials, and path management |
| **Database Target** | PostgreSQL 14+ / 16+ | Direct TCP socket health probing & telemetry |
| **Notification** | Python `smtplib` + `email.mime` | Enterprise SSL/TLS email dispatch |

---

## 7. Business Use Cases

### Use Case 1: Silent Microservice Exception Detection
- **Trigger:** A database pool exhaustion or `NullPointerException` occurs in `PaymentGateWayService`.
- **System Action:** OpsGuardian ingests the trace within 30s $\rightarrow$ GenAI diagnoses connection leak $\rightarrow$ SRE team receives an email with exact fix instructions before users submit complaints.

### Use Case 2: Multi-Trader Date Log Investigation
- **Trigger:** A specific market participant (`KT1114`) reports a failed order during trading hours.
- **System Action:** SRE selects the service $\rightarrow$ navigates to "Discover Date & Trader Subfolders" $\rightarrow$ filters by user `KT1114` $\rightarrow$ views/downloads matched error lines or runs instant AI RCA.

### Use Case 3: Offline Database Failover Warning
- **Trigger:** PostgreSQL database at `172.26.6.171:5432` goes down or refuses connections.
- **System Action:** OpsGuardian flags the node as `OFFLINE` $\rightarrow$ increments active incident counters on the dashboard $\rightarrow$ triggers critical failover notification.

---

## 8. Business Impact & ROI Analysis

| Metric | Before OpsGuardian (Manual) | With OpsGuardian (Autonomous) | Improvement / ROI |
| :--- | :--- | :--- | :--- |
| **Mean Time to Detect (MTTD)** | 15 – 45 Minutes | **< 30 Seconds** | **98% Faster Detection** |
| **Mean Time to Resolve (MTTR)** | 45 – 120 Minutes | **10 – 15 Minutes** | **75% Reduction in Downtime** |
| **SRE Manual Effort** | High (SSH into 5+ nodes manually) | Zero (Automated telemetry & AI RCA) | **~25 Hours Saved / Engineer / Month** |
| **Incident Visibility** | Fragmented across server logs | Centralized single-pane dashboard | **100% Unified Infrastructure View** |
| **Alert Quality** | Raw logs or noisy spam | Actionable GenAI fix recommendations | **Elimination of Alert Fatigue** |

---

## 9. Conclusion

NeML OpsGuardian transforms reactive server troubleshooting into a **predictive, autonomous SRE operations center**. By unifying multi-node SSH streaming, intelligent date and trader folder exploration, and Google Gemini GenAI diagnostics, the platform guarantees maximum uptime, rapid incident resolution, and operational excellence for NeML's critical trading ecosystem.
