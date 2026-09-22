import os
import re
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from google import genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class IncidentAnalysis(BaseModel):
    has_critical_issue: bool = Field(description="True if an error/exception requiring engineering action was found")
    severity: str = Field(description="CRITICAL | HIGH | MEDIUM | LOW")
    error_summary: str = Field(description="Short title of the incident")
    root_cause_analysis: str = Field(description="AI explanation of why this crash or exception occurred")
    affected_component: str = Field(description="Name of the service or database impacted")
    recommended_fix: List[str] = Field(description="Step-by-step resolution steps for developers")


class AIDiagnosticAgent:
    """Agentic AI engine responsible for cognitive root cause analysis with multi-model failover and local SRE heuristic fallback."""

    FALLBACK_MODELS = [
        "gemini-3.6-flash",
        "gemini-2.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemini-2.5-flash",
        "gemini-1.5-flash"
    ]

    ERROR_PATTERNS = re.compile(
        r'\b(ERROR|FATAL|Exception|NullPointerException|OutOfMemory|SQLException|ConnectionRefused|TimeoutException|HttpServerErrorException|CannotCreateTransactionException|ConnectException)\b',
        re.IGNORECASE
    )

    def __init__(self, model_name: str = "gemini-3.6-flash"):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY environment variable is not set!")
        self.client = genai.Client(api_key=api_key) if api_key else None
        self.model_name = model_name

    def _has_error_indicators(self, log_lines: List[str]) -> bool:
        """Checks if log lines contain genuine error patterns before spending Gemini API quota."""
        if not log_lines:
            return False
        sample = "\n".join(log_lines[-40:])
        return bool(self.ERROR_PATTERNS.search(sample))

    def _local_sre_heuristic_analysis(self, service_name: str, host: str, log_lines: List[str], health_status: str, error_context: str = "") -> IncidentAnalysis:
        """
        High-precision local SRE heuristic engine that runs when Gemini API quota (429) is exhausted or offline.
        Parses stack traces and generates structured RCA without needing external LLM calls.
        """
        raw_text = "\n".join(log_lines[-40:]) if log_lines else ""
        
        if health_status == "DOWN":
            return IncidentAnalysis(
                has_critical_issue=True,
                severity="CRITICAL",
                error_summary=f"Microservice Outage / Unreachable: {service_name}",
                root_cause_analysis=f"Health check probe on {service_name} ({host}) failed or connection was refused. The service process may have halted or port is blocked.",
                affected_component=service_name,
                recommended_fix=[
                    "Check system process status on host via SSH (`ps aux | grep java` or `systemctl status`)",
                    "Verify network connectivity and firewall port access",
                    "Inspect remote log files for crash dumps or fatal signals"
                ]
            )

        # Detect specific Java / Spring / Database exception types
        if re.search(r'NullPointerException', raw_text, re.I):
            return IncidentAnalysis(
                has_critical_issue=True,
                severity="HIGH",
                error_summary=f"NullPointerException in {service_name}",
                root_cause_analysis="An uninitialized object reference was accessed in the application code without prior null verification. This typically happens when an optional request parameter or database query returns null.",
                affected_component=service_name,
                recommended_fix=[
                    "Inspect the top stack trace line to identify the exact class and variable causing NPE",
                    "Add defensive null-checks or Optional.ofNullable() handling before accessing object methods",
                    "Validate incoming request payload schema against expected fields"
                ]
            )
        elif re.search(r'(ConnectionRefused|ConnectException|CannotCreateTransactionException|HikariPool|PSQLException)', raw_text, re.I):
            return IncidentAnalysis(
                has_critical_issue=True,
                severity="CRITICAL",
                error_summary=f"Database / Downstream Connection Failure in {service_name}",
                root_cause_analysis="The microservice failed to establish a connection with the database or downstream TCP endpoint. Potential causes include connection pool exhaustion, incorrect credentials, or target host being unreachable.",
                affected_component=f"{service_name} (Data Layer)",
                recommended_fix=[
                    "Verify database availability and check max_connections limit",
                    "Inspect database credentials and host/port in application.properties / application.yml",
                    "Verify firewall rules between application host and database server"
                ]
            )
        elif re.search(r'(OutOfMemoryError|Heap space|GC overhead)', raw_text, re.I):
            return IncidentAnalysis(
                has_critical_issue=True,
                severity="CRITICAL",
                error_summary=f"JVM OutOfMemoryError in {service_name}",
                root_cause_analysis="The Java Virtual Machine ran out of heap memory space due to excessive memory consumption or a memory leak in caching/large dataset processing.",
                affected_component=service_name,
                recommended_fix=[
                    "Increase JVM heap space allocation (e.g. -Xmx2g -Xms1g)",
                    "Analyze heap dump file with Eclipse Memory Analyzer (MAT)",
                    "Review recent large bulk query operations or unclosed streaming resources"
                ]
            )
        elif re.search(r'(TimeoutException|SocketTimeoutException|Read timed out)', raw_text, re.I):
            return IncidentAnalysis(
                has_critical_issue=True,
                severity="HIGH",
                error_summary=f"Downstream Network Timeout in {service_name}",
                root_cause_analysis="A downstream service or external API call exceeded the configured read/connect timeout threshold.",
                affected_component=service_name,
                recommended_fix=[
                    "Check network latency and health of the target downstream API",
                    "Review circuit breaker timeout configuration in application properties",
                    "Implement asynchronous retries with exponential backoff"
                ]
            )
        elif self._has_error_indicators(log_lines):
            # General error found in logs
            return IncidentAnalysis(
                has_critical_issue=True,
                severity="MEDIUM",
                error_summary=f"Application Error Detected in {service_name}",
                root_cause_analysis=f"The application log stream contains runtime error events requiring engineering review. {error_context}",
                affected_component=service_name,
                recommended_fix=[
                    "Review the recent log trace in Tab 3 (Live SSH Terminal Logs)",
                    "Check recent code deployments or configuration changes",
                    "Verify upstream request payloads"
                ]
            )
        else:
            # Healthy logs
            return IncidentAnalysis(
                has_critical_issue=False,
                severity="LOW",
                error_summary=f"Normal Operation: {service_name}",
                root_cause_analysis="Analyzed logs represent healthy operational activity. Zero critical exceptions or crashes found.",
                affected_component=service_name,
                recommended_fix=["No action required. Systems operating within normal parameters."]
            )


    def analyze_logs_and_health(
        self, 
        service_name: str, 
        host: str, 
        log_lines: List[str], 
        health_status: str
    ) -> Optional[IncidentAnalysis]:
        
        # Step 1: Quota Optimization - If logs are healthy and status is UP, do not waste Gemini API calls!
        has_errors = self._has_error_indicators(log_lines)
        if not has_errors and health_status == "UP":
            return IncidentAnalysis(
                has_critical_issue=False,
                severity="LOW",
                error_summary=f"Normal Operation: {service_name}",
                root_cause_analysis="No critical exceptions or failures found in the examined log trace. All systems operating normally.",
                affected_component=service_name,
                recommended_fix=["No action required. Systems healthy."]
            )

        # Step 2: Fallback if Gemini client is not configured
        if not self.client:
            logger.warning("GenAI Client not initialized. Using local SRE heuristic engine.")
            return self._local_sre_heuristic_analysis(service_name, host, log_lines, health_status)

        # Step 3: Call Gemini API with Multi-Model Failover
        prompt = f"""
        You are an expert Autonomous Site Reliability Engineer (SRE) monitoring microservices.
        Analyze the following operational data for service: '{service_name}' running on IP '{host}'.

        Current Health Check Status: {health_status}

        Recent Raw Log Stream:
        --------------------------------------------------
        {chr(10).join(log_lines[-40:]) if log_lines else 'No log lines provided'}
        --------------------------------------------------

        Task:
        1. Determine if a genuine exception or service failure is present. Ignore normal INFO logs.
        2. Perform Root Cause Analysis (RCA) explaining WHY it failed (e.g. Postgres DB connection pool exhausted, NullPointerException on payload, HTTP 500 downstream timeout).
        3. Assign severity (CRITICAL, HIGH, MEDIUM, LOW).
        4. Provide concrete, step-by-step developer remediation steps.
        """

        # Try configured model, then fallback models
        models_to_try = [self.model_name] + [m for m in self.FALLBACK_MODELS if m != self.model_name]

        last_error = None
        for model_candidate in models_to_try:
            try:
                response = self.client.models.generate_content(
                    model=model_candidate,
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json",
                        "response_schema": IncidentAnalysis,
                    }
                )
                
                analysis = IncidentAnalysis.model_validate_json(response.text)
                return analysis

            except Exception as e:
                err_msg = str(e)
                last_error = err_msg
                logger.warning(f"Model '{model_candidate}' failed: {err_msg[:120]}... Trying next fallback.")
                if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                    # Continue trying other models or fallback to local SRE parser
                    continue

        # Step 4: If all external Gemini models hit 429 rate-limit, fallback smoothly to local SRE heuristic engine
        logger.info("All Gemini API models rate-limited (429). Executing local SRE heuristic analysis.")
        return self._local_sre_heuristic_analysis(service_name, host, log_lines, health_status, error_context="(Analyzed via Local SRE Engine)")

