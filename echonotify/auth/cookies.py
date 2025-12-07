from fastapi import Response


class CookieManager:
    """
    A class to manage HTTP cookies in the application.
    """

    def __init__(self, response: Response):
        self.response = response

    def set_refresh_token(self, refresh_token: str, expires_in: int) -> None:
        """
        Set a refresh token as an HTTP-only secure cookie.
        """
        self.response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=expires_in,
        )

    def delete_refresh_token(self) -> None:
        """Remove the refresh token cookie."""
        self.response.delete_cookie("refresh_token")

    @staticmethod
    def set_refresh_cookie(
        response: Response, refresh_token: str, expires_in: int
    ) -> None:
        CookieManager(response).set_refresh_token(refresh_token, expires_in)

    @staticmethod
    def delete_refresh_cookie(response: Response) -> None:
        CookieManager(response).delete_refresh_token()
