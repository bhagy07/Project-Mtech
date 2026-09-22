import asyncio
import os
import logging
from agent.ai_diagnostician import AIDiagnosticAgent, IncidentAnalysis
from agent.notifier import AlertNotifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("TestSimulator")

# Sample Simulated Log Trace from a Payment Microservice
MOCK_LOG_TRACE = """
2026-08-06 17:15:01.102 [main] INFO  c.c.payment.PaymentApplication - Starting PaymentApplication v1.0.0
2026-08-06 17:15:05.420 [http-nio-8081-exec-1] INFO  c.c.payment.service.PaymentService - Processing payment transaction TXN_998124
2026-08-06 17:15:05.890 [http-nio-8081-exec-1] ERROR c.c.payment.service.PaymentService - Payment processing failed
org.postgresql.util.PSQLException: FATAL: remaining connection slots are reserved for non-replication superuser connections
    at org.postgresql.core.v3.QueryExecutorImpl.receiveErrorResponse(QueryExecutorImpl.java:2555)
    at org.postgresql.core.v3.QueryExecutorImpl.processResults(QueryExecutorImpl.java:2287)
    at org.postgresql.core.v3.QueryExecutorImpl.execute(QueryExecutorImpl.java:323)
    at org.postgresql.jdbc.PgConnection.execute(PgConnection.java:436)
    at com.zaxxer.hikari.pool.PoolBase.newConnection(PoolBase.java:353)
    at com.zaxxer.hikari.pool.HikariPool.checkin(HikariPool.java:516)
    at com.company.payment.service.PaymentService.processTransaction(PaymentService.java:142)
2026-08-06 17:15:06.001 [http-nio-8081-exec-1] ERROR c.c.payment.controller.PaymentController - Global Exception Handler caught unhandled exception
"""

async def run_simulation():
    logger.info("Starting Agentic AI Incident Simulation...")
    
    agent = AIDiagnosticAgent(model_name="gemini-3.5-flash")
    
    service_name = "Payment Microservice (Simulated)"
    host = "172.20.32.168"
    log_lines = MOCK_LOG_TRACE.strip().split("\n")
    health_status = "UP"

    logger.info("Sending simulated log trace to AI Diagnostic Agent for RCA...")
    analysis: IncidentAnalysis = agent.analyze_logs_and_health(
        service_name=service_name,
        host=host,
        log_lines=log_lines,
        health_status=health_status
    )

    if analysis:
        print("\n=======================================================")
        print("[INFO] AI AGENT DIAGNOSTIC OUTPUT")
        print("=======================================================")
        print(f"Severity            : {analysis.severity}")
        print(f"Error Summary       : {analysis.error_summary}")
        print(f"Affected Component  : {analysis.affected_component}")
        print(f"Root Cause Analysis :\n{analysis.root_cause_analysis}")
        print("\nRecommended Fix Steps:")
        for idx, step in enumerate(analysis.recommended_fix, 1):
            print(f"  {idx}. {step}")
        print("=======================================================\n")
    else:
        logger.info("No critical issue detected by AI Agent.")

if __name__ == "__main__":
    asyncio.run(run_simulation())
