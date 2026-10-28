#!/usr/bin/env python3
from __future__ import annotations

"""
WeChat Bridge 入口
启动 HTTP API 服务 + 消息长轮询循环
"""

import logging
import os
import signal
import sys

# 配置日志
log_format = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
log_datefmt = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    datefmt=log_datefmt,
    stream=sys.stdout,
)

# 确保 CWD 为项目根目录（app/ 的上级），使所有 ./data/ 路径正确
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(_project_root)

# 同时输出到文件 data/run.log
_log_dir = os.environ.get("LOG_DIR", os.path.join(_project_root, "data"))
os.makedirs(_log_dir, exist_ok=True)
_log_file = os.path.join(_log_dir, "run.log")
from logging.handlers import RotatingFileHandler

_file_handler = RotatingFileHandler(_log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
_file_handler.setFormatter(logging.Formatter(log_format, datefmt=log_datefmt))
logging.getLogger().addHandler(_file_handler)
logger = logging.getLogger("wechat-bridge")

# 确保能 import 同目录模块
sys.path.insert(0, os.path.join(_project_root, "app"))

import db
import web
from accounts import AccountManager
from version import __version__


def main():
    port = int(os.environ.get("PORT", "5200"))
    # Docker 容器内不应打开浏览器
    auto_open = os.environ.get("NO_BROWSER", "").lower() not in ("1", "true", "yes")

    logger.info("=" * 50)
    logger.info("WeChat Bridge 启动中...")
    logger.info("版本: %s", __version__)
    logger.info("端口: %d", port)
    data_dir = os.environ.get("DATA_DIR", "./data")
    logger.info("数据目录: %s", data_dir)
    logger.info("API Token: %s", "已设置" if os.environ.get("API_TOKEN") else "(未设置，接口无鉴权)")
    logger.info("日志文件: %s", _log_file)
    logger.info("=" * 50)

    # 初始化多账号运行时并恢复已保存账号
    account_manager = AccountManager(data_dir)
    restored = account_manager.restore_accounts()
    logger.info("已恢复 %d 个微信账号", len(restored))

    # 注入 Web 层运行上下文
    web.set_account_manager(account_manager, os.environ.get("API_TOKEN", ""))

    # 优雅退出
    def shutdown(signum, frame):
        logger.info("收到退出信号，正在关闭...")
        account_manager.stop_all()
        db.close_db()
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    # 延迟自动打开浏览器（等待服务器就绪）
    url = f"http://localhost:{port}"
    if auto_open:
        import threading
        import webbrowser

        def _open_browser():
            logger.info("🌐 正在打开浏览器: %s", url)
            webbrowser.open(url)

        threading.Timer(1.5, _open_browser).start()

    logger.info("✅ 服务已就绪: %s", url)

    # 启动 HTTP 服务（阻塞主线程）
    web.run_server(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
