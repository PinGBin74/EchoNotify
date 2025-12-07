class TokenExpiredError(Exception):
    detail = "Token has expired"


class TokenNotCorrectError(Exception):
    detail = "Invalid token"


class UserAlreadyExistsError(Exception):
    detail = "User already exists"


class UserNotFoundError(Exception):
    detail = "User not found Error"


class UserNotCorrectPasswordError(Exception):
    detail = "User not correct password Error"
