import asyncio
import yaml
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from tools.health_checker import HealthCheckerTool
from tools.log_fetcher import SSHLogFetcherTool
from agent.ai_diagnostician import AIDiagnosticAgent
from agent.notifier import AlertNotifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("NeMLOpsGuardian")

# Load Configuration
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

log_fetcher = SSHLogFetcherTool()
ai_agent = AIDiagnosticAgent(model_name=config["agent"]["ai_model"])
notifier = AlertNotifier(config)

async def monitor_cycle():
    """Main Agentic Execution Loop."""
    logger.info("--- Starting Autonomous Monitoring Cycle ---")

    # 1. Probing Microservices (172.26.6.171 & 172.26.6.168)
    for service in config.get("services", []):
        # Check Health Endpoint (Commented out as requested)
        # health = await HealthCheckerTool.check_service_health(service)
        health = {"status": "UP", "details": "Actuator probe disabled"}
        
        # Fetch New Log Entries over SSH (nohup.out + /logs/Trading/...)
        logs_by_path = log_fetcher.fetch_new_log_entries(service)

        # Flatten multi-source log streams for AI diagnostic engine
        all_log_lines = []
        for log_path, lines in logs_by_path.items():
            if lines:
                all_log_lines.append(f"=== Log Source: {log_path} ===")
                all_log_lines.extend(lines)

        # 2. AI Reasoning & Diagnostic Phase (Only invoked when errors or outages are detected)
        has_errors = ai_agent._has_error_indicators(all_log_lines)
        if has_errors or health["status"] == "DOWN":
            analysis = ai_agent.analyze_logs_and_health(
                service_name=service["name"],
                host=service["host"],
                log_lines=all_log_lines,
                health_status=health["status"]
            )

            # 3. Action Phase (Alert Dispatch)
            if analysis and analysis.has_critical_issue:
                logger.warning(f"AI Detected Issue in {service['name']}: {analysis.error_summary}")
                notifier.send_ai_incident_report(
                    service_name=service["name"],
                    host=service["host"],
                    analysis=analysis,
                    raw_logs="\n".join(all_log_lines[-35:]) if all_log_lines else "No log trace available. Health endpoint failed."
                )

    # 4. Check PostgreSQL Databases
    for db in config.get("databases", []):
        db_health = HealthCheckerTool.check_postgres_health(db)
        if db_health["status"] == "DOWN":
            logger.critical(f"Database DOWN: {db['name']} - {db_health.get('details')}")
            from agent.ai_diagnostician import IncidentAnalysis
            db_analysis = IncidentAnalysis(
                has_critical_issue=True,
                severity="CRITICAL",
                error_summary=f"PostgreSQL Database Unreachable: {db['name']}",
                root_cause_analysis=f"Database connection to {db['host']}:{db.get('port', 5432)} (DB: {db.get('dbname')}) failed. Error: {db_health.get('details')}",
                affected_component=f"Database: {db['name']}",
                recommended_fix=[
                    "Check PostgreSQL service status on the database host",
                    "Verify network connectivity and firewall rules for port 5432",
                    "Check database max_connections and review PostgreSQL server logs"
                ]
            )
            notifier.send_ai_incident_report(
                service_name=db["name"],
                host=db["host"],
                analysis=db_analysis,
                raw_logs=f"PostgreSQL Connection Failure:\n{db_health.get('details', 'No response from database host')}"
            )

async def main():
    scheduler = AsyncIOScheduler()
    interval = config["agent"].get("interval_seconds", 1800)

    logger.info(f"NeML OpsGuardian Monitor started. Scheduling checks every {interval}s ({interval/60:.0f} minutes).")
    
    # Run initial cycle immediately upon launch
    await monitor_cycle()

    scheduler.add_job(monitor_cycle, "interval", seconds=interval)
    scheduler.start()
    
    # Keep the async main loop running indefinitely
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
