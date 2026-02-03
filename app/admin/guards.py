from fastapi import Request, HTTPException, status


async def admin_guard(request: Request):
    """
    Session-based admin protection.
    Ensures admin is logged in via /admin/login.
    """
    if not request.session.get("admin"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin login required"
        )
