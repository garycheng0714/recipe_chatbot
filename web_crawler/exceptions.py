from app.core.exceptions import RetryableError, NonRetryableError

# --- 網路層級 ---
class RequestRetryableError(RetryableError):
    """暫時性網路問題：Timeout, 429, 502, 503, 504"""
    pass

class RequestFatalError(NonRetryableError):
    """永久性失敗：404, 網址錯誤"""
    pass

class RequestBlockedError(NonRetryableError):
    """被封鎖：403, 401 (通常需要人工介入或換 Proxy)"""
    pass

# --- 內容解析層級 ---
class ContentParsingError(NonRetryableError):
    """網頁下載成功但 HTML 結構變了，解析不出資料"""
    pass