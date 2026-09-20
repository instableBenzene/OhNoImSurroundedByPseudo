"""浏览器内（Pyodide）请求桥：把 ``weiren_game.web_ui`` 的请求处理直接跑在内存里。

前端发过来的每个 ``/api/*`` 请求都在这里交给**同一个** ``BaseHTTPRequestHandler`` 处理，
只是把 socket 换成了内存里的 ``BytesIO``。因此回合流程、随机数、存档格式与本地跑
``python game_ui.py`` 完全一致，不存在"第二套规则"。

（构建时被复制到产物的 ``vibehub_bridge.py``，源码仓库本身不使用它。）
"""

from __future__ import annotations

import email.message
import io
import json

_BRIDGE = None


class Bridge:
    def __init__(self) -> None:
        from weiren_game import web_ui

        try:
            from weiren_game.dlc import load_configured_dlc

            load_configured_dlc()
        except Exception as exc:  # noqa: BLE001 - 单个包损坏不该挡住开局
            print("dlc load failed:", exc)
        self.handler_cls = web_ui.make_handler(web_ui.Session())

    def _raw_call(self, method: str, path: str, body_text: str) -> bytes:
        handler = self.handler_cls.__new__(self.handler_cls)
        payload = body_text.encode("utf-8")
        handler.wfile = io.BytesIO()
        handler.rfile = io.BytesIO(payload)
        handler.headers = email.message.Message()
        handler.headers["Content-Length"] = str(len(payload))
        handler.headers["Content-Type"] = "application/json"
        handler.request_version = "HTTP/1.1"
        handler.protocol_version = "HTTP/1.1"
        handler.command = method
        handler.path = path
        handler.requestline = method + " " + path + " HTTP/1.1"
        handler.client_address = ("127.0.0.1", 0)
        handler.request = None
        handler.server = None
        handler.close_connection = True
        if method == "POST":
            self.handler_cls.do_POST(handler)
        else:
            self.handler_cls.do_GET(handler)
        return handler.wfile.getvalue()

    def handle(self, method: str, path: str, body_text: str = "") -> str:
        try:
            raw = self._raw_call(method, path, body_text)
        except Exception as exc:  # noqa: BLE001
            message = type(exc).__name__ + ": " + str(exc)
            return json.dumps(
                {
                    "status": 500,
                    "contentType": "application/json; charset=utf-8",
                    "body": json.dumps({"ok": False, "error": message}, ensure_ascii=False),
                },
                ensure_ascii=False,
            )
        head, _, rest = raw.partition(b"\r\n\r\n")
        status = 200
        content_type = "application/json; charset=utf-8"
        length: int | None = None
        for line in head.split(b"\r\n")[1:]:
            text = line.decode("latin-1")
            lower = text.lower()
            if lower.startswith("content-type:"):
                content_type = text.split(":", 1)[1].strip()
            elif lower.startswith("content-length:"):
                try:
                    length = int(text.split(":", 1)[1].strip())
                except ValueError:
                    length = None
            elif lower.startswith("http/"):
                parts = text.split()
                if len(parts) > 1:
                    try:
                        status = int(parts[1])
                    except ValueError:
                        status = 200
        # 少数分支（例如 /api/resourcepack）少写了一个 return，会接着再写一份响应；
        # 按第一份的 Content-Length 截断，等价于真实 HTTP 客户端读到的内容。
        body = rest[:length] if length is not None else rest
        try:
            decoded = body.decode("utf-8")
        except UnicodeDecodeError:
            decoded = ""
        return json.dumps(
            {"status": status, "contentType": content_type, "body": decoded},
            ensure_ascii=False,
        )


def init() -> None:
    global _BRIDGE
    if _BRIDGE is None:
        _BRIDGE = Bridge()


def bridge_handle(method: str, path: str, body_text: str = "") -> str:
    if _BRIDGE is None:
        init()
    return _BRIDGE.handle(method, path, body_text)


__all__ = ["Bridge", "init", "bridge_handle"]
