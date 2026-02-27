import asyncio
import sqlite3
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)

# --- КОНФИГУРАЦИЯ ---
API_TOKEN = '8670035869:AAEkJ95Jpcsqqp06zHnsh1Ch5BtfdqbyP4o'
OWNER_ID = 7458899849  # ВАШ ID (узнать в @userinfobot)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- РАБОТА С БАЗОЙ ДАННЫХ ---
def init_db():
    conn = sqlite3.connect('admin_system.db')
    cursor = conn.cursor()
    # Структура: username, user_id, нарушения, наказания, день, неделя, месяц
    cursor.execute('''CREATE TABLE IF NOT EXISTS admins 
                      (username TEXT PRIMARY KEY, 
                       user_id INTEGER DEFAULT 0,
                       violations INTEGER DEFAULT 0, 
                       punishments INTEGER DEFAULT 0,
                       msg_day INTEGER DEFAULT 0,
                       msg_week INTEGER DEFAULT 0,
                       msg_month INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

def db_execute(query, params):
    conn = sqlite3.connect('admin_system.db')
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    conn.close()

def get_admin(username):
    conn = sqlite3.connect('admin_system.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admins WHERE username = ?", (username.lower().replace("@", ""),))
    res = cursor.fetchone()
    conn.close()
    return res

# --- ЛОГИКА СЧЕТЧИКА СООБЩЕНИЙ ---
@dp.message(F.chat.type.in_({"group", "supergroup"}), ~F.text.startswith('/'))
async def message_handler(message: types.Message):
    if not message.from_user.username:
        return
    
    username = message.from_user.username.lower()
    admin_data = get_admin(username)
    
    if admin_data:
        # Обновляем ID (если еще не было) и прибавляем сообщения
        db_execute('''UPDATE admins SET 
                      user_id = ?,
                      msg_day = msg_day + 1, 
                      msg_week = msg_week + 1, 
                      msg_month = msg_month + 1 
                      WHERE username = ?''', (message.from_user.id, username))

# --- КОМАНДЫ ВЛАДЕЛЬЦА ---

@dp.message(Command("add_admin"))
async def add_admin_cmd(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    args = message.text.split()
    if len(args) < 2:
        return await message.answer("Использование: /add_admin @username")
    
    user = args[1].lower().replace("@", "")
    try:
        db_execute("INSERT INTO admins (username) VALUES (?)", (user,))
        await message.answer(f"✅ Админ @{user} добавлен в список.")
    except:
        await message.answer("❌ Этот админ уже есть в базе.")

@dp.message(Command("set_violation"))
async def set_violation_cmd(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    args = message.text.split()
    if len(args) < 3:
        return await message.answer("Формат: /set_violation @username число")
    
    user, count = args[1].lower().replace("@", ""), args[2]
    db_execute("UPDATE admins SET violations = ? WHERE username = ?", (count, user))
    await message.answer(f"⚠️ У админа @{user} теперь {count} нарушений.")

@dp.message(Command("set_punish"))
async def set_punish_cmd(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    args = message.text.split()
    if len(args) < 3:
        return await message.answer("Формат: /set_punish @username число")
    
    user, count = args[1].lower().replace("@", ""), args[2]
    db_execute("UPDATE admins SET punishments = ? WHERE username = ?", (count, user))
    await message.answer(f"⚔️ Админ @{user} наказал других: {count} раз.")

# --- ПРОСМОТР АНКЕТЫ (С АВАТАРКОЙ) ---

@dp.message(Command("rate_admin"))
async def view_admin_card(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        return await message.answer("Введите: /rate_admin @username")
    
    username = args[1].lower().replace("@", "")
    data = get_admin(username)
    
    if not data:
        return await message.answer("Этого человека нет в списке админов.")

    # Индексы согласно БД: 0:user, 1:uid, 2:violation, 3:punish, 4:day, 5:week, 6:month
    info_text = (
        f"👤 **Админ:** @{data[0]}\n"
        f"🆔 **ID:** `{data[1] if data[1] != 0 else 'Не зафиксирован'}`\n\n"
        f"📊 **Сообщения:**\n"
        f"└ День: `{data[4]}` | Неделя: `{data[5]}` | Месяц: `{data[6]}`\n\n"
        f"🚫 **Нарушений правил:** {data[2]}\n"
        f"⚔️ **Наказал нарушителей:** {data[3]}\n"
    )

    # Пробуем получить аватарку
    if data[1] != 0:
        try:
            photos = await bot.get_user_profile_photos(data[1], limit=1)
            if photos.total_count > 0:
                return await message.answer_photo(
                    photos.photos[0][-1].file_id, 
                    caption=info_text, 
                    parse_mode="Markdown"
                )
        except:
            pass
    
    await message.answer(info_text, parse_mode="Markdown")

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == '__main__':

    asyncio.run(main())
