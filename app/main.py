from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.db import init_db
from app.routers import auth, chat, ideas, pages

app = FastAPI(title="AI Idea Validator API", version="0.3.0")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException):
    if request.url.path.startswith("/ideas") or request.url.path.startswith("/auth") or request.url.path.startswith("/chat") or request.url.path.startswith("/models") or request.url.path.startswith("/prompts"):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    if exc.status_code == 404:
        return HTMLResponse(
            status_code=404,
            content=(
                "<html><body><h1>404 - Page Not Found</h1>"
                "<p>The page does not exist or has been moved.</p>"
                "<a href='/'>Go to homepage</a></body></html>"
            ),
        )
    return HTMLResponse(status_code=exc.status_code, content=f"<html><body><h1>{exc.status_code}</h1><p>{exc.detail}</p></body></html>")


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(auth.router)
app.include_router(ideas.router)
app.include_router(chat.router)
app.include_router(pages.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
