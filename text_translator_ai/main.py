from __future__ import annotations

import logging

import uvicorn

from text_translator_ai.app import create_app
from text_translator_ai.settings import load_settings


def main() -> int:
    logging.basicConfig(level=logging.INFO, force=True)
    logging.getLogger("text_translator_ai").setLevel(logging.INFO)
    settings = load_settings()
    app = create_app(settings)
    uvicorn.run(app, host=settings.host, port=settings.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
