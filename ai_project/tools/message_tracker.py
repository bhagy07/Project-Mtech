import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class DynamicMessageTrackerEngine:
    """
    Database-free, file/memory-backed runtime engine for:
    1. sms_template (Dynamic HTML/text message templates with %s placeholders)
    2. message_tracker_archive (Processed transcode tracking records)
    """

    def __init__(self, storage_dir: str = "data"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        self.templates_file = os.path.join(storage_dir, "sms_templates.json")
        self.archive_file = os.path.join(storage_dir, "message_tracker_archive.json")
        self.templates: Dict[str, Dict[str, Any]] = self._load_templates()
        self.archives: List[Dict[str, Any]] = self._load_archives()

    def _save_json(self, path: str, data: Any):
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving {path}: {e}")

    def _load_templates(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.templates_file):
            try:
                with open(self.templates_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error reading {self.templates_file}: {e}")
        
        default_tpl = {
            "7783": {
                "transcode": "7783",
                "vendor_id": 4,
                "message_type": 2,
                "forward_type": "E",
                "tc_comment": "Online Advance Payment File Details",
                "sms_template": (
                    "<p>Dear %s ,</p>\n"
                    "<p>We are pleased to inform you that the Advance Wallet Payment Collection Details for the date %s will be processed on %s.</p>\n"
                    "<p>Please find the attached Excel file containing the details of Advance Wallet Payment Collection.</p>\n"
                    "<p>If you require any further information, feel free to contact us.</p>\n"
                    "<p>Best regards,<br>"
                    "<strong>Rashtriya e Market Services Private Limited</strong>,<br>"
                    "UMP Support (080) 22864833<br>"
                    "UMP Support (080) 22864844<br>"
                    "Email: csg@remsl.in</p>"
                ),
                "reply_to": "sayali.dongre@neml.in",
                "reply_to_name": "AskUs"
            },
            "7782": {
                "transcode": "7782",
                "vendor_id": 4,
                "message_type": 2,
                "forward_type": "E",
                "tc_comment": "Daily Wallet Payment Collection Details",
                "sms_template": (
                    "<p>Dear %s ,</p>\n"
                    "<p>Please find attached the Daily Wallet Payment Collection Details for the date %s to %s.</p>\n"
                    "<p>If you require any further information or reconciliation details, please reach out to UMP Support.</p>\n"
                    "<p>Best regards,<br>"
                    "<strong>Rashtriya e Market Services Private Limited (ReMS)</strong><br>"
                    "Email: ump@remsl.in</p>"
                ),
                "reply_to": "ump@remsl.in",
                "reply_to_name": "UMP Support"
            }
        }
        self._save_json(self.templates_file, default_tpl)
        return default_tpl

    def _load_archives(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.archive_file):
            try:
                with open(self.archive_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error reading {self.archive_file}: {e}")
        
        default_archive = [
            {
                "msg_id": 282268.0,
                "msg_transcode": "7782",
                "msg_message_type": "E",
                "msg_parameters": "MCK1!15-Jul-2026!17-Jul-2026",
                "msg_mobile_nos": None,
                "msg_recipients_to": "sushmitha.m@remsl.in",
                "msg_recipients_cc": "ump@remsl.in",
                "msg_recipients_bcc": None,
                "msg_subject": "MCK1 - Daily Wallet Payment Collection Details for the date 15-Jul-2026",
                "msg_status": "SUCCESS",
                "msg_created_on": "2026-07-16 16:31:32.218902",
                "msg_has_attachment": 1.0,
                "msg_attachment_location": "/code/s3drive/UMP/UMP_KA_UAT/WALLET_PAYMNET_EMAIL/16-Jul-2026/MCK1/",
                "msg_attachment_filename": "MCK1-15-Jul-2026.csv",
                "msg_owner": "MCK1",
                "msg_modified_on": "2026-07-16 16:33:36.727552",
                "msg_market_code": None,
                "msg_cm_id": None,
                "msg_usr_type": None,
                "msg_message_txt": "<p>Dear MCK1 ,</p>\n<p>Please find attached the Daily Wallet Payment Collection Details for the date 15-Jul-2026 to 17-Jul-2026.</p>",
                "msg_trans_type": None,
                "msg_trans_status": "DELIVERED"
            }
        ]
        self._save_json(self.archive_file, default_archive)
        return default_archive

    def get_all_templates(self) -> Dict[str, Dict[str, Any]]:
        return self.templates

    def get_templates(self) -> Dict[str, Dict[str, Any]]:
        return self.templates

    def get_all_archives(self) -> List[Dict[str, Any]]:
        return self.archives

    def get_template(self, transcode: str) -> Optional[Dict[str, Any]]:
        return self.templates.get(str(transcode).strip())

    def save_template(
        self,
        transcode: str,
        tc_comment: str,
        html_template: str,
        reply_to: str = "csg@remsl.in",
        reply_to_name: str = "AskUs",
        vendor_id: int = 4,
        message_type: int = 2,
        forward_type: str = "E"
    ) -> Dict[str, Any]:
        record = {
            "transcode": str(transcode).strip(),
            "vendor_id": int(vendor_id),
            "message_type": int(message_type),
            "forward_type": forward_type,
            "tc_comment": tc_comment.strip(),
            "sms_template": html_template,
            "reply_to": reply_to.strip(),
            "reply_to_name": reply_to_name.strip()
        }
        self.templates[str(transcode).strip()] = record
        self._save_json(self.templates_file, self.templates)
        return record

    def delete_template(self, transcode: str) -> bool:
        transcode_str = str(transcode).strip()
        if transcode_str in self.templates:
            del self.templates[transcode_str]
            self._save_json(self.templates_file, self.templates)
            return True
        return False

    def dispatch_smtp_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        cc_email: Optional[str] = None,
        reply_to: Optional[str] = None,
        attachment_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Dispatches an HTML email using the configured SMTP server (Gmail/Internal Relay).
        """
        import smtplib
        import yaml
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.base import MIMEBase
        from email import encoders

        if not config:
            try:
                if os.path.exists("config.yaml"):
                    with open("config.yaml", "r", encoding="utf-8") as f:
                        config = yaml.safe_load(f) or {}
            except Exception as e:
                logger.error(f"Error loading config.yaml for SMTP: {e}")
                config = {}

        alert_cfg = config.get("alerts", {}) if config else {}
        smtp_host = alert_cfg.get("smtp_host", "smtp.gmail.com")
        smtp_port = int(alert_cfg.get("smtp_port", 465))
        smtp_user = alert_cfg.get("smtp_user", "alerts@neml.in")
        smtp_pass = os.environ.get("SMTP_PASS") or alert_cfg.get("smtp_pass", "")
        if smtp_pass in ["YOUR_SMTP_PASSWORD", "YOUR_GOOGLE_APP_PASSWORD", "YOUR_16_CHAR_GOOGLE_APP_PASSWORD"]:
            smtp_pass = ""

        msg = MIMEMultipart("mixed")
        msg["Subject"] = subject
        msg["From"] = smtp_user or "csg@remsl.in"
        msg["To"] = to_email
        if cc_email:
            msg["Cc"] = cc_email
        if reply_to:
            msg.add_header("Reply-To", reply_to)

        # Body part
        html_part = MIMEText(html_body, "html")
        msg.attach(html_part)

        # Attachment part
        if attachment_path and os.path.exists(attachment_path):
            try:
                with open(attachment_path, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f'attachment; filename="{os.path.basename(attachment_path)}"',
                )
                msg.attach(part)
            except Exception as e:
                logger.warning(f"Could not attach file {attachment_path}: {e}")

        recipients = [r.strip() for r in to_email.split(",") if r.strip()]
        if cc_email:
            recipients.extend([r.strip() for r in cc_email.split(",") if r.strip()])

        try:
            if smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
                if smtp_port != 25:
                    server.starttls()

            if smtp_pass and smtp_user:
                server.login(smtp_user, smtp_pass)

            server.sendmail(msg["From"], recipients, msg.as_string())
            server.quit()
            logger.info(f"Transcode email successfully dispatched to {recipients} (Subject: {subject})")
            return {"status": "SUCCESS", "message": f"Email delivered to {', '.join(recipients)}"}
        except Exception as e:
            err_msg = f"SMTP dispatch failed: {e}"
            logger.error(err_msg)
            return {"status": "FAILED", "error": err_msg}

    def process_transcode(
        self,
        msg_transcode: str,
        msg_parameters: str,
        msg_recipients_to: str,
        msg_recipients_cc: Optional[str] = None,
        msg_subject: Optional[str] = None,
        attachment_filename: Optional[str] = None,
        attachment_location: Optional[str] = None,
        msg_owner: str = "SYSTEM",
        status: str = "SUCCESS",
        dispatch_email: bool = False,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        transcode_str = str(msg_transcode).strip()
        template_obj = self.templates.get(transcode_str)

        param_list = [p.strip() for p in msg_parameters.split("!")] if msg_parameters else []

        if template_obj and template_obj.get("sms_template"):
            raw_template = template_obj["sms_template"]
            try:
                expected_args = raw_template.count("%s")
                padded_args = list(param_list) + [""] * max(0, expected_args - len(param_list))
                args_to_apply = tuple(padded_args[:expected_args])
                formatted_message_txt = raw_template % args_to_apply
            except Exception as e:
                formatted_message_txt = f"<p>Formatting Error: {e}</p>\n{raw_template}"
        else:
            formatted_message_txt = f"<p>Transcode {transcode_str} processed with parameters: {msg_parameters}</p>"

        new_msg_id = float(int(datetime.now().timestamp() * 1000) % 10000000)
        
        default_subject = template_obj.get("tc_comment") if template_obj else f"Notification {transcode_str}"
        if param_list:
            default_subject = f"{param_list[0]} - {default_subject}"

        actual_subject = msg_subject or default_subject
        dispatch_status = "DELIVERED" if status == "SUCCESS" else "FAILED"

        # If email dispatch requested
        if dispatch_email and msg_recipients_to:
            full_att_path = None
            if attachment_location and attachment_filename:
                full_att_path = os.path.join(attachment_location, attachment_filename)
            elif attachment_filename:
                full_att_path = attachment_filename

            reply_to_addr = template_obj.get("reply_to") if template_obj else None

            dispatch_res = self.dispatch_smtp_email(
                to_email=msg_recipients_to,
                subject=actual_subject,
                html_body=formatted_message_txt,
                cc_email=msg_recipients_cc,
                reply_to=reply_to_addr,
                attachment_path=full_att_path,
                config=config
            )
            if dispatch_res["status"] == "SUCCESS":
                status = "SUCCESS"
                dispatch_status = "DELIVERED"
            else:
                status = "FAILED"
                dispatch_status = f"FAILED: {dispatch_res.get('error')}"

        archive_record = {
            "msg_id": new_msg_id,
            "msg_transcode": transcode_str,
            "msg_message_type": "E",
            "msg_parameters": msg_parameters,
            "msg_mobile_nos": None,
            "msg_recipients_to": msg_recipients_to.strip() if msg_recipients_to else "",
            "msg_recipients_cc": msg_recipients_cc.strip() if msg_recipients_cc else None,
            "msg_recipients_bcc": None,
            "msg_subject": actual_subject,
            "msg_status": status,
            "msg_created_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
            "msg_has_attachment": 1.0 if attachment_filename else 0.0,
            "msg_attachment_location": attachment_location,
            "msg_attachment_filename": attachment_filename,
            "msg_owner": msg_owner,
            "msg_modified_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
            "msg_market_code": None,
            "msg_cm_id": None,
            "msg_usr_type": None,
            "msg_message_txt": formatted_message_txt,
            "msg_trans_type": None,
            "msg_trans_status": dispatch_status
        }

        self.archives.insert(0, archive_record)
        self._save_json(self.archive_file, self.archives)

        return archive_record

    def get_archives(
        self,
        transcode_filter: Optional[str] = None,
        recipient_filter: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        results = self.archives
        if transcode_filter:
            results = [r for r in results if transcode_filter.lower() in str(r.get("msg_transcode", "")).lower()]
        if recipient_filter:
            results = [r for r in results if recipient_filter.lower() in str(r.get("msg_recipients_to", "")).lower() or recipient_filter.lower() in str(r.get("msg_recipients_cc", "")).lower()]
        return results[:limit]
