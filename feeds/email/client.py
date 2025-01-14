import dataclasses
import smtplib
import ssl
from email.header import Header
from email.message import Message
from email.mime.base import MIMEBase
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
    gpg_home_path: str | None = None


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
        mime_message = self._create_message(email)
        context = ssl.create_default_context()
        with smtplib.SMTP(host=self.configuration.smtp_host, port=self.configuration.smtp_port) as mail_server:
            mail_server.starttls(context=context)
            mail_server.login(self.configuration.smtp_user, self.configuration.smtp_password)
            mail_server.send_message(mime_message)

    def _create_message(self, message: EmailMessage) -> MIMEBase:
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

    def _create_message(self, message: EmailMessage) -> MIMEBase:
        mime_message = MIMEBase(_maintype="multipart", _subtype="encrypted", protocol="application/pgp-encrypted")
        mime_message.add_header(_name="Content-Type", _value="multipart/mixed", protected_headers="v1")
        mime_message[MimeMessageField.SUBJECT] = Header(message.subject, self.encoding)
        mime_message[MimeMessageField.FROM] = self.configuration.sender
        mime_message[MimeMessageField.TO] = self.configuration.recipients[0]

        pgp_version_info_message = Message()
        pgp_version_info_message.add_header(_name="Content-Type", _value="application/pgp-encrypted")
        pgp_version_info_message.add_header(_name="Content-Description", _value="PGP/MIME version identification")
        pgp_version_info_message.set_payload("Version: 1" + "\n")

        pgp_payload = Message()
        pgp_payload.add_header(_name="Content-Type", _value="application/octet-stream", name="encrypted.asc")
        pgp_payload.add_header(_name="Content-Description", _value="OpenPGP encrypted message")
        pgp_payload.add_header(_name="Content-Disposition", _value="inline", filename="encrypted.asc")

        encrypted_message = MIMEText(message.body, "html", self.encoding)
        pgp_payload.set_payload(
            self._pgp_service.encrypt_string(encrypted_message.as_string(), self.configuration.recipients[0]))

        mime_message.attach(pgp_version_info_message)
        mime_message.attach(pgp_payload)

        return mime_message


class DummyEmailClient(EmailClient):
    """ Dummy email client for debugging locally """

    def send_email(self, email: EmailMessage) -> None:
        print(f"Sending email with subject: {email.subject} to {self.configuration.recipients[0]}")
