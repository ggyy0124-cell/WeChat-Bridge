from __future__ import annotations

import json
import logging
import os
import threading

logger = logging.getLogger(__name__)

_config_cache: dict | None = None
_config_cache_mtime: float = 0.0
_config_cache_file: str = ""


def _resolve_config_file() -> str:
    """优先使用 config.json，向后兼容 ai_config.json"""
    base_dir = os.path.dirname(os.environ.get("AI_CONFIG_FILE", "./data/ai_config.json"))
    new_config = os.path.join(base_dir, "config.json")
    old_config = os.path.join(base_dir, "ai_config.json")

    if os.path.exists(new_config):
        return new_config
    if os.path.exists(old_config):
        return old_config
    return os.environ.get("AI_CONFIG_FILE", old_config)


CONFIG_FILE = _resolve_config_file()
_config_lock = threading.Lock()

DEFAULT_CONFIG = {
    "keepalive_remind_minutes": 1380,  # 0=关闭, 60~1430=用户最后消息后N分钟发送提醒
}

# 已移除功能（遥测、AI 助手、Webhook 转发）在旧配置文件中残留的字段，加载时丢弃，不再保存或对外暴露
REMOVED_KEYS = (
    "telemetry_enabled",
    "enabled",
    "provider",
    "model",
    "api_key",
    "base_url",
    "system_prompt",
    "max_history",
    "max_tokens_per_day",
    "usage",
    "show_reasoning",
    "webhook_enabled",
    "webhook_url",
    "webhook_mode",
    "webhook_timeout",
)


def _invalidate_config_cache():
    global _config_cache, _config_cache_mtime, _config_cache_file
    _config_cache = None
    _config_cache_mtime = 0.0
    _config_cache_file = ""


def validate_config(cfg: dict) -> dict:
    """简单的 schema 校验与格式化"""
    valid = cfg.copy()
    for key in REMOVED_KEYS:
        valid.pop(key, None)

    try:
        valid["keepalive_remind_minutes"] = max(-1, int(valid.get("keepalive_remind_minutes", 1380)))
    except (TypeError, ValueError):
        valid["keepalive_remind_minutes"] = 1380

    return valid


def load_config() -> dict:
    """加载配置，优先从文件读取，基于 mtime 热加载"""
    global _config_cache, _config_cache_mtime, _config_cache_file

    try:
        current_mtime = os.path.getmtime(CONFIG_FILE) if os.path.exists(CONFIG_FILE) else 0.0
    except OSError:
        current_mtime = 0.0

    if _config_cache is not None and _config_cache_file == CONFIG_FILE and _config_cache_mtime == current_mtime:
        return _config_cache.copy()

    config = DEFAULT_CONFIG.copy()
    saved = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                saved = json.load(f)
            config.update(saved)
        except Exception as e:
            logger.warning("读取配置失败: %s", e)

    # 应用 schema 校验
    config = validate_config(config)

    # 向后兼容：将旧的双布尔迁移为新字段，如有旧字段则自动升级保存一次
    needs_save = False
    if "keepalive_23h" in config or "keepalive_23h58m" in config:
        if "keepalive_remind_minutes" not in config:
            if config.get("keepalive_23h58m", False):
                config["keepalive_remind_minutes"] = 1438  # 23h58m
            elif config.get("keepalive_23h", False):
                config["keepalive_remind_minutes"] = 1380  # 23h
        config.pop("keepalive_23h", None)
        config.pop("keepalive_23h58m", None)
        needs_save = True

    if "keepalive_remind_minutes" not in config:
        config["keepalive_remind_minutes"] = 1380
        needs_save = True

    if needs_save:
        save_config(config)

    _config_cache = config.copy()
    _config_cache_mtime = current_mtime
    _config_cache_file = CONFIG_FILE
    return config


def save_config(config: dict):
    """持久化配置到文件（加锁防并发写撕裂），同时清除缓存。"""
    _invalidate_config_cache()
    with _config_lock:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        logger.info("配置已保存")
