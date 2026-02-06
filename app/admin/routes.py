from fastapi import APIRouter, Request, Depends, Body
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from app.database import AsyncSessionLocal

# =================================================
# Router
# =================================================
router = APIRouter(prefix="/admin", tags=["Admin"])
templates = Jinja2Templates(directory="app/admin/templates")

# =================================================
# Admin Auth (SESSION BASED)
# =================================================
def admin_required(request: Request):
    if not request.session.get("admin"):
        raise RedirectResponse("/admin/login", status_code=302)

# =================================================
# AUDIT LOGGER (IMMUTABLE)
# =================================================
async def audit_log(
    admin_id: int,
    action: str,
    entity: str,
    entity_id: int | None = None,
    meta: dict | None = None
):
    async with AsyncSessionLocal() as db:
        await db.execute(
            text("""
                INSERT INTO admin_audit_logs
                (admin_id, action, entity, entity_id, meta)
                VALUES (:admin_id, :action, :entity, :entity_id, :meta)
            """),
            {
                "admin_id": admin_id,
                "action": action,
                "entity": entity,
                "entity_id": entity_id,
                "meta": meta,
            }
        )
        await db.commit()

# =================================================
# DASHBOARD
# =================================================
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, _=Depends(admin_required)):
    return templates.TemplateResponse("dashboard.html", {"request": request})

# =================================================
# SETTINGS
# =================================================
ADMIN_SETTINGS = {
    "pause_matching": False,
    "pause_payments": False,
    "commission": 20,
    "session_limit": 10,
}

@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, _=Depends(admin_required)):
    return templates.TemplateResponse("settings.html", {"request": request})

@router.get("/settings/data")
async def get_settings(_=Depends(admin_required)):
    return ADMIN_SETTINGS

@router.post("/settings/save")
async def save_settings(
    request: Request,
    data: dict = Body(...),
    _=Depends(admin_required)
):
    admin_id = request.session["admin"]

    ADMIN_SETTINGS.update({
        "pause_matching": bool(data.get("pause_matching")),
        "pause_payments": bool(data.get("pause_payments")),
        "commission": int(data.get("commission", 0)),
        "session_limit": int(data.get("session_limit", 0)),
    })

    await audit_log(
        admin_id=admin_id,
        action="settings_updated",
        entity="settings",
        meta=data
    )

    return {"ok": True}

# =================================================
# WITHDRAWALS
# =================================================
@router.get("/withdrawals", response_class=HTMLResponse)
async def withdrawals_page(request: Request, _=Depends(admin_required)):
    return templates.TemplateResponse("withdrawals.html", {"request": request})

@router.get("/withdrawals/data")
async def withdrawals_data(_=Depends(admin_required)):
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("""
            SELECT id, user_id, amount, status,
                   screenshot_url, created_at, paid_at
            FROM withdrawals
            ORDER BY created_at DESC
        """))
        return result.mappings().all()

@router.post("/withdrawals/{wid}/approve")
async def approve_withdrawal(
    wid: int,
    request: Request,
    _=Depends(admin_required)
):
    admin_id = request.session["admin"]

    async with AsyncSessionLocal() as db:
        await db.execute(text("""
            UPDATE withdrawals
            SET status = 'approved'
            WHERE id = :id AND status = 'pending'
        """), {"id": wid})
        await db.commit()

    await audit_log(
        admin_id=admin_id,
        action="withdrawal_approved",
        entity="withdrawals",
        entity_id=wid
    )

    return {"ok": True}

@router.post("/withdrawals/{wid}/reject")
async def reject_withdrawal(
    wid: int,
    request: Request,
    _=Depends(admin_required)
):
    admin_id = request.session["admin"]

    async with AsyncSessionLocal() as db:
        await db.execute(text("""
            UPDATE withdrawals
            SET status = 'rejected'
            WHERE id = :id AND status = 'pending'
        """), {"id": wid})
        await db.commit()

    await audit_log(
        admin_id=admin_id,
        action="withdrawal_rejected",
        entity="withdrawals",
        entity_id=wid
    )

    return {"ok": True}

@router.post("/withdrawals/{wid}/pay")
async def mark_paid(
    wid: int,
    request: Request,
    data: dict = Body(...),
    _=Depends(admin_required)
):
    admin_id = request.session["admin"]
    method = data.get("method")
    ref = data.get("ref")

    if not method or not ref:
        return {"error": "Missing payout details"}

    async with AsyncSessionLocal() as db:
        await db.execute(text("""
            UPDATE withdrawals
            SET status = 'paid',
                payout_method = :method,
                payout_ref = :ref,
                paid_at = NOW()
            WHERE id = :id AND status = 'approved'
        """), {
            "id": wid,
            "method": method,
            "ref": ref
        })
        await db.commit()

    await audit_log(
        admin_id=admin_id,
        action="withdrawal_paid",
        entity="withdrawals",
        entity_id=wid,
        meta=data
    )

    return {"ok": True}

# =================================================
# WALLETS (READ-ONLY)
# =================================================
@router.get("/wallets", response_class=HTMLResponse)
async def wallets_page(request: Request, _=Depends(admin_required)):
    return templates.TemplateResponse("wallets.html", {"request": request})

@router.get("/wallets/data")
async def wallets_data(_=Depends(admin_required)):
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("""
            SELECT
              u.id AS user_id,
              COALESCE(SUM(CASE WHEN l.type = 'earn' THEN l.amount ELSE 0 END), 0) AS total_earned,
              COALESCE(SUM(CASE WHEN w.status = 'paid' THEN w.amount ELSE 0 END), 0) AS total_withdrawn
            FROM users u
            LEFT JOIN ledger l ON l.user_id = u.id
            LEFT JOIN withdrawals w ON w.user_id = u.id
            GROUP BY u.id
            ORDER BY u.id
        """))

        rows = result.mappings().all()
        return [
            {
                "user_id": r["user_id"],
                "total_earned": float(r["total_earned"]),
                "total_withdrawn": float(r["total_withdrawn"]),
                "balance": float(r["total_earned"] - r["total_withdrawn"])
            }
            for r in rows
        ]

# =================================================
# LEDGER (READ-ONLY)
# =================================================
@router.get("/ledger", response_class=HTMLResponse)
async def ledger_page(request: Request, _=Depends(admin_required)):
    return templates.TemplateResponse("ledger.html", {"request": request})

@router.get("/ledger/data")
async def ledger_data(
    user_id: int | None = None,
    _=Depends(admin_required)
):
    query = """
        SELECT id, user_id, type, amount, ref, created_at
        FROM ledger
    """
    params = {}

    if user_id:
        query += " WHERE user_id = :uid"
        params["uid"] = user_id

    query += " ORDER BY created_at DESC LIMIT 500"

    async with AsyncSessionLocal() as db:
        result = await db.execute(text(query), params)
        return result.mappings().all()

# =================================================
# SESSIONS (READ-ONLY)
# =================================================
@router.get("/sessions", response_class=HTMLResponse)
async def sessions_page(request: Request, _=Depends(admin_required)):
    return templates.TemplateResponse("sessions.html", {"request": request})

@router.get("/sessions/data")
async def sessions_data(_=Depends(admin_required)):
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("""
            SELECT id, user_a, user_b, started_at, ended_at
            FROM sessions
            ORDER BY started_at DESC
            LIMIT 500
        """))
        return result.mappings().all()


# =================================================
# AUDIT LOG UI
# =================================================
@router.get("/audit", response_class=HTMLResponse)
async def audit_page(request: Request, _=Depends(admin_required)):
    return templates.TemplateResponse(
        "audit_logs.html",
        {"request": request}
    )

@router.get("/audit/data")
async def audit_data(_=Depends(admin_required)):
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("""
            SELECT
              id,
              admin_id,
              action,
              entity,
              entity_id,
              created_at
            FROM admin_audit_logs
            ORDER BY created_at DESC
            LIMIT 500
        """))
        return result.mappings().all()

# =================================================
# ANALYTICS DASHBOARD
# =================================================
@router.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request, _=Depends(admin_required)):
    return templates.TemplateResponse(
        "analytics.html",
        {"request": request}
    )

@router.get("/analytics/data")
async def analytics_data(_=Depends(admin_required)):
    async with AsyncSessionLocal() as db:

        # Daily revenue (last 7 days)
        revenue = await db.execute(text("""
            SELECT
              DATE(created_at) AS day,
              SUM(amount) AS total
            FROM ledger
            WHERE type = 'earn'
            GROUP BY day
            ORDER BY day DESC
            LIMIT 7
        """))

        # Withdrawals summary
        withdrawals = await db.execute(text("""
            SELECT
              COUNT(*) AS count,
              COALESCE(SUM(amount), 0) AS total
            FROM withdrawals
            WHERE status = 'paid'
        """))

        # Sessions summary
        sessions = await db.execute(text("""
            SELECT
              COUNT(*) AS total,
              COUNT(*) FILTER (WHERE ended_at IS NULL) AS active
            FROM sessions
        """))

        return {
            "revenue": revenue.mappings().all()[::-1],
            "withdrawals": withdrawals.mappings().first(),
            "sessions": sessions.mappings().first()
        }
