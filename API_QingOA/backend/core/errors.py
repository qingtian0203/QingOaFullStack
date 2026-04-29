from __future__ import annotations


SUCCESS = 0
INVALID_CREDENTIALS = 1001
INVALID_TOKEN = 1002
BAD_REQUEST = 1003
OUT_OF_RANGE = 1004
ALREADY_PUNCHED = 1005
NO_PUNCH_PERMISSION = 1006
INTERNAL_ERROR = 9999


class ApiError(Exception):
    def __init__(self, code: int, msg: str, data=None, http_status: int = 200):
        self.code = code
        self.msg = msg
        self.data = data
        self.http_status = http_status
        super().__init__(msg)

