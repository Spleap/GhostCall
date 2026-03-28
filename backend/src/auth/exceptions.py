from src.exceptions import BusinessException


class AuthFailedException(BusinessException):
    def __init__(self):
        super().__init__(code=40101, message="账号或密码错误")
