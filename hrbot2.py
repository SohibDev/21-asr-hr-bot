import json
import os
import nest_asyncio
import asyncio
import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters, CallbackQueryHandler
)

# Event loop muammosini hal qilish
nest_asyncio.apply()

# Config o‘qish bekor qilindi, faqat adminlar ro‘yxati beriladi
ADMINS = [5498281083]


# Bosqichlar
(
    ASK_NAME, ASK_AGE, ASK_LOCATION, ASK_PHONE,
    ASK_EDUCATION, ASK_PROFESSION, ASK_EXPERIENCE, ASK_RESUME, ASK_START_DATE
) = range(9)

profession_options = [
    "Dasturchi", "Muhandis", "O'qituvchi", "Shifokor", "Savdo", "Boshqa"
]

# /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salom! Iltimos, to‘liq ism-familiyangizni kiriting:")
    return ASK_NAME

# Admin panel
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        await update.message.reply_text("❌ Siz admin emassiz.")
        return

    keyboard = [
        ["📝 Yangi arizalar", "🔍 Qidiruv"],
        ["📤 Rezyume yuklash", "⭐ Holat belgilash"],
        ["📊 Statistikalar"]
    ]
    await update.message.reply_text("🔐 Admin paneliga xush kelibsiz!", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Yoshingiz nechida?")
    return ASK_AGE

async def ask_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['age'] = update.message.text
    await update.message.reply_text("Qayerda yashaysiz?")
    return ASK_LOCATION

async def ask_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['location'] = update.message.text
    await update.message.reply_text("Telefon raqamingizni kiriting:")
    return ASK_PHONE

async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("Ta’lim darajangiz (masalan: Oliy, Litsey, ...):")
    return ASK_EDUCATION

async def ask_education(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['education'] = update.message.text
    keyboard = [[InlineKeyboardButton(text=prof, callback_data=prof)] for prof in profession_options]
    await update.message.reply_text("Qaysi sohada ishlamoqchisiz?", reply_markup=InlineKeyboardMarkup(keyboard))
    return ASK_PROFESSION

async def profession_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['profession'] = query.data
    await query.edit_message_text(f"Siz tanladingiz: {query.data}\nIsh tajribangiz bormi? Bo‘lsa, qisqacha yozing:")
    return ASK_EXPERIENCE

async def ask_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['experience'] = update.message.text
    keyboard = [[InlineKeyboardButton("O'tish", callback_data='skip_resume')]]
    await update.message.reply_text(
        "Ixtiyoriy: Agar rezyumeingiz bo‘lsa, PDF formatida yuklang.\nYoki 'O'tish' tugmasini bosing.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ASK_RESUME

async def ask_resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query and update.callback_query.data == 'skip_resume':
        await update.callback_query.answer()
        context.user_data['resume_path'] = None
        await update.callback_query.edit_message_text("Rezyume yuklanmadi. Endi ish boshlash vaqtini kiriting:")
        return ASK_START_DATE

    if update.message and update.message.document:
        doc = update.message.document
        if doc.mime_type != 'application/pdf':
            await update.message.reply_text("Iltimos, faqat PDF formatdagi faylni yuboring.")
            return ASK_RESUME

        new_file = await context.bot.get_file(doc.file_id)
        os.makedirs("data/resumes", exist_ok=True)
        filename = f"data/resumes/{update.message.from_user.id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        await new_file.download_to_drive(filename)
        context.user_data['resume_path'] = filename
        await update.message.reply_text("✅ Rezyume qabul qilindi. Endi ish boshlash vaqtini yozing:")
        return ASK_START_DATE

    await update.message.reply_text("Iltimos, rezyume yuboring yoki 'O'tish' tugmasini bosing.")
    return ASK_RESUME

async def ask_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['start_date'] = update.message.text
    user_data = context.user_data.copy()
    user_data['telegram_username'] = update.message.from_user.username or ""
    user_data['telegram_id'] = update.message.from_user.id

    os.makedirs("data", exist_ok=True)
    file_path = "data/users.json"

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    data.append(user_data)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print("✅ users.json fayliga saqlandi.")

    admin_message = (
        f"📩 Yangi ariza:\n"
        f"👤 Ism: {user_data['name']}\n"
        f"📅 Yosh: {user_data['age']}\n"
        f"📍 Manzil: {user_data['location']}\n"
        f"📞 Telefon: {user_data['phone']}\n"
        f"🎓 Ta'lim: {user_data['education']}\n"
        f"💼 Soha: {user_data['profession']}\n"
        f"🧠 Tajriba: {user_data['experience']}\n"
        f"⏱ Ish boshlash: {user_data['start_date']}\n"
        f"🔗 Telegram: @{user_data['telegram_username']}\n"
        f"🆔 ID: {user_data['telegram_id']}"
    )

    for admin_id in ADMINS:
        try:
            if user_data.get('resume_path'):
                with open(user_data['resume_path'], "rb") as f:
                    await context.bot.send_document(chat_id=admin_id, document=f, caption=admin_message)
            else:
                await context.bot.send_message(chat_id=admin_id, text=admin_message)
        except Exception as e:
            print(f"❌ Admin ID {admin_id} ga yuborishda xatolik: {e}")

    await update.message.reply_text("✅ Ma’lumotlaringiz saqlandi. Rahmat!", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Jarayon bekor qilindi.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def main():
    app = ApplicationBuilder().token("7045089929:AAFQLrMyJGGJeBVUZgpvEVqsYp8hmudlxQQ").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            ASK_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_age)],
            ASK_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_location)],
            ASK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            ASK_EDUCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_education)],
            ASK_PROFESSION: [CallbackQueryHandler(profession_chosen)],
            ASK_EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_experience)],
            ASK_RESUME: [
                CallbackQueryHandler(ask_resume, pattern='^skip_resume$'),
                MessageHandler(filters.Document.PDF, ask_resume),
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_resume),
            ],
            ASK_START_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_start_date)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(conv_handler)

    print("🚀 Bot ishga tushdi...")
    await app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
