# 企业微信邮箱 (腾讯企业邮) MCP 服务

[![MCP](https://img.shields.io/badge/MCP-1.12+-blue.svg)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://www.python.org)

适用于企业微信邮箱（腾讯企业邮）的 Model Context Protocol (MCP) 服务。
赋予 AI 助手（如 Antigravity、Claude Desktop、Cursor 等）自动发送邮件、读取最近邮件以及管理企业邮件的能力。

---

## 🌟 核心功能

- 📨 **发送邮件 (`exmail_send_email`)**：
  - 支持发送纯文本及 HTML 富文本邮件。
  - 支持单收件人、多收件人、抄送（CC）及密送（BCC）。
  - 支持添加本地文件作为附件（自动识别 MIME 类型与 UTF-8 文件名编码）。
- 📥 **查收邮件 (`exmail_list_emails`)**：
  - 拉取收件箱或指定文件夹的最近邮件摘要（主题、发件人、日期）。
  - 支持仅过滤未读邮件或按主题/发件人搜索。
- 📖 **读取详情 (`exmail_get_email`)**：
  - 读取指定邮件的正文（纯文本/HTML）及附件元数据。
- 🔍 **连接诊断 (`exmail_check_connection`)**：
  - 快速验证 SMTP 与 IMAP 连通性及授权码是否有效。

---

## 🔑 权限与专用密码配置指南

由于企业微信邮箱具有高级安全防护，**直接使用常规网页登录密码或微信扫码是无法通过 SMTP/IMAP 协议登录的**，必须获取**“客户端专用密码”**。

### 第一步：确认客户端权限已开启
1. 访问并登录 [腾讯企业邮箱网页版](https://exmail.qq.com)。
2. 进入右上角 **【设置】** -> **【收发信设置】**。
3. 检查并确保勾选了 **开启 POP3/SMTP 服务** 或 **开启 IMAP/SMTP 服务**。
*(注：如果该选项被锁定，需要联系企业微信管理员在【管理后台 -> 协作 -> 邮件 -> 安全管理 -> 客户端访问权限】中开启)*。

### 第二步：生成客户端专用密码（授权码）
1. 在网页版设置中，切换至 **【邮箱绑定】** 或 **【安全设置】**。
2. 找到 **“客户端专用密码”**（或“生成新密码”）。
3. 点击 **【生成新密码】**，系统将展示一串 16 位的随机字母授权码（例如：`abcdefgh12345678`）。
4. **复制该密码备用**。

---

## 🚀 安装与初始化

进入项目目录：
```powershell
cd C:\StudyFiles\mcp-service\wechat-work-mail-mcp
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
```

运行单元测试：
```powershell
.\.venv\Scripts\pytest
```

---

## ⚙️ MCP 客户端配置

### 1. Antigravity / Gemini 配置 (`mcp_config.json`)
打开配置文件：`C:\Users\Nyx\.gemini\config\mcp_config.json`，在 `mcpServers` 下追加：

```json
{
  "mcpServers": {
    "wechat-work-mail": {
      "command": "C:/StudyFiles/mcp-service/wechat-work-mail-mcp/.venv/Scripts/python.exe",
      "args": ["-m", "wechat_work_mail.server"],
      "env": {
        "EXMAIL_USER": "your_email@yourcompany.com",
        "EXMAIL_PASS": "your_client_app_password"
      }
    }
  }
}
```

也可以使用可执行脚本形式：
```json
{
  "mcpServers": {
    "wechat-work-mail": {
      "command": "C:/StudyFiles/mcp-service/wechat-work-mail-mcp/.venv/Scripts/wechat-work-mail-mcp.exe",
      "args": [],
      "env": {
        "EXMAIL_USER": "your_email@yourcompany.com",
        "EXMAIL_PASS": "your_client_app_password"
      }
    }
  }
}
```

---

## 🤖 AI 交互示例

配置生效后，您可以直接向 AI 发出日常自然语言指令：

- *“帮我检查一下企业微信邮箱连接是否正常。”*
- *“帮我给 zhangsan@partner.com 发送一封商务跟进邮件，主题是‘Q3项目进展沟通’，正文写得客气专业一些，并抄送我的主管 lisi@mycompany.com。”*
- *“请把当前目录下的 `report.pdf` 作为附件，发邮件给财务部的 wangwu@mycompany.com。”*
- *“查一下我收件箱最近有没有来自人事部门的未读邮件？”*
