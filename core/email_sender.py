from __future__ import annotations

import os
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Protocol

from dotenv import load_dotenv


@dataclass(frozen=True)
class SmtpConfig:
    host: str
    port: int
    username: str
    password: str
    sender: str
    use_ssl: bool = True


@dataclass(frozen=True)
class EmailDeliveryResult:
    sent: bool
    message: str


class SmtpClient(Protocol):
    def __enter__(self) -> "SmtpClient":
        ...

    def __exit__(self, exc_type, exc, traceback) -> None:
        ...

    def login(self, username: str, password: str) -> None:
        ...

    def send_message(self, message: EmailMessage) -> None:
        ...


def load_smtp_config_from_env() -> SmtpConfig | None:
    load_dotenv()
    host = os.getenv("HR_SMTP_HOST")
    username = os.getenv("HR_SMTP_USERNAME")
    password = os.getenv("HR_SMTP_PASSWORD")
    sender = os.getenv("HR_SMTP_FROM") or username
    if not host or not username or not password or not sender:
        return None

    port = int(os.getenv("HR_SMTP_PORT", "465"))
    use_ssl = os.getenv("HR_SMTP_USE_SSL", "true").lower() not in {"0", "false", "no"}
    return SmtpConfig(
        host=host,
        port=port,
        username=username,
        password=password,
        sender=sender,
        use_ssl=use_ssl,
    )


def build_report_email(
    *,
    sender: str,
    recipient: str,
    subject: str,
    report_markdown: str,
    attachment_name: str = "batch_report.md",
) -> EmailMessage:
    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(report_markdown)
    message.add_attachment(
        report_markdown.encode("utf-8"),
        maintype="text",
        subtype="markdown",
        filename=attachment_name,
    )
    return message


def send_report_email(
    *,
    recipient: str,
    subject: str,
    report_markdown: str,
    attachment_name: str = "batch_report.md",
    config: SmtpConfig | None = None,
    smtp_factory=None,
) -> EmailDeliveryResult:
    smtp_config = config or load_smtp_config_from_env()
    if smtp_config is None:
        return EmailDeliveryResult(
            sent=False,
            message="SMTP 配置不完整，未发送邮件。",
        )
    if not recipient.strip():
        return EmailDeliveryResult(sent=False, message="收件人为空，未发送邮件。")

    message = build_report_email(
        sender=smtp_config.sender,
        recipient=recipient.strip(),
        subject=subject.strip() or "Agentic HR 批量候选人评估报告",
        report_markdown=report_markdown,
        attachment_name=attachment_name,
    )

    factory = smtp_factory
    if factory is None:
        factory = smtplib.SMTP_SSL if smtp_config.use_ssl else smtplib.SMTP

    with factory(smtp_config.host, smtp_config.port) as smtp:
        smtp.login(smtp_config.username, smtp_config.password)
        smtp.send_message(message)

    return EmailDeliveryResult(sent=True, message=f"已发送报告到 {recipient.strip()}。")
