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
        [InlineKeyboardButton("🎨 خلفيات رمضان", callback_data="send_background")],
        [InlineKeyboardButton("🏆 نقاطي", callback_data="show_score")],
        [InlineKeyboardButton("🏅 لوحة المتصدرين", callback_data="leaderboard")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📌 *اختر من القائمة الرئيسية:*", reply_markup=reply_markup, parse_mode="Markdown")

# 📌 إرسال خلفية رمضانية
async def send_background(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()  # تأكيد استلام البيانات
    backgrounds = ["background1.jpg", "background2.jpg", "background3.jpg"]
    selected_background = random.choice(backgrounds)
    
    try:
        with open(selected_background, "rb") as photo:
            await query.message.reply_photo(photo=photo, caption="🎨 إليك خلفية رمضانية جميلة!")
    except FileNotFoundError:
        await query.message.reply_text("❌ عذرًا، حدث خطأ في إرسال الخلفية.")

# 📌 معالج للأزرار الأخرى لتجنب تعطلها
async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "start_challenge":
        await query.message.reply_text("🚀 تم بدء التحدي اليومي!")
    elif data == "prayer_times":
        await query.message.reply_text("🕌 مواقيت الصلاة متاحة قريبًا!")
    elif data == "dhikr":
        await query.message.reply_text("📖 أذكار الصباح والمساء قادمة قريبًا!")
    elif data == "show_score":
        await query.message.reply_text("🏆 نقاطك الحالية: 0")  # يمكنك تعديلها وفق قاعدة البيانات
    elif data == "leaderboard":
        await query.message.reply_text("🏅 لوحة المتصدرين ستتوفر قريبًا!")
    else:
        await query.message.reply_text("❌ خيار غير معروف.")

# 📌 إعداد البوت
def main():
    init_db()
    app = Application.builder().token(TOKEN).build()

    # إضافة المعالجات
    app.add_handler(CommandHandler("start", main_menu))
    app.add_handler(CallbackQueryHandler(send_background, pattern="send_background"))  # معالجة زر الخلفيات
    app.add_handler(CallbackQueryHandler(button_handler))  # معالجة الأزرار الأخرى

    app.run_polling()

if __name__ == "__main__":
    main()
