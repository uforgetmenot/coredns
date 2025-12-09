"""Server-rendered UI routes"""

from __future__ import annotations

from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.services.auth_service import get_auth_service

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="app/templates")
auth_service = get_auth_service()


def _get_session_user(request: Request) -> str | None:
    return request.session.get("user")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render login view."""

    if _get_session_user(request):
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "error": None,
            "user": None,
        },
    )


@router.post("/login", response_class=HTMLResponse)
async def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    """Process login form submissions."""

    try:
        username_authenticated, user_info = auth_service.authenticate(
            username=username, password=password
        )
        request.session["user"] = username_authenticated
        request.session["user_info"] = user_info.model_dump()
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as exc:  # pragma: no cover - UI level feedback only
        status_code = exc.status_code if hasattr(exc, "status_code") else status.HTTP_401_UNAUTHORIZED
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": getattr(exc, "detail", "Authentication failed"),
                "user": None,
            },
            status_code=status_code,
        )


@router.get("/logout")
async def logout(request: Request):
    """Clear session and redirect to login."""

    user = _get_session_user(request)
    if user:
        auth_service.logout(user)
    request.session.clear()
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Render dashboard shell that consumes API data via JS."""

    user = _get_session_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "default_primary_dns": settings.upstream_primary_dns_default,
            "default_secondary_dns": settings.upstream_secondary_dns_default,
        },
    )


@router.get("/records", response_class=HTMLResponse)
async def records_page(request: Request):
    """Render DNS records management page."""

    user = _get_session_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        "records.html",
        {
            "request": request,
            "user": user,
        },
    )


@router.get("/corefile", response_class=HTMLResponse)
async def corefile_page(request: Request):
    """Render Corefile management page."""

    user = _get_session_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        "corefile.html",
        {
            "request": request,
            "user": user,
        },
    )
