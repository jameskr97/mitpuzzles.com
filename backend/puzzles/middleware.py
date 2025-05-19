from http.cookies import SimpleCookie

from channels.middleware import BaseMiddleware


class CookieMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        # Extract and parse cookies
        headers = dict(scope.get("headers", []))
        if b"cookie" in headers:
            cookie_header = headers[b"cookie"].decode("utf-8")
            cookies = SimpleCookie()
            cookies.load(cookie_header)

            # Copy into scope["cookies"]
            scope["cookies"] = {key: morsel.value for key, morsel in cookies.items()}
        else:
            scope["cookies"] = {}

        return await super().__call__(scope, receive, send)
