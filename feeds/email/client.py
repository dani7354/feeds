from email.header import Header
from email.mime.text import MIMEText
import dataclasses
import smtplib
import ssl


@dataclasses.dataclass(frozen=True)
class Configuration:
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    sender: str


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
    def __init__(self, configuration: Configuration):
        super().__init__(configuration)

    def send_email(self, message: EmailMessage) -> None:
        mime_message = self._create_message_str(message)
        context = ssl.create_default_context()
        with smtplib.SMTP(host=self.configuration.smtp_host, port=self.configuration.smtp_port) as mail_server:
            mail_server.starttls(context=context)
            mail_server.login(self.configuration.smtp_user, self.configuration.smtp_password)
            mail_server.send_message(mime_message)

    @staticmethod
    def _create_message_str(message: EmailMessage) -> MIMEText:
        mime_text_message = MIMEText(message.body, "html", "utf-8")
        mime_text_message["Subject"] = Header(message.subject, "utf-8")
        mime_text_message["From"] = message.sender
        mime_text_message["To"] = message.recipient

        return mime_text_message
