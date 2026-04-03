import logging
import os
import smtplib
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

_SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
_SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
_SMTP_USER = os.getenv("SMTP_USER")
_SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
_EMAIL_FROM = os.getenv("EMAIL_FROM", _SMTP_USER or "")
_EMAIL_TO = os.getenv("EMAIL_TO")


def send_email(subject: str, body: str) -> None:
    """发送邮件，配置不全或发送失败只记日志不抛异常"""
    if not all([_SMTP_USER, _SMTP_PASSWORD, _EMAIL_TO]):
        logger.debug("邮件配置不全，跳过发送")
        return

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = _EMAIL_FROM
    msg["To"] = _EMAIL_TO

    try:
        with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT) as server:
            server.starttls()
            server.login(_SMTP_USER, _SMTP_PASSWORD)
            server.send_message(msg)
        logger.info("邮件已发送至 %s", _EMAIL_TO)
    except Exception:
        logger.exception("邮件发送失败")
