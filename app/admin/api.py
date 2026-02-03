from fastapi import APIRouter, Depends

from app.admin.guards import admin_guard
from app.admin.stats import get_admin_stats
from app.admin.views import (
    get_pending_females,
    get_pending_withdrawals,
)
from app.core.admin.actions import (
    approve_female,
    mark_withdrawal_paid,
)

router = APIRouter(
    tags=["Admin"],
    dependencies=[Depends(admin_guard)]
)


# -------------------------
# FEMALE APPROVAL
# -------------------------
@router.get("/females/pending")
async def pending_females():
    return await get_pending_females()


@router.post("/females/{telegram_id}/approve")
async def approve_female_api(telegram_id: int):
    await approve_female(telegram_id)
    return {"status": "approved"}


# -------------------------
# WITHDRAWALS
# -------------------------
@router.get("/withdrawals/pending")
async def pending_withdrawals():
    return await get_pending_withdrawals()


@router.post("/withdrawals/{withdrawal_id}/paid")
async def mark_paid_api(withdrawal_id: int):
    await mark_withdrawal_paid(withdrawal_id)
    return {"status": "paid"}

@router.get("/stats")
async def admin_stats():
    return await get_admin_stats()
