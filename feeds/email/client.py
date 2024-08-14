import dataclasses
import smtplib
import ssl
from email.header import Header
from email.mime.text import MIMEText
from typing import Sequence


@dataclasses.dataclass(frozen=True)
class Configuration:
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    sender: str
    recipients: Sequence[str]


@dataclasses.dataclass(frozen=True)
class EmailMessage:
    subject: str
    body: str


class EmailClient:
    def __init__(self, configuration: Configuration):
        self.configuration = configuration

    def send_email(self, email: EmailMessage) -> None:
        raise NotImplementedError


class StandardSMTP(EmailClient):

    def send_email(self, email: EmailMessage) -> None:
        mime_message = self._create_message_str(email)
        context = ssl.create_default_context()
        with smtplib.SMTP(host=self.configuration.smtp_host, port=self.configuration.smtp_port) as mail_server:
            mail_server.starttls(context=context)
            mail_server.login(self.configuration.smtp_user, self.configuration.smtp_password)
            mail_server.send_message(mime_message)

    def _create_message_str(self, message: EmailMessage) -> MIMEText:
        mime_text_message = MIMEText(message.body, "html", "utf-8")
        mime_text_message["Subject"] = Header(message.subject, "utf-8")
        mime_text_message["From"] = self.configuration.sender
        mime_text_message["To"] = self.configuration.recipients[0]

        return mime_text_message
