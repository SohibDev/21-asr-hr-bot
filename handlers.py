from telebot import types
import os
from validators import validate_name, validate_date, validate_nonempty, validate_phone
from storage import save_user_data, update_user_data, DATA_DIR

def start_handler(message, bot):
    bot.send_message(message.chat.id,
        "📩 Kastingda ishtirok etish istagida bo'lgan Yigit-qizlar!\n"
        "Iltimos, quyidagi ma'lumotlarni ketma-ket yuboring.\n\n1. F.I.O")
    bot.register_next_step_handler(message, get_name, bot)

def get_name(message, bot):
    if not validate_name(message.text):
        bot.send_message(message.chat.id, "❌ Iltimos, to'liq F.I.O yuboring (kamida ism va familiya). Qaytadan yozing:")
        bot.register_next_step_handler(message, get_name, bot)
        return
    save_user_data(message.from_user.id, {"fio": message.text})
    bot.send_message(message.chat.id, "2. Tug'ilgan kun, oy, yilingiz (DD.MM.YYYY yoki DD-MM-YYYY):")
    bot.register_next_step_handler(message, get_birthdate, bot)

def get_birthdate(message, bot):
    if not validate_date(message.text):
        bot.send_message(message.chat.id, "❌ Sana noto'g'ri formatda. Iltimos DD.MM.YYYY yoki DD-MM-YYYY ko'rinishida yuboring:")
        bot.register_next_step_handler(message, get_birthdate, bot)
        return
    update_user_data(message.from_user.id, {"birthdate": message.text})
    bot.send_message(message.chat.id, "3. Yashash manzilingiz:")
    bot.register_next_step_handler(message, get_address, bot)

def get_address(message, bot):
    if not validate_nonempty(message.text):
        bot.send_message(message.chat.id, "❌ Manzil bo'sh bo'lishi mumkin emas. Qaytadan yozing:")
        bot.register_next_step_handler(message, get_address, bot)
        return
    update_user_data(message.from_user.id, {"address": message.text})
    bot.send_message(message.chat.id, "4. Qaysi tillarni bilasiz? (Misol: O'zbek, Rus, Ingliz)")
    bot.register_next_step_handler(message, get_languages, bot)

def get_languages(message, bot):
    if not validate_nonempty(message.text):
        bot.send_message(message.chat.id, "❌ Iltimos, tillarni kiriting. Bo'sh qoldirmang:")
        bot.register_next_step_handler(message, get_languages, bot)
        return
    update_user_data(message.from_user.id, {"languages": message.text})
    bot.send_message(message.chat.id, "5. Ish tajribangiz:")
    bot.register_next_step_handler(message, get_experience, bot)

def get_experience(message, bot):
    if not validate_nonempty(message.text):
        bot.send_message(message.chat.id, "❌ Iltimos, ish tajribangizni yozing:")
        bot.register_next_step_handler(message, get_experience, bot)
        return
    update_user_data(message.from_user.id, {"experience": message.text})
    bot.send_message(message.chat.id, "6. Nimalarga qiziqasiz?")
    bot.register_next_step_handler(message, get_interests, bot)

def get_interests(message, bot):
    if not validate_nonempty(message.text):
        bot.send_message(message.chat.id, "❌ Iltimos, qiziqishlaringizni yozing:")
        bot.register_next_step_handler(message, get_interests, bot)
        return
    update_user_data(message.from_user.id, {"interests": message.text})
    bot.send_message(message.chat.id, "7. Telefon raqamingiz:")
    bot.register_next_step_handler(message, get_phone, bot)

def get_phone(message, bot):
    if not validate_phone(message.text):
        bot.send_message(message.chat.id, "❌ Telefon raqam noto'g'ri formatda. Iltimos, faqat raqamlar va +, -, () belgilarini kiriting:")
        bot.register_next_step_handler(message, get_phone, bot)
        return
    update_user_data(message.from_user.id, {"phone": message.text})
    bot.send_message(message.chat.id, "8. Iltimos, fotosuratingizni yuboring (faqat rasm):")
    bot.register_next_step_handler(message, get_photo, bot)

def get_photo(message, bot):
    if not message.photo:
        bot.send_message(message.chat.id, "❌ Bu rasm emas. Iltimos, faqat fotosuratingizni yuboring:")
        bot.register_next_step_handler(message, get_photo, bot)
        return

    photo_id = message.photo[-1].file_id
    file_info = bot.get_file(photo_id)
    downloaded_file = bot.download_file(file_info.file_path)
    photo_path = os.path.join(DATA_DIR, f"{message.from_user.id}.jpg")
    with open(photo_path, 'wb') as f:
        f.write(downloaded_file)

    bot.send_message(message.chat.id, "✅ Arizangiz qabul qilindi, rahmat!")
