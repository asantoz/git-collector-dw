class HttpRequestError(Exception):
    def __init__(self, message, status):
        self.message = message
        self.status = status
        super().__init__(self.message, self.status)

class RateLimitExceedError(Exception):
    def __init__(self, message, time_to_wait):
        self.message = message
        self.time_to_wait = time_to_wait
        super().__init__(self.message,self.time_to_wait)
