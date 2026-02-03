from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from app.config import ADMIN_SECRET

router = APIRouter(tags=["Admin Auth"])


# -------------------------
# LOGIN PAGE
# -------------------------
@router.get("/login", response_class=HTMLResponse)
async def admin_login_page():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>TRUEME Admin Login</title>
    </head>
    <body style="font-family:sans-serif">
        <h2>🔐 TRUEME Admin Login</h2>
        <form method="post">
            <input type="password" name="secret" placeholder="Admin Secret" required />
            <br><br>
            <button type="submit">Login</button>
        </form>
    </body>
    </html>
    """


# -------------------------
# LOGIN ACTION
# -------------------------
@router.post("/login")
async def admin_login(request: Request, secret: str = Form(...)):
    if secret != ADMIN_SECRET:
        raise HTTPException(status_code=401, detail="Invalid admin secret")

    # ✅ create admin session
    request.session["admin"] = True

    return RedirectResponse(
        url="/admin/ui",
        status_code=302
    )


# -------------------------
# LOGOUT
# -------------------------
@router.get("/logout")
async def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse("/admin/login", status_code=302)
