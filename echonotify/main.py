from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from echonotify.auth.handlers import router as auth_router
from echonotify.chat.handlers import router as chat_router
from echonotify.orders.handlers import router as orders_router
from echonotify.settings import Settings
from echonotify.users.user_creation.handlers import router as users_router

settings = Settings()

# Redis and Celery are initialized separately in their respective modules


app = FastAPI(
    title="Echonotify API",
    description="API for Echonotify",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "OPTIONS", "DELETE"],
    allow_headers=[
        "Content-type",
        "Authorization",
        "Set-Cookie",
        "X-Requested-With",
    ],
    max_age=settings.CORS_MAX_AGE or 600,
)


app.add_middleware(
    ProxyHeadersMiddleware, trusted_hosts=["localhost", "127.0.0.1"]
)


@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


app.include_router(auth_router)

app.include_router(users_router)

app.include_router(orders_router)

app.include_router(chat_router)


# Mount static files
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")
