from fastapi import APIRouter, Request, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
import boto3
import uuid
import os

from app.database import AsyncSessionLocal
from app.verification.security import verify_telegram_login
from app.models.female_verification import FemaleVerification
from app.config import AWS_REGION, S3_BUCKET

# -----------------------------------
# Router
# -----------------------------------
router = APIRouter(prefix="/verify", tags=["Verification"])

# -----------------------------------
# AWS S3 CLIENT (PRIVATE OBJECTS)
# -----------------------------------
s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
)

# -----------------------------------
# STEP 1: TELEGRAM LOGIN PAGE
# -----------------------------------
@router.get("/female", response_class=HTMLResponse)
async def female_verify_page():
    with open("app/verification/templates/login.html") as f:
        return f.read()

# -----------------------------------
# STEP 2: TELEGRAM AUTH CALLBACK
# -----------------------------------
@router.get("/female/auth")
async def telegram_auth_callback(request: Request):
    data = dict(request.query_params)

    if not verify_telegram_login(data.copy()):
        raise HTTPException(status_code=403, detail="Telegram auth failed")

    telegram_id = int(data["id"])
    full_name = (
        f"{data.get('first_name', '')} {data.get('last_name', '')}"
    ).strip()

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(FemaleVerification).where(
                FemaleVerification.telegram_id == telegram_id
            )
        )
        record = result.scalar_one_or_none()

        if not record:
            record = FemaleVerification(
                telegram_id=telegram_id,
                full_name=full_name,
                status="pending",
            )
            db.add(record)
        else:
            record.full_name = full_name

        await db.commit()

    return RedirectResponse(
        url=f"/verify/female/upload?telegram_id={telegram_id}",
        status_code=302,
    )

# -----------------------------------
# STEP 3: UPLOAD FORM (UI)
# -----------------------------------
@router.get("/female/upload", response_class=HTMLResponse)
async def upload_page(telegram_id: int):
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Female Verification</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body {{
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
  background: #f4f6f8;
}}
.container {{
  max-width: 420px;
  margin: 40px auto;
  background: #ffffff;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.08);
}}
h1 {{
  font-size: 22px;
  text-align: center;
  margin-bottom: 8px;
}}
.subtitle {{
  text-align: center;
  font-size: 14px;
  color: #666;
  margin-bottom: 24px;
}}
label {{
  font-size: 14px;
  font-weight: 500;
  display: block;
  margin-bottom: 6px;
}}
input {{
  width: 100%;
  padding: 10px;
  border-radius: 8px;
  border: 1px solid #ccc;
  margin-bottom: 16px;
  font-size: 14px;
}}
input[type="file"] {{
  padding: 6px;
}}
button {{
  width: 100%;
  padding: 12px;
  background: #4f46e5;
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
}}
button:hover {{
  background: #4338ca;
}}
.note {{
  margin-top: 16px;
  font-size: 13px;
  color: #555;
  text-align: center;
}}
.secure {{
  margin-top: 8px;
  font-size: 12px;
  color: #888;
  text-align: center;
}}
</style>
</head>

<body>
<div class="container">
  <h1>📸 Female Verification</h1>
  <div class="subtitle">Complete this once to unlock chat access</div>

  <form action="/verify/female/upload" method="post" enctype="multipart/form-data">
    <input type="hidden" name="telegram_id" value="{telegram_id}" />

    <label>📞 Phone Number</label>
    <input type="text" name="phone_number" required />

    <label>📧 Email</label>
    <input type="email" name="email" required />

    <label>📷 Upload Live Photo</label>
    <input type="file" name="photo" accept="image/*" required />

    <button type="submit">Submit Verification</button>
  </form>

  <div class="note">Your photo is reviewed manually by our team.</div>
  <div class="secure">🔒 Secure & private • Stored safely</div>
</div>
</body>
</html>
"""

# -----------------------------------
# STEP 4: HANDLE UPLOAD (LOCKED)
# -----------------------------------
@router.post("/female/upload")
async def handle_upload(
    telegram_id: int = Form(...),
    phone_number: str = Form(...),
    email: str = Form(...),
    photo: UploadFile = Form(...),
):
    if not photo or not photo.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid image")

    # 🔒 LOCKED S3 KEY FORMAT
    ext = os.path.splitext(photo.filename)[1].lower() or ".jpg"
    s3_key = f"female_verification/{telegram_id}/{uuid.uuid4()}{ext}"

    # 🔒 UPLOAD (PRIVATE OBJECT)
    try:
        s3.upload_fileobj(
            photo.file,
            S3_BUCKET,
            s3_key,
            ExtraArgs={
                "ContentType": photo.content_type,
                "ACL": "private",
            },
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Image upload failed. Please try again."
        )

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(FemaleVerification).where(
                FemaleVerification.telegram_id == telegram_id
            )
        )
        record = result.scalar_one_or_none()

        if not record:
            raise HTTPException(status_code=404, detail="User not found")

        record.phone_number = phone_number
        record.email = email
        record.photo_s3_key = s3_key   # ✅ STORE ONLY KEY
        record.status = "pending"

        await db.commit()

    return HTMLResponse("""
    <html>
      <body style="font-family: Arial, sans-serif; text-align: center; margin-top: 40px;">
        <h2>✅ Verification Submitted</h2>
        <p>Your profile is under admin review.</p>
        <p>You may now return to Telegram.</p>
      </body>
    </html>
    """)
