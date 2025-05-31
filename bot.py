import os
import sqlite3
import json
from telegram.constants import ParseMode
from telegram import Update, InputFile, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler, CallbackQueryHandler
)

# === TOKEN VA ADMIN ===
BOT_TOKEN = "7761246714:AAEL1j05-2gOImgVmaTPAuMBe9uHuXrtfUQ"
ADMIN_IDS = [7546949428]  # O‘zingizning ID’ingiz bilan almashtiring

# === BOSQICHLAR ===
FULL_NAME, AGE, PROFESSION, PHONE, PHOTO, CV = range(6)

# === DATABASE FUNKSIYALARI ===
def init_db():
    conn = sqlite3.connect("hr_bot.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS applicants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER,
            full_name TEXT,
            age TEXT,
            profession TEXT,
            phone TEXT,
            photo_path TEXT,
            cv_path TEXT,
            status TEXT DEFAULT 'Ko‘rib chiqilmoqda'
        )
    ''')
    conn.commit()
    conn.close()

def add_applicant(tg_id, full_name, age, profession, phone, photo_path, cv_path):
    conn = sqlite3.connect('hr_bot.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO applicants (tg_id, full_name, age, profession, phone, photo_path, cv_path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (tg_id, full_name, age, profession, phone, photo_path, cv_path))
    conn.commit()
    conn.close()

def get_all_applicants():
    conn = sqlite3.connect('hr_bot.db')
    c = conn.cursor()
    c.execute('SELECT * FROM applicants ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    return rows

def update_status(applicant_id, new_status):
    conn = sqlite3.connect('hr_bot.db')
    c = conn.cursor()
    c.execute('UPDATE applicants SET status = ? WHERE id = ?', (new_status, applicant_id))
    conn.commit()
    conn.close()

# === YORDAMCHI ===
def save_user_data(user_id, data):
    os.makedirs("data", exist_ok=True)
    file_path = "data/userdata.json"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            all_data = json.load(f)
    else:
        all_data = {}
    all_data[str(user_id)] = data
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=4, ensure_ascii=False)

async def notify_admins(context, data, photo_path=None, cv_path=None):
    text = (
        f"📩 <b>Yangi ariza!</b>\n\n"
        f"👤 <b>Ism:</b> {data['full_name']}\n"
        f"🎂 <b>Yosh:</b> {data['age']}\n"
        f"🛠 <b>Kasb:</b> {data['profession']}\n"
        f"📱 <b>Telefon:</b> {data['phone']}"
    )

    for admin_id in ADMIN_IDS:
        try:
            # Foto yuborishmi
            if photo_path and os.path.exists(photo_path):
                with open(photo_path, "rb") as photo_file:
                    await context.bot.send_photo(
                        chat_id=admin_id,
                        photo=photo_file,
                        caption=text,
                        parse_mode=ParseMode.HTML
                    )
                    print(f"✅ Rasm yuborildi: {photo_path}")
            else:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=text,
                    parse_mode=ParseMode.HTML
                )
                print("ℹ️ Rasm yo‘q, faqat matn yuborildi.")

            # CV yuborish
            if cv_path and os.path.exists(cv_path):
                with open(cv_path, "rb") as cv_file:
                    await context.bot.send_document(
                        chat_id=admin_id,
                        document=cv_file
                    )
                    print(f"✅ CV yuborildi: {cv_path}")
        except BadRequest as e:
            print(f"❌ Telegram xatosi: {e}")
        except Exception as e:
            print(f"❌ Umumiy xatolik: {e}")
# === FOYDALANUVCHI FORMASI ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Salom! Ismingizni kiriting:", reply_markup=ReplyKeyboardRemove())
    return FULL_NAME

async def full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['full_name'] = update.message.text
    await update.message.reply_text("Yoshingizni kiriting:")
    return AGE

async def age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['age'] = update.message.text
    await update.message.reply_text("Kasbingizni kiriting:")
    return PROFESSION

async def profession(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['profession'] = update.message.text
    await update.message.reply_text("Telefon raqamingizni kiriting:")
    return PHONE

async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("Suratingizni yuboring (faqat rasm):")
    return PHOTO

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("❌ Iltimos, faqat rasm yuboring.")
        return PHOTO

    os.makedirs("photos", exist_ok=True)
    photo_file = await update.message.photo[-1].get_file()
    photo_path = f"photos/{update.message.from_user.id}.jpg"
    await photo_file.download_to_drive(photo_path)
    context.user_data['photo_path'] = photo_path

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📎 O‘tkazib yuborish", callback_data="skip_cv")]
    ])
    data = context.user_data
    add_applicant(update.message.from_user.id, data['full_name'], data['age'], data['profession'], data['phone'], data['photo_path'], None)
    save_user_data(update.message.from_user.id, {**data, "cv_path": None})

    await notify_admins(context, data, photo_path=data['photo_path'], cv_path=None)
    await update.message.reply_text("✅ Arizangiz qabul qilindi. Rahmat!")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Jarayon bekor qilindi.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# === ADMIN BUYRUQLARId ===
async def list_applications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Sizda ruxsat yo‘q.")
        return

    apps = get_all_applicants()
    if not apps:
        await update.message.reply_text("📭 Hozircha arizalar yo‘q.")
        return

    for app in apps:
        msg = (
            f"🆔 ID: {app[0]}\n"
            f"👤 Ism: {app[2]}\n"
            f"🎂 Yosh: {app[3]}\n"
            f"🛠 Kasb: {app[4]}\n"
            f"📞 Tel: {app[5]}\n"
            f"📄 Holat: {app[8]}"
        )
        await update.message.reply_text(msg)

async def set_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Sizda ruxsat yo‘q.")
        return

    try:
        args = context.args
        if len(args) < 2:
            raise ValueError("Kam argument")
        applicant_id = int(args[0])
        status = ' '.join(args[1:])
        update_status(applicant_id, status)
        await update.message.reply_text(f"✅ ID {applicant_id} holati yangilandi: {status}")
    except Exception:
        await update.message.reply_text("❌ To‘g‘ri format: /set_status ID YANGI_HOLAT")

# === MAIN ===
def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, full_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age)],
            PROFESSION: [MessageHandler(filters.TEXT & ~filters.COMMAND, profession)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone)],
            PHOTO: [MessageHandler(filters.PHOTO, photo)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("applications", list_applications))
    app.add_handler(CommandHandler("set_status", set_status))

    print("✅ Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()

