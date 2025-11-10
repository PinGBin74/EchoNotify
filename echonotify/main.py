from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from echonotify.settings import Settings

settings = Settings()


app = FastAPI(
    title="Omsklingo API",
    description="API for Omsklingo",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "OPTIONS", "DELETE"],
    allow_headers=[
        "Content-type",
        "Authorization",
        "Set-Cookie",
        "X-Requested-With",
    ],
    max_age=settings.CORS_MAX_AGE,
)


app.add_middleware(
    ProxyHeadersMiddleware, trusted_hosts=["localhost", "127.0.0.1"]
)


@app.get("/")
async def root():
    return RedirectResponse(url="/docs")
