"""PyWebView launcher for the Asphalt-TEG frontend."""

from __future__ import annotations

import webview


class Api:
    pass


if __name__ == "__main__":
    api = Api()
    webview.create_window(
        "Asphalt-TEG Simulator",
        "ui/index.html",
        js_api=api,
        width=980,
        height=620,
        resizable=True,
    )
    webview.start()
