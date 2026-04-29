from __future__ import annotations

import uvicorn

from backend.core.config import SERVER_HOST, SERVER_PORT


if __name__ == "__main__":
    uvicorn.run("main:app", host=SERVER_HOST, port=SERVER_PORT, reload=True)

