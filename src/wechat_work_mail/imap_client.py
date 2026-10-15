from __future__ import annotations

import email
import imaplib
import logging
import ssl
from email.header import decode_header
from typing import Any

from .config import MailConfig

import re
from html.parser import HTMLParser

logger = logging.getLogger(__name__)


class _HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []
        self.in_script_or_style = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.in_script_or_style = True
        elif tag in ("p", "br", "div", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6"):
            self.fed.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.in_script_or_style = False

    def handle_data(self, data):
        if not self.in_script_or_style:
            self.fed.append(data)

    def get_text(self):
        text = "".join(self.fed)
        lines = [line.strip() for line in text.splitlines()]
        return "\n".join(chunk for chunk in lines if chunk)


def _html_to_plain_text(html_content: str) -> str:
    if not html_content:
        return ""
    try:
        extractor = _HTMLTextExtractor()
        extractor.feed(html_content)
        return extractor.get_text()
    except Exception:
        clean = re.sub(r"<(script|style).*?>.*?</\1>", "", html_content, flags=re.DOTALL | re.IGNORECASE)
        clean = re.sub(r"<[^>]+>", " ", clean)
        return "\n".join(chunk.strip() for chunk in clean.splitlines() if chunk.strip())



def _decode_mime_str(header_val: str | None) -> str:
    """Decode RFC 2047 encoded email headers."""
    if not header_val:
        return ""
    decoded_parts = decode_header(header_val)
    result = []
    for content, encoding in decoded_parts:
        if isinstance(content, bytes):
            try:
                charset = encoding if encoding else "utf-8"
                result.append(content.decode(charset, errors="replace"))
            except Exception:
                result.append(content.decode("utf-8", errors="replace"))
        else:
            result.append(str(content))
    return "".join(result)


class ExmailIMAPClient:
    def __init__(self, config: MailConfig):
        self.config = config

    def test_connection(self) -> dict[str, Any]:
        """Test IMAP SSL connection and authentication."""
        errors = self.config.validate()
        if errors:
            return {"success": False, "message": "配置校验失败: " + "; ".join(errors)}

        context = ssl.create_default_context()
        try:
            with imaplib.IMAP4_SSL(
                self.config.imap_host, self.config.imap_port, ssl_context=context
            ) as imap:
                imap.login(self.config.user, self.config.password)
            return {
                "success": True,
                "message": f"IMAP 验证成功！已连接到 {self.config.imap_host}:{self.config.imap_port}，账号: {self.config.user}",
            }
        except imaplib.IMAP4.error as e:
            return {
                "success": False,
                "message": f"IMAP 身份验证或连接失败: {str(e)}。请确认是否开启 IMAP 协议并使用【客户端专用密码】。",
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"IMAP 连接异常: {type(e).__name__} - {str(e)}",
            }

    def list_recent_emails(
        self,
        limit: int = 10,
        folder: str = "INBOX",
        unread_only: bool = False,
        query: str | None = None,
    ) -> dict[str, Any]:
        """
        List recent email summaries from specified folder.
        """
        errors = self.config.validate()
        if errors:
            return {"success": False, "message": "配置校验失败: " + "; ".join(errors)}

        context = ssl.create_default_context()
        try:
            with imaplib.IMAP4_SSL(
                self.config.imap_host, self.config.imap_port, ssl_context=context
            ) as imap:
                imap.login(self.config.user, self.config.password)
                imap.select(folder, readonly=True)

                search_criteria = "UNSEEN" if unread_only else "ALL"
                if query:
                    # Search in subject or from
                    search_criteria = f'(OR (SUBJECT "{query}") (FROM "{query}"))'

                status, data = imap.search(None, search_criteria)
                if status != "OK" or not data or not data[0]:
                    return {
                        "success": True,
                        "count": 0,
                        "emails": [],
                        "message": "未检索到匹配的邮件",
                    }

                msg_ids = data[0].split()
                # Take recent ones (last N)
                selected_ids = msg_ids[-limit:][::-1]

                results = []
                for mid in selected_ids:
                    id_str = mid.decode("ascii", errors="ignore")
                    fetch_res, msg_data = imap.fetch(mid, "(BODY.PEEK[HEADER.FIELDS (FROM TO SUBJECT DATE)])")
                    if fetch_res != "OK" or not msg_data:
                        continue

                    raw_header = b""
                    for part in msg_data:
                        if isinstance(part, tuple):
                            raw_header = part[1]
                            break

                    msg = email.message_from_bytes(raw_header)
                    results.append({
                        "id": id_str,
                        "subject": _decode_mime_str(msg.get("Subject")),
                        "from": _decode_mime_str(msg.get("From")),
                        "to": _decode_mime_str(msg.get("To")),
                        "date": msg.get("Date", ""),
                    })

                return {
                    "success": True,
                    "count": len(results),
                    "folder": folder,
                    "emails": results,
                }
        except Exception as e:
            logger.exception("Failed to list emails via IMAP")
            return {
                "success": False,
                "message": f"拉取邮件列表失败: {type(e).__name__} - {str(e)}",
            }

    def get_email_detail(self, email_id: str, folder: str = "INBOX") -> dict[str, Any]:
        """
        Fetch full body and attachment metadata of an email by its ID.
        """
        errors = self.config.validate()
        if errors:
            return {"success": False, "message": "配置校验失败: " + "; ".join(errors)}

        context = ssl.create_default_context()
        try:
            with imaplib.IMAP4_SSL(
                self.config.imap_host, self.config.imap_port, ssl_context=context
            ) as imap:
                imap.login(self.config.user, self.config.password)
                imap.select(folder, readonly=True)

                status, data = imap.fetch(email_id.encode("ascii"), "(RFC822)")
                if status != "OK" or not data:
                    return {"success": False, "message": f"未找到 ID 为 {email_id} 的邮件"}

                raw_email = b""
                for part in data:
                    if isinstance(part, tuple):
                        raw_email = part[1]
                        break

                msg = email.message_from_bytes(raw_email)
                subject = _decode_mime_str(msg.get("Subject"))
                from_addr = _decode_mime_str(msg.get("From"))
                to_addr = _decode_mime_str(msg.get("To"))
                cc_addr = _decode_mime_str(msg.get("Cc"))
                date_str = msg.get("Date", "")

                text_body = ""
                html_body = ""
                attachments = []

                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition", ""))

                        filename = part.get_filename()
                        if filename:
                            decoded_fn = _decode_mime_str(filename)
                            attachments.append({
                                "filename": decoded_fn,
                                "content_type": content_type,
                                "size": len(part.get_payload(decode=True) or b""),
                            })
                            continue

                        if "attachment" in content_disposition:
                            continue

                        if content_type == "text/plain" and not text_body:
                            payload = part.get_payload(decode=True)
                            charset = part.get_content_charset() or "utf-8"
                            text_body = payload.decode(charset, errors="replace") if payload else ""
                        elif content_type == "text/html" and not html_body:
                            payload = part.get_payload(decode=True)
                            charset = part.get_content_charset() or "utf-8"
                            html_body = payload.decode(charset, errors="replace") if payload else ""
                else:
                    payload = msg.get_payload(decode=True)
                    charset = msg.get_content_charset() or "utf-8"
                    content = payload.decode(charset, errors="replace") if payload else ""
                    if msg.get_content_type() == "text/html":
                        html_body = content
                    else:
                        text_body = content

                if not text_body and html_body:
                    text_body = _html_to_plain_text(html_body)

                return {
                    "success": True,
                    "id": email_id,
                    "subject": subject,
                    "from": from_addr,
                    "to": to_addr,
                    "cc": cc_addr,
                    "date": date_str,
                    "body_text": text_body or "(正文为空)",
                    "has_html": bool(html_body),
                    "attachments": attachments,
                }
        except Exception as e:
            logger.exception("Failed to fetch email detail")
            return {
                "success": False,
                "message": f"读取邮件详情失败: {type(e).__name__} - {str(e)}",
            }
