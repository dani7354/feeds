import dataclasses
import smtplib
import ssl
from email.header import Header
from email.mime.text import MIMEText
from enum import StrEnum
from typing import Sequence

from feeds.service.encryption import PGPService


class MimeMessageField(StrEnum):
    SUBJECT = "Subject"
    FROM = "From"
    TO = "To"


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
    """ Base class for email clients """

    def __init__(self, configuration: Configuration):
        self.configuration = configuration

    def send_email(self, email: EmailMessage) -> None:
        """Should be overwritten by subclasses"""
        raise NotImplementedError


class StandardSMTP(EmailClient):
    """ Email client that sends emails using SMTP. Default email client. """

    encoding = "utf-8"

    def send_email(self, email: EmailMessage) -> None:
        mime_message = self._create_message_str(email)
        context = ssl.create_default_context()
        with smtplib.SMTP(host=self.configuration.smtp_host, port=self.configuration.smtp_port) as mail_server:
            mail_server.starttls(context=context)
            mail_server.login(self.configuration.smtp_user, self.configuration.smtp_password)
            mail_server.send_message(mime_message)

    def _create_message_str(self, message: EmailMessage) -> MIMEText:
        mime_text_message = MIMEText(message.body, "html", self.encoding)
        mime_text_message[MimeMessageField.SUBJECT] = Header(message.subject, self.encoding)
        mime_text_message[MimeMessageField.FROM] = self.configuration.sender
        mime_text_message[MimeMessageField.TO] = self.configuration.recipients[0]

        return mime_text_message


class EncryptedEmailClient(StandardSMTP):
    """" Email client that encrypts the email body using PGP (GnuPG) """

    def __init__(self, configuration: Configuration, pgp_service: PGPService):
        super().__init__(configuration)
        self._pgp_service = pgp_service

    def _create_message_str(self, message: EmailMessage) -> MIMEText:
        mime_text_message = MIMEText(
            self._pgp_service.encrypt_string(message.body, recipient=self.configuration.recipients[0]),
            "html",
            self.encoding)
        mime_text_message[MimeMessageField.SUBJECT] = Header(message.subject, self.encoding)
        mime_text_message[MimeMessageField.FROM] = self.configuration.sender
        mime_text_message[MimeMessageField.TO] = self.configuration.recipients[0]

        return mime_text_message


class DummyEmailClient(EmailClient):
    """ Dummy email client for debugging locally """

    def send_email(self, email: EmailMessage) -> None:
        print(f"Sending email with subject: {email.subject} to {self.configuration.recipients[0]}")
