from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
import random
import string
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import asyncio

from config import BOT_TOKEN
import database as db

  #Брать токен из ОП, можно реализовать через файл
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

  #class = FSM -  состояния, в котором может быть бот
class RegisterState(StatesGroup):
    waiting_for_name = State()


class WishState(StatesGroup):
    waiting_description = State()
    waiting_link = State()
    waiting_price = State()


class GroupViewState(StatesGroup):
    choosing_group = State()
    choosing_user = State()

class GroupManageState(StatesGroup):
    waiting_group_name = State()
    waiting_invite_code = State()


    #Основное меню (def - кнопки)
def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Профиль")],
            [KeyboardButton(text="🎁 Добавить желание")],
            [KeyboardButton(text="📋 Мои желания")],
            [KeyboardButton(text="👥 Группы")],
            [KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True
    )

    #Меню группы (кнопки)
def groups_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📂 Мои группы")],
            [KeyboardButton(text="➕ Создать группу")],
            [KeyboardButton(text="🔑 Вступить в группу")],
            [KeyboardButton(text="⬅️ Назад")],
            [KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True
    )
    #dp. - регистрация обработчика, lambda - условия для его вызова, прим /start
    #Вызов функии "отмена"
@dp.message(lambda m: m.text in ["❌ Отмена", "⬅️ Назад"])
async def cancel_any(message: types.Message, state: FSMContext):
    await state.clear() #очистить состояние
    await message.answer("Ок, отменил ✅", reply_markup=main_menu())

@dp.message(lambda m: m.text == "👤 Профиль")
async def profile(message: types.Message, state: FSMContext):
    await state.clear()
    user = db.get_user_by_tg(message.from_user.id)
    if not user:
        await message.answer("Сначала /start")
        return

    await message.answer(
        f"👤 Профиль\n\n"
        f"Имя: {user[3]}\n"
        f"Telegram: @{user[2]}",
        reply_markup=main_menu()
    )

    #lambda - простая функция, может быть заменена на усл. check и тп. Это просто X который сопоставляет Dispatcher и отправляет хендлеру
    #Хендлер - функция, которая реагирует на команду (например присылает ответ на определенное сообщение) 
    #Вызов гл.меню
@dp.message(Command("menu"))
async def menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню", reply_markup=main_menu())

@dp.message(lambda m: m.text == "🎁 Добавить желание")
async def add_wish_button(message: types.Message, state: FSMContext):
    user = db.get_user_by_tg(message.from_user.id)
    if not user:
        await message.answer("Сначала /start")
        return

    
    await state.clear()
    await state.set_state(WishState.waiting_description)

    await message.answer(
        "🎁 Добавление желания\n\n"
        "1/3 Напиши описание желания (например: “Наушники Sony”)\n"
        "Или нажми ❌ Отмена",
        reply_markup=main_menu()
    )


    #Защита от null значения
@dp.message(WishState.waiting_description)
async def wish_step_description(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if not text:
        await message.answer("Описание не может быть пустым. Напиши описание желания:")
        return

    await state.update_data(description=text)
    await state.set_state(WishState.waiting_link)

    await message.answer(
        "2/3 Отправь ссылку на товар или напиши `нет`",
        reply_markup=main_menu()
    )

@dp.message(WishState.waiting_link)
async def wish_step_link(message: types.Message, state: FSMContext):
    text = message.text.strip()

    link = ""
    if text.lower() not in ["нет", "no", "-"]:
        link = text  

    await state.update_data(link=link)
    await state.set_state(WishState.waiting_price)

    await message.answer(
        "3/3 Укажи цену (например: 5000₽) или напиши `нет`",
        reply_markup=main_menu()
    )

@dp.message(WishState.waiting_price)
async def wish_step_price(message: types.Message, state: FSMContext):
    text = message.text.strip()

    price = ""
    if text.lower() not in ["нет", "no", "-"]:
        price = text  

    data = await state.get_data()
    description = data.get("description", "")
    link = data.get("link", "")

    user = db.get_user_by_tg(message.from_user.id)
    if not user:
        await message.answer("Сначала /start")
        await state.clear()
        return

    db.add_wish(user[0], description, link, price)

    # итоговая “карточка”
    result = "✅ Желание добавлено!\n\n"
    result += f"Описание: {description}\n"
    result += f"Ссылка: {link if link else '—'}\n"
    result += f"Цена: {price if price else '—'}\n"

    await message.answer(result, reply_markup=main_menu())
    await state.clear()


from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def send_my_wishes(message: types.Message, user_id: int):
    wishes = db.get_wishes_with_id(user_id)

    if not wishes:
        await message.answer("У тебя пока нет желаний 🙃", reply_markup=main_menu())
        return

    text = "📋 Твои желания:\n\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[])

    for idx, (wish_id, d, l, p) in enumerate(wishes, start=1):
        text += f"{idx}) {d}\n"
        if l:
            text += f"{l}\n"
        if p:
            text += f"Цена: {p}\n"
        text += "\n"

        kb.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"❌ Удалить #{idx}",
                callback_data=f"delwish:{wish_id}"
            )
        ])

    await message.answer(text, reply_markup=kb)

    #Карточка "группы"

@dp.message(lambda m: m.text == "👥 Группы")
async def groups_root(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Меню групп:", reply_markup=groups_menu())


@dp.message(lambda m: m.text == "➕ Создать группу")
async def create_group_button(message: types.Message, state: FSMContext):
    user = db.get_user_by_tg(message.from_user.id)
    if not user:
        await message.answer("Сначала /start")
        return

    await message.answer("Введи название новой группы:")
    await state.set_state(GroupManageState.waiting_group_name)

@dp.message(lambda m: m.text == "🔑 Вступить в группу")
async def join_group_button(message: types.Message, state: FSMContext):
    user = db.get_user_by_tg(message.from_user.id)
    if not user:
        await message.answer("Сначала /start")
        return

    await message.answer("Введи код группы:")
    await state.set_state(GroupManageState.waiting_invite_code)


    #Генератор кода
def gen_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

@dp.message(lambda m: m.text == "📂 Мои группы")
async def my_groups(message: types.Message, state: FSMContext):
    user = db.get_user_by_tg(message.from_user.id)
    if not user:
        await message.answer("Сначала /start")
        return

    groups = db.get_groups_for_user(user[0])
    if not groups:
        await message.answer("Ты пока не состоишь ни в одной группе 🙃", reply_markup=groups_menu())
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for group_id, name in groups:
        kb.inline_keyboard.append([
    InlineKeyboardButton(text=name, callback_data=f"group:{group_id}")
        ])

    await message.answer("Выбери группу:", reply_markup=kb)

@dp.message(GroupManageState.waiting_group_name)
async def create_group_step2(message: types.Message, state: FSMContext):
    user = db.get_user_by_tg(message.from_user.id)
    if not user:
        await message.answer("Сначала /start")
        await state.clear()
        return

    group_name = message.text.strip()
    code = gen_code()

    db.create_group(group_name, code)

    # Найти группу по коду
    group = db.get_group_by_code(code)

    # Создатель сам заходит в свою группу
    db.add_user_to_group_auto(
        group_id=group[0],
        user_id=user[0],
        telegram_username=message.from_user.username,
        telegram_id=message.from_user.id
    )

    await message.answer(
        f"Группа создана 🎉\nКод приглашения: `{code}`\n\nТы автоматически добавлен в группу ✅",
        parse_mode="Markdown",
        reply_markup=groups_menu()
    )
    await state.clear()

@dp.message(GroupManageState.waiting_invite_code)
async def join_group_step2(message: types.Message, state: FSMContext):
    user = db.get_user_by_tg(message.from_user.id)
    if not user:
        await message.answer("Сначала /start")
        await state.clear()
        return

    code = message.text.strip()
    group = db.get_group_by_code(code)

    if not group:
        await message.answer("Группа не найдена 😕 Проверь код и попробуй ещё раз.", reply_markup=groups_menu())
        return

    db.add_user_to_group_auto(
        group_id=group[0],
        user_id=user[0],
        telegram_username=message.from_user.username,
        telegram_id=message.from_user.id
    )

    await message.answer(
        f"Ты вступил в группу: {group[1]} ✅",
        reply_markup=groups_menu()
    )
    await state.clear()


@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    user = db.get_user_by_tg(message.from_user.id)

    if user:
        await message.answer(
    "Ты уже зарегистрирован 🙂",
    reply_markup=main_menu()
)
        return

    await message.answer("Привет! Напиши имя для своей карточки:")
    await state.set_state(RegisterState.waiting_for_name)
@dp.message(RegisterState.waiting_for_name)
async def get_name(message: types.Message, state: FSMContext):
    db.add_user(
        message.from_user.id,
        message.from_user.username,
        message.text
    )

    await message.answer(
    "Готово! Профиль создан 🎉",
    reply_markup=main_menu()
)
    await state.clear()



@dp.message(Command("add_wish"))
async def add_wish_command(message: types.Message, state: FSMContext):
    await add_wish_button(message, state)

    #callback - вернуть значение после запроса (прим. вывести список желаний из БД // список пользователей)

@dp.callback_query(lambda c: c.data == "groups:menu")
async def groups_menu_back(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Меню групп:", reply_markup=groups_menu())
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("group:"))
async def choose_group(callback: types.CallbackQuery, state: FSMContext):
    group_id = int(callback.data.split(":")[1])

    users = db.get_users_in_group(group_id)
    if not users:
        await callback.message.answer("В группе пока нет участников")
        await callback.answer()
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for username, user_id in users:
        kb.inline_keyboard.append([
            InlineKeyboardButton(
                text=username,
                callback_data=f"user:{user_id}"
            )
        ])

    # Кнопка "назад"
    kb.inline_keyboard.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data="groups:menu")
    ])

    await callback.message.answer("Выбери пользователя:", reply_markup=kb)
    await state.set_state(GroupViewState.choosing_user)
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("user:"))
async def show_wishes(callback: types.CallbackQuery):
    data = callback.data

    target_user_id = int(data.split(":")[1])
    current_user = db.get_user_by_tg(callback.from_user.id)

    if not current_user:
        await callback.answer("Ты не зарегистрирован")
        return

    current_user_id = current_user[0]

    has_access = db.users_have_common_group(current_user_id, target_user_id)
    if not has_access:
        await callback.message.answer("⛔ У тебя нет доступа к желаниям этого пользователя")
        await callback.answer()
        return

    wishes = db.get_wishes(target_user_id)
    if not wishes:
        await callback.message.answer("У пользователя пока нет желаний")
        await callback.answer()
        return

    text = "🎁 Желания:\n\n"
    for d, l, p in wishes:
        text += f"• {d}\n"
        if l:
            text += f"{l}\n"
        if p:
            text += f"Цена: {p}\n"
        text += "\n"

    await callback.message.answer(text)
    await callback.answer()



@dp.callback_query(lambda c: c.data.startswith("delwish:"))
async def delete_wish_cb(callback: types.CallbackQuery):
    user = db.get_user_by_tg(callback.from_user.id)
    if not user:
        await callback.answer("Сначала /start")
        return

    wish_id = int(callback.data.split(":")[1])
    deleted = db.delete_wish(user[0], wish_id)

    if deleted:
        await callback.answer("Удалено ✅")
    else:
        await callback.answer("Не найдено или нет доступа", show_alert=True)

    try:
        await callback.message.delete()
    except Exception:
        pass

    await send_my_wishes(callback.message, user[0])


@dp.message(lambda m: m.text == "📋 Мои желания")
async def my_wishes(message: types.Message, state: FSMContext):
    await state.clear()

    user = db.get_user_by_tg(message.from_user.id)
    if not user:
        await message.answer("Сначала /start")
        return

    await send_my_wishes(message, user[0])


@dp.message()
async def fallback(message: types.Message, state: FSMContext):

    if await state.get_state() is not None:
        return

    user = db.get_user_by_tg(message.from_user.id)

    if not user:
        await message.answer(
            "Привет! Я бот для вишлиста 🎁\n\n"
            "Чтобы начать, нажми /start\n"
            "После регистрации появится меню 🙂"
        )
        return

    await message.answer("Открываю меню 🙂", reply_markup=main_menu())



async def main():
    db.init_db()     # Инициализация базы данных
    await dp.start_polling(bot)    # Ожидание сообщений от Telegram

    #Прямой запуск файла (python3 bot.py)
if __name__ == "__main__":
    asyncio.run(main())