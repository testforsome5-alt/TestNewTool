from __future__ import annotations

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse

from app.models.schemas import LoginInput, RegisterInput, UserOut
from app.services.auth_service import login_user, oauth_callback, oauth_start, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
def register(payload: RegisterInput) -> UserOut:
    return register_user(payload)


@router.post("/login", response_model=UserOut)
def login(payload: LoginInput) -> UserOut:
    return login_user(payload)


@router.get("/oauth/{provider}/start")
def oauth_provider_start(provider: str, request: Request) -> dict[str, str]:
    return {"provider": provider, "authorize_url": oauth_start(provider, str(request.base_url).rstrip("/"))}


@router.get("/oauth/{provider}/callback", response_model=UserOut)
def oauth_provider_callback(provider: str, email: str | None = Query(default=None)) -> UserOut:
    return oauth_callback(provider, email)


@router.get("/login/page", response_class=HTMLResponse)
def login_page() -> str:
    return """
    <html><body>
      <h1>Login</h1>
      <form method='post' action='/auth/login'>
        <label>Email <input name='email' /></label><br/>
        <label>Password <input type='password' name='password' /></label><br/>
        <p>Use API clients for JSON auth requests.</p>
      </form>
      <h3>Social login</h3>
      <ul>
        <li><a href='/auth/oauth/google/start'>Continue with Google</a></li>
        <li><a href='/auth/oauth/github/start'>Continue with GitHub</a></li>
        <li><a href='/auth/oauth/apple/start'>Continue with Apple</a></li>
        <li><a href='/auth/oauth/microsoft/start'>Continue with Microsoft</a></li>
      </ul>
    </body></html>
    """


@router.get("/register/page", response_class=HTMLResponse)
def register_page() -> str:
    return """
    <html><body>
      <h1>Register</h1>
      <form method='post' action='/auth/register'>
        <label>Email <input name='email' /></label><br/>
        <label>Password <input type='password' name='password' /></label><br/>
        <label>Role
          <select name='role'>
            <option value='user'>user</option>
            <option value='admin'>admin</option>
          </select>
        </label>
        <p>Use API clients for JSON registration requests.</p>
      </form>
    </body></html>
    """
