from __future__ import annotations

"""
微信指令路由

从 bridge.py 拆分而来，通过 Mixin 注入 WeChatBridge。
处理 / 开头的内置指令（/help, /status, /pull, /mute, /keepalive, /uid）。
"""

import logging
import time

import config as cfg
from fmt import md_inline as _md_inline

logger = logging.getLogger(__name__)


def _format_minutes(minutes: int) -> str:
    hours = minutes // 60
    mins = minutes % 60
    if hours and mins:
        return f"{hours}小时{mins}分钟"
    if hours:
        return f"{hours}小时"
    return f"{mins}分钟"


class CommandMixin:
    """指令路由 Mixin，注入 WeChatBridge。"""

    def _handle_command(self, text: str, user_id: str) -> str:
        """处理 / 开头的指令。"""
        cmd = text.strip().lower()
        if cmd in ("/help", "/帮助"):
            lines = [
                "## 📋 可用指令",
                "",
                "- `/status`：查看 Bot 运行状态和配置",
                "- `/pull`：拉取缓存中的未送达消息",
                "- `/mute 时长`：静默模式，期间推送自动缓存",
                "- `/uid`：查看自己的用户 ID",
                "- `/keepalive on|off`：开关连接保活提醒",
            ]
            return "\n".join(lines)

        if cmd in ("/status", "/状态"):
            settings = cfg.load_config()
            summary = self.get_delivery_summary(user_id)
            uptime_seconds = int(time.time() - getattr(self, "_start_time", time.time()))
            m, s = divmod(uptime_seconds, 60)
            h, m = divmod(m, 60)
            uptime_str = f"{h}小时 {m}分钟" if h > 0 else f"{m}分钟"
            if uptime_seconds < 60:
                uptime_str = f"{uptime_seconds}秒"

            keepalive = settings.get("keepalive_remind_minutes", 1380)
            if keepalive > 0:
                notify_enabled = f"✅ 开启（{_format_minutes(keepalive)}）"
            else:
                notify_enabled = "❌ 关闭"

            return (
                "## 🤖 WeChat Bridge\n\n"
                "### 运行状态\n\n"
                f"- **运行时长**：{uptime_str}\n"
                f"- **缓存消息**：{summary['pending_count']} 条\n"
                f"- **投递状态**：{_md_inline(summary['status'])}\n"
                f"- **缓存原因**：{summary['blocked_reason_text']}\n\n"
                "### 功能配置\n\n"
                f"- **保活提醒**：{notify_enabled}"
            )

        if cmd in ("/pull",):
            return "__MAGIC_PULL__"

        if cmd in ("/uid",):
            return f"## 🆔 用户 ID\n\n{_md_inline(user_id)}"

        if cmd.startswith("/mute"):
            parts = text.strip().split()
            if len(parts) == 1:
                # /mute 无参数：查看当前状态
                mute_ts = self._mute_until.get(user_id, 0)
                if mute_ts and time.time() < mute_ts:
                    from datetime import datetime

                    unmute_str = datetime.fromtimestamp(mute_ts).strftime("%H:%M")
                    return f"## 🔇 静默模式\n\n- **状态**：开启中\n- **恢复时间**：{unmute_str}\n- 回复任意内容自动关闭"
                return "## 🔇 静默模式\n\n- **状态**：未开启\n- **用法**：`/mute 2h` 或 `/mute 30`（分钟）"

            action = parts[1].lower()

            # 解析时长：支持 30m, 2h, 1.5h, 纯数字=分钟
            duration_str = action
            minutes = 0
            try:
                if duration_str.endswith("h"):
                    minutes = int(float(duration_str[:-1]) * 60)
                elif duration_str.endswith("m"):
                    minutes = int(duration_str[:-1])
                elif duration_str.isdigit():
                    minutes = int(duration_str)
            except (ValueError, IndexError):
                pass

            if minutes <= 0:
                return "## ❓ 用法\n\n- `/mute 30`：静默 30 分钟\n- `/mute 2h`：静默 2 小时\n- 回复任意内容自动关闭"
            if minutes > 24 * 60:
                return "## ⚠️ 静默时长不能超过 24 小时"

            self._mute_until[user_id] = time.time() + minutes * 60
            if minutes >= 60:
                display = f"{minutes // 60}小时" + (f"{minutes % 60}分钟" if minutes % 60 else "")
            else:
                display = f"{minutes}分钟"
            from datetime import datetime

            unmute_str = datetime.fromtimestamp(self._mute_until[user_id]).strftime("%H:%M")
            return f"## 🔇 静默模式已开启\n\n- **时长**：{display}\n- **恢复时间**：{unmute_str}\n- 期间推送将自动缓存，回复任意内容自动关闭"

        if cmd.startswith("/keepalive ") or cmd.startswith("/保活 "):
            parts = cmd.split()
            if len(parts) > 1:
                action = parts[1].lower()
                current = cfg.load_config()
                if action in ("on", "1", "true", "开启"):
                    current["keepalive_remind_minutes"] = 1380
                    cfg.save_config(current)
                    return "## ✅ 保活提醒\n\n- **状态**：已开启\n- **提醒时间**：距最后发言 `23小时` 时提醒"
                if action in ("off", "0", "false", "关闭"):
                    current["keepalive_remind_minutes"] = 0
                    cfg.save_config(current)
                    return "## ❌ 保活提醒\n\n- **状态**：已关闭"
            return "## ❓ 用法\n\n- 开启：`/keepalive on`\n- 关闭：`/keepalive off`"

        return f"## ❓ 未知指令\n\n- **收到**：{_md_inline(text)}\n- 发送 `/help` 查看可用指令"
