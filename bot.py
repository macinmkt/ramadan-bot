import os
import random
import sqlite3
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
        [InlineKeyboardButton("🏆 نقاطي", callback_data="show_score")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📌 *اختر من القائمة الرئيسية:*", reply_markup=reply_markup, parse_mode="Markdown")

# 📌 بدء التحدي اليومي
async def start_challenge(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    # اختيار 3 كلمات عشوائية
    challenge_words = random.sample(WORDS_LIST, 3)
    challenge_text = "، ".join(challenge_words)

    # تعيين وقت انتهاء التحدي (5 دقائق من الآن)
    end_time = (datetime.now() + timedelta(minutes=5)).isoformat()

    with sqlite3.connect("ramadan_bot.db") as conn:
        conn.execute("INSERT OR REPLACE INTO users (user_id, challenge_end_time) VALUES (?, ?)", (user_id, end_time))

    # إرسال التحدي للمستخدم
    await query.message.edit_text(
        f"⏳ *تحدي اليوم!*\n\n"
        f"حاول حفظ هذه الكلمات في 5 دقائق:\n"
        f"**{challenge_text}**\n\n"
        f"اضغط على الزر أدناه عند الانتهاء.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ انتهيت من الحفظ", callback_data="complete_challenge")]]),
        parse_mode="Markdown"
    )

# 📌 تأكيد إكمال التحدي
async def complete_challenge(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    with sqlite3.connect("ramadan_bot.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT challenge_end_time FROM users WHERE user_id=?", (user_id,))
        end_time = cursor.fetchone()[0]

    if datetime.now() <= datetime.fromisoformat(end_time):
        # إذا أكمل التحدي في الوقت المحدد
        with sqlite3.connect("ramadan_bot.db") as conn:
            conn.execute("UPDATE users SET score = score + 10 WHERE user_id=?", (user_id,))
        await query.message.edit_text("🎉 *أحسنت!* لقد أكملت التحدي بنجاح وربحت 10 نقاط.")
    else:
        # إذا تأخر عن الوقت المحدد
        await query.message.edit_text("⏰ *انتهى الوقت!* حاول مرة أخرى في التحدي القادم.")

# 📌 عرض النقاط
async def show_score(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    with sqlite3.connect("ramadan_bot.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT score FROM users WHERE user_id=?", (user_id,))
        score = cursor.fetchone()[0] or 0

    await query.message.edit_text(f"🏆 *نقاطك الحالية:* {score} نقطة.", parse_mode="Markdown")

# 📌 إعداد البوت
def main():
    init_db()
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", main_menu))
    app.add_handler(CallbackQueryHandler(start_challenge, pattern="start_challenge"))
    app.add_handler(CallbackQueryHandler(complete_challenge, pattern="complete_challenge"))
    app.add_handler(CallbackQueryHandler(show_score, pattern="show_score"))

    app.run_polling()

if __name__ == "__main__":
    main()
