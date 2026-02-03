from aiogram.fsm.state import StatesGroup, State

class FemaleVerification(StatesGroup):
    waiting_photo = State()
    waiting_otp = State()
