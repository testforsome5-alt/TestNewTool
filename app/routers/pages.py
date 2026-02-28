from __future__ import annotations

from contextlib import closing

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.core.db import get_conn

router = APIRouter(tags=["pages"])


@router.get("/", response_class=HTMLResponse)
def home() -> str:
    return """
    <html><body>
      <h1>AI Idea Validator</h1>
      <p>Public MVP for startup idea validation.</p>
      <ul>
        <li><a href='/auth/register/page'>Register</a></li>
        <li><a href='/auth/login/page'>Login</a></li>
        <li><a href='/pricing'>Pricing</a></li>
        <li><a href='/privacy'>Privacy</a></li>
        <li><a href='/terms'>Terms</a></li>
        <li><a href='/cookies'>Cookies</a></li>
        <li><a href='/security'>Security</a></li>
      </ul>
    </body></html>
    """


@router.get("/pricing", response_class=HTMLResponse)
def pricing() -> str:
    return "<html><body><h1>Pricing</h1><p>Free / Pro / Team plans.</p></body></html>"


@router.get("/privacy", response_class=HTMLResponse)
def privacy() -> str:
    return "<html><body><h1>Privacy Policy</h1><p>We store account and report data for service delivery.</p></body></html>"


@router.get("/terms", response_class=HTMLResponse)
def terms() -> str:
    return "<html><body><h1>Terms of Service</h1><p>By using the service you accept platform terms.</p></body></html>"


@router.get("/cookies", response_class=HTMLResponse)
def cookies() -> str:
    return "<html><body><h1>Cookie Policy</h1><p>Essential cookies are used for auth and analytics.</p></body></html>"


@router.get("/security", response_class=HTMLResponse)
def security() -> str:
    return "<html><body><h1>Security</h1><p>Token auth, role-based access and DB persistence controls are enabled.</p></body></html>"


@router.get("/ui/user/{user_id}", response_class=HTMLResponse)
def user_dashboard(user_id: str) -> str:
    with closing(get_conn()) as conn:
        rows = conn.execute(
            "SELECT id, title, region, model, created_at FROM reports WHERE user_id = ? ORDER BY id DESC",
            (user_id,),
        ).fetchall()

    rows_html = "".join(
        f"<tr><td>{r['id']}</td><td>{r['title']}</td><td>{r['region']}</td><td>{r['model']}</td><td>{r['created_at']}</td></tr>"
        for r in rows
    ) or "<tr><td colspan='5'>No ideas yet</td></tr>"

    return f"""
    <html><body>
      <h1>User Dashboard</h1>
      <table border='1' cellpadding='6'>
        <tr><th>ID</th><th>Title</th><th>Region</th><th>Model</th><th>Created</th></tr>
        {rows_html}
      </table>
    </body></html>
    """


@router.get("/ui/admin", response_class=HTMLResponse)
def admin_dashboard() -> str:
    with closing(get_conn()) as conn:
        users = conn.execute("SELECT id, email, role, auth_provider, created_at FROM users ORDER BY id DESC").fetchall()
        reports = conn.execute(
            "SELECT id, user_id, title, model, created_at FROM reports ORDER BY id DESC LIMIT 50"
        ).fetchall()

    users_html = "".join(
        f"<tr><td>{u['id']}</td><td>{u['email']}</td><td>{u['role']}</td><td>{u['auth_provider']}</td><td>{u['created_at']}</td></tr>"
        for u in users
    ) or "<tr><td colspan='5'>No users</td></tr>"

    reports_html = "".join(
        f"<tr><td>{r['id']}</td><td>{r['user_id']}</td><td>{r['title']}</td><td>{r['model']}</td><td>{r['created_at']}</td></tr>"
        for r in reports
    ) or "<tr><td colspan='5'>No reports</td></tr>"

    return f"""
    <html><body>
      <h1>Admin Dashboard</h1>
      <h2>Users</h2>
      <table border='1' cellpadding='6'>
        <tr><th>ID</th><th>Email</th><th>Role</th><th>Provider</th><th>Created</th></tr>
        {users_html}
      </table>
      <h2>Recent Idea Reports</h2>
      <table border='1' cellpadding='6'>
        <tr><th>ID</th><th>User ID</th><th>Title</th><th>Model</th><th>Created</th></tr>
        {reports_html}
      </table>
    </body></html>
    """
