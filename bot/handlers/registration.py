from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from services import create_user, get_user_by_username
from .operations import OperationStates


registration_router = Router()


class RegistrationStates(StatesGroup):
    asking_first_name = State()
    asking_last_name = State()
    asking_age = State()
    asking_gender = State()


@registration_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    from_user = message.from_user
    if from_user is None:
        await message.answer("Не удалось определить пользователя.")
        return

    # Проверяем пользователя в API по username
    ext_user = await get_user_by_username(from_user.username)
    if ext_user:
        await state.set_state(OperationStates.awaiting_number)
        await message.answer(
            f"Добро пожаловать, {ext_user['name']}!\n"
            "Введите номер анкеты для прохождения опроса."
        )
        return

    # Если пользователь не найден в API - начинаем регистрацию
    await state.set_state(RegistrationStates.asking_first_name)
    await message.answer(
        "Добро пожаловать! Для работы с ботом необходимо зарегистрироваться.\n\n"
        "Напишите, пожалуйста, ваше имя:"
    )


@registration_router.message(RegistrationStates.asking_first_name, F.text.len() > 0)
async def receive_first_name(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer(
            "Имя не должно быть пустым. Введите имя ещё раз."
        )
        return

    await state.update_data(first_name=text)
    await state.set_state(RegistrationStates.asking_last_name)
    await message.answer("Спасибо! Теперь введите вашу фамилию:")


@registration_router.message(RegistrationStates.asking_last_name, F.text.len() > 0)
async def receive_last_name(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer(
            "Фамилия не должна быть пустой. Введите фамилию ещё раз."
        )
        return

    await state.update_data(last_name=text)
    await state.set_state(RegistrationStates.asking_age)
    await message.answer("Спасибо! Теперь введите ваш возраст (число):")


@registration_router.message(RegistrationStates.asking_age, F.text.len() > 0)
async def receive_age(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    try:
        age = int(text)
        if age < 1 or age > 120:
            await message.answer(
                "Возраст должен быть от 1 до 120 лет. Введите возраст ещё раз."
            )
            return
    except ValueError:
        await message.answer(
            "Возраст должен быть числом. Введите возраст ещё раз."
        )
        return

    await state.update_data(age=age)
    await state.set_state(RegistrationStates.asking_gender)
    await message.answer(
        "Отлично! Теперь выберите пол:\n"
        "M - Мужской\n"
        "F - Женский"
    )


@registration_router.message(RegistrationStates.asking_gender, F.text.len() > 0)
async def receive_gender(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip().upper()

    # Принимаем как буквы, так и полные названия
    if text in ["M", "М", "МУЖСКОЙ", "МУЖ"]:
        gender = "M"
    elif text in ["F", "Ж", "ЖЕНСКИЙ", "ЖЕН"]:
        gender = "F"
    else:
        await message.answer(
            "Пожалуйста, выберите один из вариантов:\n"
            "M - Мужской\n"
            "F - Женский"
        )
        return

    from_user = message.from_user
    if from_user is None:
        await message.answer(
            "Не удалось завершить регистрацию: нет данных пользователя."
        )
        return

    # Получаем все данные регистрации
    data = await state.get_data()

    # Регистрируем пользователя через API
    created = await create_user(
        tg_nickname=from_user.username or "",
        name=data.get("first_name", ""),
        surname=data.get("last_name", ""),
        age=data.get("age", 0),
        gender=gender,
    )

    if created:
        await state.set_state(OperationStates.awaiting_number)
        await message.answer(
            "✅ Регистрация завершена!\n\n"
            "Введите номер анкеты:"
        )
    else:
        await message.answer(
            "❌ Ошибка при регистрации. Попробуйте позже или обратитесь к администратору."
        )

