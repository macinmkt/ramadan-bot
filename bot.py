import os
import random
import sqlite3
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler

# 🔴 ضع توكن البوت الخاص بك هنا
TOKEN = os.getenv("TOKEN")

# 🛠️ قاعدة البيانات لحفظ تقدم المستخدمين
def init_db():
    with sqlite3.connect("ramadan_bot.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                score INTEGER DEFAULT 0,
                challenge_end_time TEXT
            )
        """)

# 📌 الكلمات العلية للحفظ
WORDS_LIST = ["إخلاص", "تقوى", "عبادة", "صبر", "إحسان", "توبة", "خشوع", "رحمة", "مغفرة", "يقين"]

# 📌 القائمة الرئيسية
async def main_menu(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("🎯 بدء التحدي اليومي", callback_data="start_challenge")],
        [InlineKeyboardButton("🕌 مواقيت الصلاة", callback_data="prayer_times")],
        [InlineKeyboardButton("📖 أذكار الصباح والمساء", callback_data="dhikr")],
        [InlineKeyboardButton("🎨 خلفيات رمضان", callback_data="send_background")],  # زر جديد
        [InlineKeyboardButton("🏆 نقاطي", callback_data="show_score")],
        [InlineKeyboardButton("🏅 لوحة المتصدرين", callback_data="leaderboard")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📌 *اختر من القائمة الرئيسية:*", reply_markup=reply_markup, parse_mode="Markdown")

# 📌 إرسال خلفية رمضانية
async def send_background(update: Update, context: CallbackContext):
    query = update.callback_query
    # قائمة بخلفيات رمضان
    backgrounds = ["background1.jpg", "background2.jpg", "background3.jpg"]
    selected_background = random.choice(backgrounds)
    
    with open(selected_background, "rb") as photo:
        await query.message.reply_photo(photo=InputFile(photo), caption="🎨 إليك خلفية رمضانية جميلة!")

# 📌 إعداد البوت
def main():
    init_db()
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", main_menu))
    app.add_handler(CallbackQueryHandler(send_background, pattern="send_background"))  # معالج جديد
    # أضف باقي المعالجات هنا...

    app.run_polling()

if __name__ == "__main__":
    main()
