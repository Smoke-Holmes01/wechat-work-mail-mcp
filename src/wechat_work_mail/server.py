from __future__ import annotations

import logging
from typing import Any

try:
    from mcp.server.mcpserver import MCPServer
except ImportError:  # pragma: no cover - fallback for mcp 1.x
    from mcp.server.fastmcp import FastMCP as MCPServer

from .config import MailConfig
from .imap_client import ExmailIMAPClient
from .smtp_client import ExmailSMTPClient

config = MailConfig.from_env()
logging.basicConfig(
    level=getattr(logging, config.log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("wechat_work_mail_mcp")

mcp = MCPServer("wechat-work-mail-mcp")


@mcp.tool()
def exmail_check_connection() -> dict[str, Any]:
    """
    检查企业微信邮箱配置及 SMTP、IMAP 服务器连通性。
    若连接失败，会返回具体的排查建议。
    """
    cfg = MailConfig.from_env()
    errors = cfg.validate()
    if errors:
        return {
            "success": False,
            "status": "配置不完整",
            "errors": errors,
            "tips": "请在环境变量或 .env 文件中设置 EXMAIL_USER 和 EXMAIL_PASS（网页端生成的客户端专用密码）。",
        }

    smtp_client = ExmailSMTPClient(cfg)
    imap_client = ExmailIMAPClient(cfg)

    smtp_res = smtp_client.test_connection()
    imap_res = imap_client.test_connection()

    all_ok = smtp_res["success"] and imap_res["success"]
    return {
        "success": all_ok,
        "smtp": smtp_res,
        "imap": imap_res,
        "user": cfg.user,
    }


@mcp.tool()
def exmail_send_email(
    to_addrs: list[str],
    subject: str,
    body: str,
    is_html: bool = False,
    cc_addrs: list[str] | None = None,
    bcc_addrs: list[str] | None = None,
    attachments: list[str] | None = None,
    from_name: str | None = None,
) -> dict[str, Any]:
    """
    通过企业微信邮箱发送邮件。支持纯文本/HTML、多收件人、抄送、密送以及本地文件附件。

    :param to_addrs: 收件人邮箱列表，例如 ["alice@company.com", "bob@external.com"]
    :param subject: 邮件主题
    :param body: 邮件正文（若 is_html 为 True，可传入 HTML 代码）
    :param is_html: 正文是否为 HTML 格式，默认为 False
    :param cc_addrs: 抄送人邮箱列表（可选）
    :param bcc_addrs: 密送人邮箱列表（可选）
    :param attachments: 本地文件附件路径列表（例如 ["C:/docs/report.pdf"]，可选）
    :param from_name: 发件人显示昵称（可选，默认使用邮箱前缀）
    """
    cfg = MailConfig.from_env()
    client = ExmailSMTPClient(cfg)
    return client.send_email(
        to_addrs=to_addrs,
        subject=subject,
        body=body,
        is_html=is_html,
        cc_addrs=cc_addrs,
        bcc_addrs=bcc_addrs,
        attachments=attachments,
        from_name=from_name,
    )


@mcp.tool()
def exmail_list_emails(
    limit: int = 10,
    folder: str = "INBOX",
    unread_only: bool = False,
    query: str | None = None,
) -> dict[str, Any]:
    """
    获取企业微信邮箱收件箱或指定文件夹的最近邮件摘要列表。

    :param limit: 获取邮件数量上限，默认 10 封
    :param folder: 邮箱文件夹，默认 "INBOX"（收件箱）
    :param unread_only: 是否仅查看未读邮件，默认 False
    :param query: 搜索关键词（按主题或发件人匹配，可选）
    """
    cfg = MailConfig.from_env()
    client = ExmailIMAPClient(cfg)
    return client.list_recent_emails(
        limit=limit,
        folder=folder,
        unread_only=unread_only,
        query=query,
    )


@mcp.tool()
def exmail_get_email(email_id: str, folder: str = "INBOX") -> dict[str, Any]:
    """
    根据邮件 ID 读取单封邮件的完整正文、发件人、时间及附件列表。

    :param email_id: 邮件 ID（可通过 exmail_list_emails 获取）
    :param folder: 邮件所在文件夹，默认 "INBOX"
    """
    cfg = MailConfig.from_env()
    client = ExmailIMAPClient(cfg)
    return client.get_email_detail(email_id=email_id, folder=folder)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
