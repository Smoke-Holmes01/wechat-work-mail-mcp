from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def load_dotenv(dotenv_path: Path | None = None) -> None:
    """Simple .env loader if .env file exists."""
    if dotenv_path is None:
        dotenv_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if not dotenv_path.is_file():
        return

    try:
        with open(dotenv_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                if key not in os.environ:
                    os.environ[key] = val
    except Exception:
        pass


@dataclass
class MailConfig:
    user: str
    password: str
    smtp_host: str = "smtp.exmail.qq.com"
    smtp_port: int = 465
    imap_host: str = "imap.exmail.qq.com"
    imap_port: int = 993
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> MailConfig:
        load_dotenv()
        return cls(
            user=os.environ.get("EXMAIL_USER", "").strip(),
            password=os.environ.get("EXMAIL_PASS", "").strip(),
            smtp_host=os.environ.get("EXMAIL_SMTP_HOST", "smtp.exmail.qq.com").strip(),
            smtp_port=int(os.environ.get("EXMAIL_SMTP_PORT", "465")),
            imap_host=os.environ.get("EXMAIL_IMAP_HOST", "imap.exmail.qq.com").strip(),
            imap_port=int(os.environ.get("EXMAIL_IMAP_PORT", "993")),
            log_level=os.environ.get("EXMAIL_LOG_LEVEL", "INFO").strip().upper(),
        )

    def validate(self) -> list[str]:
        errors = []
        if not self.user:
            errors.append("EXMAIL_USER 未配置（请输入完整企业邮箱地址）")
        elif "@" not in self.user:
            errors.append("EXMAIL_USER 格式无效，必须包含 '@'")
        if not self.password:
            errors.append("EXMAIL_PASS 未配置（请输入网页端生成的客户端专用密码）")
        return errors
