from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy import select, func
from sqlalchemy.sql import func as sql_func
import boto3

from app.admin.guards import admin_guard
from app.database import AsyncSessionLocal
from app.models.female_verification import FemaleVerification
from app.models.user import User
from app.config import AWS_REGION, S3_BUCKET

# NOTE: prefix="/admin" is applied when router is included
router = APIRouter(tags=["Admin UI"])

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

s3 = boto3.client("s3", region_name=AWS_REGION)

# -------------------------------------------------
# Helpers
# -------------------------------------------------
def signed_photo_url(key: str) -> str:
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET, "Key": key},
        ExpiresIn=300,
    )

# -------------------------------------------------
# DASHBOARD (UI)
# -------------------------------------------------
@router.get("/ui", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    await admin_guard(request)
    return templates.TemplateResponse("dashboard.html", {"request": request})

# -------------------------------------------------
# DASHBOARD STATS (JSON)
# -------------------------------------------------
@router.get("/stats", response_class=JSONResponse)
async def admin_stats(request: Request):
    await admin_guard(request)

    async with AsyncSessionLocal() as db:
        total_users = await db.scalar(
            select(func.count()).select_from(User)
        )

        verified_females = await db.scalar(
            select(func.count())
            .select_from(FemaleVerification)
            .where(FemaleVerification.status == "approved")
        )

        pending_females = await db.scalar(
            select(func.count())
            .select_from(FemaleVerification)
            .where(FemaleVerification.status == "pending")
        )

    return {
        "users": {
            "total": total_users or 0,
            "females": (verified_females or 0),
            "verified_females": verified_females or 0,
            "pending_females": pending_females or 0,
        },
        "chats": {
            "total": 0,
            "active": 0,
        },
        "payouts": {
            "total": 0,
            "paid": 0,
            "pending": 0,
        },
    }

# -------------------------------------------------
# PENDING FEMALES (DASHBOARD QUEUE)
# -------------------------------------------------
@router.get("/females/pending", response_class=JSONResponse)
async def admin_females_pending(request: Request):
    await admin_guard(request)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(FemaleVerification)
            .where(FemaleVerification.status == "pending")
            .order_by(FemaleVerification.created_at.desc())
        )
        females = result.scalars().all()

    return [
        {
            "telegram_id": f.telegram_id,
            "phone_number": f.phone_number,
            "email": f.email,
        }
        for f in females
    ]

# -------------------------------------------------
# APPROVE / REJECT (DASHBOARD ACTIONS)
# -------------------------------------------------
@router.post("/females/{telegram_id}/approve")
async def approve_female(request: Request, telegram_id: int):
    await admin_guard(request)

    async with AsyncSessionLocal() as db:
        record = await db.scalar(
            select(FemaleVerification)
            .where(FemaleVerification.telegram_id == telegram_id)
        )

        if not record:
            raise HTTPException(status_code=404, detail="Not found")

        record.status = "approved"
        record.reviewed_at = sql_func.now()
        await db.commit()

    return RedirectResponse("/admin/ui", status_code=302)

@router.post("/females/{telegram_id}/reject")
async def reject_female(request: Request, telegram_id: int):
    await admin_guard(request)

    async with AsyncSessionLocal() as db:
        record = await db.scalar(
            select(FemaleVerification)
            .where(FemaleVerification.telegram_id == telegram_id)
        )

        if not record:
            raise HTTPException(status_code=404, detail="Not found")

        record.status = "rejected"
        record.reviewed_at = sql_func.now()
        await db.commit()

    return RedirectResponse("/admin/ui", status_code=302)

# -------------------------------------------------
# VERIFIED FEMALES (VIEW ONLY)
# -------------------------------------------------
@router.get("/females", response_class=HTMLResponse)
async def admin_females(request: Request):
    await admin_guard(request)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(FemaleVerification)
            .where(FemaleVerification.status == "approved")
            .order_by(FemaleVerification.reviewed_at.desc())
        )
        females = result.scalars().all()

    rows = ""
    for f in females:
        photo = "-"
        if f.photo_s3_key:
            url = signed_photo_url(f.photo_s3_key)
            photo = f'<img src="{url}" class="h-12 w-12 rounded object-cover" />'

        rows += f"""
        <tr>
          <td class="p-2">{f.telegram_id}</td>
          <td class="p-2">{f.full_name or "-"}</td>
          <td class="p-2">{f.phone_number or "-"}</td>
          <td class="p-2">{f.email or "-"}</td>
          <td class="p-2">{photo}</td>
          <td class="p-2">{f.reviewed_at.strftime("%Y-%m-%d") if f.reviewed_at else "-"}</td>
        </tr>
        """

    return HTMLResponse(f"""
<!DOCTYPE html>
<html>
<head>
<title>Verified Females</title>
<script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 p-6">

<h2 class="text-xl font-semibold mb-2">👩 Verified Females</h2>
<p class="text-gray-500 mb-4 text-sm">
View-only list. All approvals are handled from the dashboard.
</p>

<div class="bg-white rounded shadow">
<table class="w-full text-sm">
<tr class="bg-gray-800 text-white">
  <th class="p-2">Telegram ID</th>
  <th class="p-2">Name</th>
  <th class="p-2">Phone</th>
  <th class="p-2">Email</th>
  <th class="p-2">Photo</th>
  <th class="p-2">Verified At</th>
</tr>
{rows or "<tr><td colspan='6' class='p-4 text-center'>No verified females</td></tr>"}
</table>
</div>

<a href="/admin/ui" class="text-indigo-600 block mt-4">← Back to Dashboard</a>

</body>
</html>
""")

# -------------------------------------------------
# ALL USERS (VIEW ONLY)  ✅ FIXES /admin/users
# -------------------------------------------------
@router.get("/users", response_class=HTMLResponse)
async def admin_users(request: Request):
    await admin_guard(request)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).order_by(User.created_at.desc())
        )
        users = result.scalars().all()

    rows = "".join(
        f"""
        <tr>
          <td class="p-2">{u.telegram_id}</td>
          <td class="p-2">{u.created_at.strftime('%Y-%m-%d')}</td>
        </tr>
        """
        for u in users
    )

    return HTMLResponse(f"""
<!DOCTYPE html>
<html>
<head>
<title>All Users</title>
<script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 p-6">

<h2 class="text-xl font-semibold mb-4">👥 All Users</h2>

<div class="bg-white rounded shadow">
<table class="w-full text-sm">
<tr class="bg-gray-800 text-white">
  <th class="p-2">Telegram ID</th>
  <th class="p-2">Joined</th>
</tr>
{rows or "<tr><td colspan='2' class='p-4 text-center'>No users</td></tr>"}
</table>
</div>

<a href="/admin/ui" class="text-indigo-600 block mt-4">← Back to Dashboard</a>

</body>
</html>
""")
