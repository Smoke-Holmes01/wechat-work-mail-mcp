from __future__ import annotations

import logging
import mimetypes
import os
import smtplib
import ssl
from email.header import Header
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, parseaddr
from pathlib import Path
from typing import Any

from .config import MailConfig

logger = logging.getLogger(__name__)


def _format_address(addr: str) -> str:
    """Ensure email address has properly encoded display name if present."""
    name, email_part = parseaddr(addr)
    if name:
        return formataddr((Header(name, "utf-8").encode(), email_part))
    return email_part


class ExmailSMTPClient:
    def __init__(self, config: MailConfig):
        self.config = config

    def test_connection(self) -> dict[str, Any]:
        """Test SMTP SSL connection and authentication."""
        errors = self.config.validate()
        if errors:
            return {"success": False, "message": "配置校验失败: " + "; ".join(errors)}

        context = ssl.create_default_context()
        try:
            with smtplib.SMTP_SSL(
                self.config.smtp_host, self.config.smtp_port, context=context, timeout=15
            ) as server:
                server.login(self.config.user, self.config.password)
            return {
                "success": True,
                "message": f"SMTP 验证成功！已连接到 {self.config.smtp_host}:{self.config.smtp_port}，账号: {self.config.user}",
            }
        except smtplib.SMTPAuthenticationError as e:
            return {
                "success": False,
                "message": f"SMTP 身份验证失败(代码 {e.smtp_code})：请确认使用的是【客户端专用密码】而非普通登录密码。错误详情: {e.smtp_error.decode('utf-8', errors='ignore') if isinstance(e.smtp_error, bytes) else str(e.smtp_error)}",
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"SMTP 连接失败: {type(e).__name__} - {str(e)}",
            }

    def send_email(
        self,
        to_addrs: list[str] | str,
        subject: str,
        body: str,
        is_html: bool = False,
        cc_addrs: list[str] | str | None = None,
        bcc_addrs: list[str] | str | None = None,
        attachments: list[str] | None = None,
        from_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Send an email via Tencent Exmail SMTP SSL.
        """
        errors = self.config.validate()
        if errors:
            return {"success": False, "message": "配置校验失败: " + "; ".join(errors)}

        # Normalize recipients
        if isinstance(to_addrs, str):
            to_list = [addr.strip() for addr in to_addrs.split(",") if addr.strip()]
        else:
            to_list = [addr.strip() for addr in to_addrs if addr.strip()]

        if not to_list:
            return {"success": False, "message": "收件人列表不能为空"}

        cc_list = []
        if cc_addrs:
            if isinstance(cc_addrs, str):
                cc_list = [addr.strip() for addr in cc_addrs.split(",") if addr.strip()]
            else:
                cc_list = [addr.strip() for addr in cc_addrs if addr.strip()]

        bcc_list = []
        if bcc_addrs:
            if isinstance(bcc_addrs, str):
                bcc_list = [addr.strip() for addr in bcc_addrs.split(",") if addr.strip()]
            else:
                bcc_list = [addr.strip() for addr in bcc_addrs if addr.strip()]

        # Prepare MIME
        msg = MIMEMultipart("mixed")
        
        # From header
        sender_display = from_name if from_name else self.config.user.split("@")[0]
        msg["From"] = formataddr((Header(sender_display, "utf-8").encode(), self.config.user))
        msg["To"] = ", ".join(_format_address(addr) for addr in to_list)
        msg["Subject"] = Header(subject, "utf-8").encode()

        if cc_list:
            msg["Cc"] = ", ".join(_format_address(addr) for addr in cc_list)

        # Body part
        body_subtype = "html" if is_html else "plain"
        body_part = MIMEText(body, body_subtype, "utf-8")
        msg.attach(body_part)

        # Attachments
        added_attachments = []
        if attachments:
            for attach_path_str in attachments:
                path = Path(attach_path_str).resolve()
                if not path.is_file():
                    return {
                        "success": False,
                        "message": f"附件文件不存在: {attach_path_str}",
                    }
                try:
                    filename = path.name
                    with open(path, "rb") as af:
                        file_data = af.read()

                    part = MIMEApplication(file_data)
                    # Support RFC 2231 / utf-8 filename
                    part.add_header(
                        "Content-Disposition",
                        "attachment",
                        filename=("utf-8", "", filename),
                    )
                    msg.attach(part)
                    added_attachments.append(filename)
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"读取或添加附件失败 ({path.name}): {str(e)}",
                    }

        all_recipients = to_list + cc_list + bcc_list
        context = ssl.create_default_context()

        try:
            with smtplib.SMTP_SSL(
                self.config.smtp_host, self.config.smtp_port, context=context, timeout=30
            ) as server:
                server.login(self.config.user, self.config.password)
                server.sendmail(self.config.user, all_recipients, msg.as_string())

            return {
                "success": True,
                "message": "邮件发送成功",
                "details": {
                    "to": to_list,
                    "cc": cc_list,
                    "subject": subject,
                    "attachments": added_attachments,
                },
            }
        except smtplib.SMTPAuthenticationError as e:
            return {
                "success": False,
                "message": f"SMTP 身份验证失败: 请检查【客户端专用密码】是否有效。(Code: {e.smtp_code})",
            }
        except Exception as e:
            logger.exception("Failed to send email via SMTP")
            return {
                "success": False,
                "message": f"发送邮件异常: {type(e).__name__} - {str(e)}",
            }
