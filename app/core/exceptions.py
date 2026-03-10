import httpx

'''
DB 錯誤
├── 暫時性（值得 retry）
│   ├── OperationalError    ← 連線斷掉、DB 重啟
│   └── DisconnectionError  ← 網路瞬斷
└── 永久性（retry 也沒用）
    ├── ProgrammingError    ← SQL 語法錯誤、table 不存在
    ├── IntegrityError      ← constraint 違反
    └── DataError           ← 資料格式錯誤
'''


# 定義哪些情況應該 retry
RETRYABLE_EXCEPTIONS = (
    httpx.TimeoutException,      # 連線/讀取逾時
    httpx.ConnectError,          # 無法建立連線
    httpx.RemoteProtocolError,   # 伺服器回應異常
)


class BaseAppError(Exception):
    """專案所有異常的祖先"""
    def __init__(self, message: str, extra: dict = None):
        super().__init__(message)
        self.extra = extra or {}

class RetryableError(BaseAppError):
    """所有『值得重試』異常的父類別"""
    pass

class NonRetryableError(BaseAppError):
    """所有『一刀斃命』異常的父類別"""
    pass