import os
from unittest.mock import MagicMock, patch

import pytest
from wechat_work_mail.config import MailConfig
from wechat_work_mail.imap_client import ExmailIMAPClient, _decode_mime_str
from wechat_work_mail.smtp_client import ExmailSMTPClient, _format_address


def test_config_validation():
    # Empty config
    cfg = MailConfig(user="", password="")
    errors = cfg.validate()
    assert len(errors) == 2

    # Invalid email
    cfg_invalid = MailConfig(user="invalidemail", password="mypassword")
    errors = cfg_invalid.validate()
    assert any("必须包含 '@'" in e for e in errors)

    # Valid config
    cfg_valid = MailConfig(user="test@company.com", password="mypassword")
    assert cfg_valid.validate() == []


def test_format_address():
    assert _format_address("alice@example.com") == "alice@example.com"
    formatted = _format_address("张三 <zhangsan@example.com>")
    assert "zhangsan@example.com" in formatted


def test_decode_mime_str():
    assert _decode_mime_str(None) == ""
    assert _decode_mime_str("Normal Text") == "Normal Text"
    # RFC 2047 encoded
    encoded = "=?utf-8?b?5byA5Y+R5pel5oql?="  # "开发日报" in base64
    assert _decode_mime_str(encoded) == "开发日报"


@patch("smtplib.SMTP_SSL")
def test_smtp_send_email_success(mock_smtp_ssl, tmp_path):
    mock_server = MagicMock()
    mock_smtp_ssl.return_value.__enter__.return_value = mock_server

    cfg = MailConfig(user="sender@company.com", password="dummy_password")
    client = ExmailSMTPClient(cfg)

    # Create dummy attachment
    dummy_file = tmp_path / "report.txt"
    dummy_file.write_text("Hello attachment", encoding="utf-8")

    result = client.send_email(
        to_addrs=["receiver@company.com"],
        subject="测试邮件",
        body="<h1>测试内容</h1>",
        is_html=True,
        cc_addrs=["cc@company.com"],
        attachments=[str(dummy_file)],
    )

    assert result["success"] is True
    assert mock_server.login.called
    assert mock_server.sendmail.called
    sent_args = mock_server.sendmail.call_args[0]
    assert sent_args[0] == "sender@company.com"
    assert "receiver@company.com" in sent_args[1]
    assert "cc@company.com" in sent_args[1]


@patch("smtplib.SMTP_SSL")
def test_smtp_test_connection(mock_smtp_ssl):
    mock_server = MagicMock()
    mock_smtp_ssl.return_value.__enter__.return_value = mock_server

    cfg = MailConfig(user="sender@company.com", password="dummy_password")
    client = ExmailSMTPClient(cfg)

    res = client.test_connection()
    assert res["success"] is True
    mock_server.login.assert_called_with("sender@company.com", "dummy_password")
