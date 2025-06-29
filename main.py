import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import aiohttp
from datetime import datetime

API_TOKEN = '7609005170:AAHZZCUY5D48MjyKEDcfUOnJvtpm5wB0_N4'
ADMIN_ID = 959222282  # O'zingizning Telegram ID

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

users = {}

menu = ReplyKeyboardMarkup(resize_keyboard=True)
menu.add(KeyboardButton("📨 Xabar yuborish"), KeyboardButton("✏️ Ismni tahrirlash"))
menu.add(KeyboardButton("💱 Valyuta kurslari"))

# Start buyrug'i
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    if user_id in users:
        await message.answer("Siz avval ro'yxatdan o'tgansiz.", reply_markup=menu)
    else:
        await message.answer("Salom! Iltimos, ismingizni kiriting:")
        users[user_id] = {"step": "get_name"}

# Ro'yxatdan o'tish
@dp.message_handler(lambda message: users.get(message.from_user.id, {}).get("step") == "get_name")
async def get_name(message: types.Message):
    users[message.from_user.id] = {
        "name": message.text,
        "step": "get_phone"
    }
    kb = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("📞 Raqamni yuborish", request_contact=True))
    await message.answer("Endi telefon raqamingizni yuboring:", reply_markup=kb)

@dp.message_handler(content_types=types.ContentType.CONTACT)
async def get_phone(message: types.Message):
    users[message.from_user.id]["phone"] = message.contact.phone_number
    users[message.from_user.id]["step"] = "done"
    await message.answer("Ro'yxatdan o'tdingiz! Endi menyudan foydalanishingiz mumkin.", reply_markup=menu)

# Tugma: Ismni tahrirlash
@dp.message_handler(lambda message: message.text == "✏️ Ismni tahrirlash")
async def edit_name(message: types.Message):
    users[message.from_user.id]["step"] = "get_name"
    await message.answer("Yangi ismingizni yuboring:")

# Tugma: Valyuta kursi
@dp.message_handler(lambda message: message.text == "💱 Valyuta kurslari")
async def currency_info(message: types.Message):
    today = datetime.today().strftime("%Y-%m-%d")
    url = f"https://cbu.uz/uz/arkhiv-kursov-valyut/json/"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            msg = f"🇺🇿 {today} kundagi MB kurslari:\n"
            for val in data[:3]:  # USD, EUR, RUB
                msg += f"{val['CcyNm_UZ']} ({val['Ccy']}): {val['Rate']} so'm\n"
            await message.answer(msg)

# Tugma: Xabar yuborish
@dp.message_handler(lambda message: message.text == "📨 Xabar yuborish")
async def prompt_message(message: types.Message):
    users[message.from_user.id]["step"] = "send_message"
    await message.answer("Admin uchun xabaringizni yuboring (matn, rasm, audio, video, fayl, gif):")

# Adminga barcha xabarlarni yuborish
@dp.message_handler(content_types=types.ContentType.ANY)
async def forward_to_admin(message: types.Message):
    user = users.get(message.from_user.id)
    if user and user.get("step") == "send_message":
        caption = f"📥 Yangi xabar:\n👤 {user['name']}\n📞 {user['phone']}"
        try:
            if message.text:
                await bot.send_message(ADMIN_ID, f"{caption}\n📝 {message.text}")
            elif message.photo:
                await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption)
            elif message.video:
                await bot.send_video(ADMIN_ID, message.video.file_id, caption=caption)
            elif message.audio:
                await bot.send_audio(ADMIN_ID, message.audio.file_id, caption=caption)
            elif message.document:
                await bot.send_document(ADMIN_ID, message.document.file_id, caption=caption)
            elif message.voice:
                await bot.send_voice(ADMIN_ID, message.voice.file_id, caption=caption)
            elif message.animation:
                await bot.send_animation(ADMIN_ID, message.animation.file_id, caption=caption)
            else:
                await bot.send_message(ADMIN_ID, f"{caption}\n[Fayl turini yuborib bo'lmadi]")
        except Exception as e:
            await message.reply("Xabarni yuborishda xatolik yuz berdi.")
        users[message.from_user.id]["step"] = "done"
        await message.reply("Xabaringiz yuborildi ✅", reply_markup=menu)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
