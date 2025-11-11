class TokenExpiredError(Exception):
    detail = "Token has expired"


class TokenNotCorrectError(Exception):
    detail = "Invalid token"
