from sqlalchemy.ext.asyncio import AsyncSession
from app.models.female_stats import FemaleStats
from app.database import get_session

class FemaleRegistrationError(Exception):
    pass

async def start_registration(telegram_id: int):
    async with get_session() as session:  # AsyncSession
        existing = await session.get(FemaleStats, telegram_id)
        if existing:
            raise FemaleRegistrationError("ALREADY_REGISTERED")

        female = FemaleStats(
            telegram_id=telegram_id,
            status="pending",
            verified=False
        )
        session.add(female)
        await session.commit()

async def submit_profile(
    telegram_id: int,
    age: int,
    languages: list[str]
):
    if age < 18:
        raise FemaleRegistrationError("UNDERAGE")

    async with get_session() as session:
        female = await session.get(FemaleStats, telegram_id)
        if not female:
            raise FemaleRegistrationError("NOT_REGISTERED")

        female.age = age
        female.languages = languages
        await session.commit()
