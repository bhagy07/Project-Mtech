import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, Any
from agent.ai_diagnostician import IncidentAnalysis

logger = logging.getLogger(__name__)

class AlertNotifier:
    """Formulates HTML Emails and handles anti-spam deduplication."""

    def __init__(self, config: Dict[str, Any]):
        self.cfg = config["alerts"]
        self.sent_history: Dict[str, datetime] = {}

    def is_throttled(self, key: str) -> bool:
        last_sent = self.sent_history.get(key)
        if not last_sent:
            return False
        throttle_limit = timedelta(minutes=self.cfg.get("throttle_minutes", 15))
        return datetime.now() - last_sent < throttle_limit

    def send_ai_incident_report(self, service_name: str, host: str, analysis: IncidentAnalysis, raw_logs: str):
        throttle_key = f"{service_name}_{analysis.error_summary}"
        if self.is_throttled(throttle_key):
            logger.info(f"Alert throttled for {throttle_key}")
            return

        subject = f"🚨 [{analysis.severity}] Agentic Alert: {service_name} on {host}"
        
        fixes_html = "".join([f"<li>{fix}</li>" for fix in analysis.recommended_fix])

        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f6f9; padding: 20px;">
            <div style="max-width: 700px; margin: auto; background: white; border-radius: 8px; padding: 25px; border-left: 6px solid #dc3545;">
                <h2 style="color: #dc3545; margin-top: 0;">🚨 AI Agent Incident Report</h2>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <tr><td><strong>Service:</strong></td><td>{service_name}</td></tr>
                    <tr><td><strong>Server IP:</strong></td><td>{host}</td></tr>
                    <tr><td><strong>Severity:</strong></td><td><span style="background: #dc3545; color: white; padding: 3px 8px; border-radius: 4px;">{analysis.severity}</span></td></tr>
                    <tr><td><strong>Issue:</strong></td><td>{analysis.error_summary}</td></tr>
                    <tr><td><strong>Timestamp:</strong></td><td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
                </table>

                <div style="background: #e9ecef; border-radius: 6px; padding: 15px; margin-bottom: 20px;">
                    <h3 style="margin-top: 0; color: #343a40;">🤖 AI Root Cause Analysis (RCA)</h3>
                    <p style="color: #495057;">{analysis.root_cause_analysis}</p>
                </div>

                <div style="background: #d4edda; border-radius: 6px; padding: 15px; margin-bottom: 20px; color: #155724;">
                    <h3 style="margin-top: 0;">🛠️ Recommended Fix Steps</h3>
                    <ul>{fixes_html}</ul>
                </div>

                <details>
                    <summary style="cursor: pointer; color: #0056b3; font-weight: bold;">Show Raw Exception Stack Trace</summary>
                    <pre style="background: #212529; color: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; font-size: 12px;">{raw_logs}</pre>
                </details>
            </div>
        </body>
        </html>
        """

        self._send_email(subject, body_html)
        self.sent_history[throttle_key] = datetime.now()

    def _send_email(self, subject: str, html_content: str):
        import os
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.cfg.get("smtp_user", "alerts@neml.in")
        msg["To"] = self.cfg.get("recipient_email", "uppfunds@neml.in")
        msg.attach(MIMEText(html_content, "html"))

        smtp_host = self.cfg.get("smtp_host", "smtp.gmail.com")
        smtp_port = int(self.cfg.get("smtp_port", 587))
        smtp_user = self.cfg.get("smtp_user", "")
        smtp_pass = os.environ.get("SMTP_PASS") or self.cfg.get("smtp_pass", "")
        if smtp_pass in ["YOUR_SMTP_PASSWORD", "YOUR_GOOGLE_APP_PASSWORD", "YOUR_16_CHAR_GOOGLE_APP_PASSWORD"]:
            smtp_pass = ""

        try:
            if smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
                if smtp_port != 25:
                    server.starttls()

            if smtp_pass and smtp_user:
                server.login(smtp_user, smtp_pass)

            server.sendmail(msg["From"], [msg["To"]], msg.as_string())
            server.quit()
            logger.info(f"HTML Alert email sent successfully: {subject} to {msg['To']}")
        except Exception as e:
            logger.error(f"Failed to dispatch email alert: {e}")
