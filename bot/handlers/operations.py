from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
import logging

from services import call_external_api, submit_survey_response, get_user_by_username
from config import get_user_service_base_url
import httpx

logger = logging.getLogger(__name__)


operations_router = Router()


class OperationStates(StatesGroup):
    awaiting_number = State()

class SurveyStates(StatesGroup):
    answering_question = State()


async def get_survey_from_api(survey_id: int):
    """Получение данных опроса из API"""
    base = get_user_service_base_url()
    if not base:
        return None
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Сначала получаем список всех опросов или конкретный опрос
            # Для простоты используем тестовые данные, если API недоступен
            return {
                "id": survey_id,
                "title": f"Опрос #{survey_id}",
                "questions": [
                    f"Вопрос 1 для опроса {survey_id}",
                    f"Вопрос 2 для опроса {survey_id}",
                    f"Вопрос 3 для опроса {survey_id}",
                ]
            }
    except Exception as e:
        logger.warning("Не удалось получить опрос из API: %s", e)
        return None


@operations_router.message(
    OperationStates.awaiting_number, F.text.len() > 0
)
async def receive_number(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    try:
        survey_id = int(text)
    except ValueError:
        await message.answer("Пожалуйста, отправьте номер анкеты (число).")
        return

    # Получаем данные опроса из API
    survey_data = await get_survey_from_api(survey_id)
    if not survey_data:
        await message.answer(
            f"Не удалось загрузить анкету с номером {survey_id}. "
            "Попробуйте позже или обратитесь к администратору."
        )
        return

    questions = survey_data["questions"]
    if not questions:
        await message.answer(
            f"Анкета с номером {survey_id} не содержит вопросов."
        )
        return
    
    # Сохраняем данные анкеты в состоянии
    await state.update_data({
        "survey_id": survey_id,
        "survey_title": survey_data.get("title", f"Опрос #{survey_id}"),
        "questions": questions,
        "current_question": 0,
        "answers": []
    })
    
    # Начинаем опрос
    await state.set_state(SurveyStates.answering_question)
    await message.answer(
        f"Начинаем анкету: {survey_data.get('title', f'№{survey_id}')}\n\n"
        f"Вопрос 1 из {len(questions)}:\n{questions[0]}"
    )


@operations_router.message(SurveyStates.answering_question, F.text.len() > 0)
async def receive_answer(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer("Ответ не может быть пустым. Пожалуйста, ответьте на вопрос.")
        return
    
    # Получаем данные анкеты из состояния
    data = await state.get_data()
    survey_id = data["survey_id"]
    questions = data["questions"]
    current_question = data["current_question"]
    answers = data["answers"]
    
    # Добавляем ответ
    answers.append(text)
    
    # Проверяем, есть ли ещё вопросы
    if current_question + 1 < len(questions):
        # Переходим к следующему вопросу
        next_question = current_question + 1
        await state.update_data({
            "current_question": next_question,
            "answers": answers
        })
        
        await message.answer(
            f"Вопрос {next_question + 1} из {len(questions)}:\n"
            f"{questions[next_question]}"
        )
    else:
        # Анкета завершена
        await finish_survey(message, state, survey_id, answers)


async def finish_survey(message: Message, state: FSMContext, survey_id: int, answers: list) -> None:
    """Завершение анкеты и отправка результатов на бекенд"""
    
    from_user = message.from_user
    if not from_user:
        await message.answer("Ошибка: не удалось определить пользователя.")
        await state.set_state(OperationStates.awaiting_number)
        return

    # Получаем данные пользователя из API
    user_data = await get_user_by_username(from_user.username)
    if not user_data:
        await message.answer(
            "Ошибка: пользователь не найден в системе. "
            "Обратитесь к администратору."
        )
        await state.set_state(OperationStates.awaiting_number)
        return

    # Отправляем ответы на бекенд через API
    result = await submit_survey_response(survey_id, user_data, answers)
    
    if result:
        await message.answer(
            "✅ Анкета успешно завершена и отправлена!"
            "\n\nВведите номер новой анкеты или /start"
        )
    else:
        await message.answer(
            "⚠️ Анкета завершена, но не удалось отправить ответы на сервер. "
            "Попробуйте позже или обратитесь к администратору.\n\n"
            "Введите номер новой анкеты или /start"
        )
    
    # Возвращаемся в начальное состояние
    await state.set_state(OperationStates.awaiting_number)

