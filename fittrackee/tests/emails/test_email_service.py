# ruff: noqa: E501 -- preserve the independent email text expectation.
from unittest.mock import Mock, patch

from flask import Flask

from fittrackee import email_service

expected_en_text_body = """Hi test,

You recently requested to reset your password for your FitTrackee account. Use the link below to reset it.
This password reset link is only valid for 3 seconds.

Reset your password: http://localhost/password-reset?token=xxx

For security, this request was received from a Linux device using Firefox.
If you did not request a password reset, please ignore this email.

Thanks,
The FitTrackee Team
http://localhost"""


class TestEmailServiceSend:
    email_data = {
        "expiration_delay": "3 seconds",
        "username": "test",
        "password_reset_url": "http://localhost/password-reset?token=xxx",
        "operating_system": "Linux",
        "browser_name": "Firefox",
        "fittrackee_url": "http://localhost",
    }

    @staticmethod
    def assert_smtp(smtp: Mock) -> None:
        assert smtp.sendmail.call_count == 1
        args, _ = smtp.sendmail.call_args
        assert args[0] == "fittrackee@example.com"
        assert args[1] == "test@test.com"
        assert expected_en_text_body in args[2]

    @patch("smtplib.SMTP_SSL")
    @patch("smtplib.SMTP")
    def test_it_sends_message(
        self, mock_smtp: Mock, mock_smtp_ssl: Mock, app: Flask
    ) -> None:
        email_service.send(
            template="password_reset_request",
            lang="en",
            recipient="test@test.com",
            data=self.email_data,
        )

        smtp = mock_smtp.return_value.__enter__.return_value
        assert smtp.login.call_count == 1
        smtp.starttls.assert_not_called()
        self.assert_smtp(smtp)

    @patch("smtplib.SMTP_SSL")
    @patch("smtplib.SMTP")
    def test_it_sends_message_with_ssl(
        self, mock_smtp: Mock, mock_smtp_ssl: Mock, app_ssl: Flask
    ) -> None:
        email_service.send(
            template="password_reset_request",
            lang="en",
            recipient="test@test.com",
            data=self.email_data,
        )

        smtp = mock_smtp_ssl.return_value.__enter__.return_value
        assert smtp.login.call_count == 1
        smtp.starttls.assert_not_called()
        self.assert_smtp(smtp)

    @patch("smtplib.SMTP_SSL")
    @patch("smtplib.SMTP")
    def test_it_sends_message_with_tls(
        self, mock_smtp: Mock, mock_smtp_ssl: Mock, app_tls: Flask
    ) -> None:
        email_service.send(
            template="password_reset_request",
            lang="en",
            recipient="test@test.com",
            data=self.email_data,
        )

        smtp = mock_smtp.return_value.__enter__.return_value
        assert smtp.login.call_count == 1
        assert smtp.starttls.call_count == 1
        self.assert_smtp(smtp)

    @patch("smtplib.SMTP_SSL")
    @patch("smtplib.SMTP")
    def test_it_sends_message_without_authentication(
        self, mock_smtp: Mock, mock_smtp_ssl: Mock, app_wo_email_auth: Flask
    ) -> None:
        email_service.send(
            template="password_reset_request",
            lang="en",
            recipient="test@test.com",
            data=self.email_data,
        )

        smtp = mock_smtp.return_value.__enter__.return_value
        smtp.login.assert_not_called()
        smtp.starttls.assert_not_called()
        self.assert_smtp(smtp)
