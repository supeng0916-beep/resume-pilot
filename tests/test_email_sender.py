from __future__ import annotations

from email.message import EmailMessage

from core.email_sender import SmtpConfig, build_report_email, send_report_email


class FakeSmtp:
    sent_messages: list[EmailMessage] = []
    login_calls: list[tuple[str, str]] = []

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port

    def __enter__(self) -> "FakeSmtp":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def login(self, username: str, password: str) -> None:
        self.login_calls.append((username, password))

    def send_message(self, message: EmailMessage) -> None:
        self.sent_messages.append(message)


def test_send_report_email_skips_when_smtp_config_missing(monkeypatch) -> None:
    for key in [
        "HR_SMTP_HOST",
        "HR_SMTP_USERNAME",
        "HR_SMTP_PASSWORD",
        "HR_SMTP_FROM",
    ]:
        monkeypatch.delenv(key, raising=False)

    result = send_report_email(
        recipient="hr@example.com",
        subject="报告",
        report_markdown="# 批量候选人评估汇总",
    )

    assert result.sent is False
    assert "SMTP 配置不完整" in result.message


def test_build_report_email_adds_markdown_attachment() -> None:
    message = build_report_email(
        sender="system@example.com",
        recipient="hr@example.com",
        subject="报告",
        report_markdown="# 批量候选人评估汇总",
        attachment_name="batch.md",
    )

    assert message["From"] == "system@example.com"
    assert message["To"] == "hr@example.com"
    assert message["Subject"] == "报告"
    assert len(list(message.iter_attachments())) == 1


def test_send_report_email_uses_smtp_client() -> None:
    FakeSmtp.sent_messages = []
    FakeSmtp.login_calls = []
    config = SmtpConfig(
        host="smtp.example.com",
        port=465,
        username="system@example.com",
        password="secret",
        sender="system@example.com",
    )

    result = send_report_email(
        recipient="hr@example.com",
        subject="报告",
        report_markdown="# 批量候选人评估汇总",
        config=config,
        smtp_factory=FakeSmtp,
    )

    assert result.sent is True
    assert FakeSmtp.login_calls == [("system@example.com", "secret")]
    assert FakeSmtp.sent_messages[0]["To"] == "hr@example.com"
