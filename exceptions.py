class CustomExceptionA(Exception):
    def __init__(self, detail: str):
        self.detail = detail
        self.status_code = 400


class CustomExceptionB(Exception):
    def __init__(self, detail: str):
        self.detail = detail
        self.status_code = 404
