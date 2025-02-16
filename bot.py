import os
import random
import sqlite3
import requests
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
        [InlineKeyboardButton("🕌 مواقيت الصلاة", callback_data="prayer_times")],
        [InlineKeyboardButton("📖 أذكار الصباح والمساء", callback_data="dhikr")],
        [InlineKeyboardButton("🏆 نقاطي", callback_data="show_score")],
        [InlineKeyboardButton("🏅 لوحة المتصدرين", callback_data="leaderboard")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📌 *اختر من القائمة الرئيسية:*", reply_markup=reply_markup, parse_mode="Markdown")

# 📌 بدء التحدي اليومي
async def start_challenge(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()  # تأكيد استلام البيانات
    keyboard = [
        [InlineKeyboardButton("سهل 🟢", callback_data="easy_challenge")],
        [InlineKeyboardButton("متوسط 🟡", callback_data="medium_challenge")],
        [InlineKeyboardButton("صعب 🔴", callback_data="hard_challenge")],
        [InlineKeyboardButton("🔙 الرجوع", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text("📌 *اختر مستوى التحدي:*", reply_markup=reply_markup, parse_mode="Markdown")

# 📌 اختيار مستوى التحدي
async def choose_challenge_level(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()  # تأكيد استلام البيانات
    level = query.data

    if level == "easy_challenge":
        words_count, time_limit, points = 3, 5, 10
    elif level == "medium_challenge":
        words_count, time_limit, points = 5, 7, 20
    elif level == "hard_challenge":
        words_count, time_limit, points = 7, 10, 30

    challenge_words = random.sample(WORDS_LIST, words_count)
    challenge_text = "، ".join(challenge_words)
    end_time = (datetime.now() + timedelta(minutes=time_limit)).isoformat()

    with sqlite3.connect("ramadan_bot.db") as conn:
        conn.execute("INSERT OR REPLACE INTO users (user_id, challenge_end_time) VALUES (?, ?)", (query.from_user.id, end_time))

    await query.message.edit_text(
        f"⏳ *تحدي اليوم!*\n\n"
        f"حاول حفظ هذه الكلمات في {time_limit} دقائق:\n"
        f"**{challenge_text}**\n\n"
        f"اضغط على الزر أدناه عند الانتهاء.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ انتهيت من الحفظ", callback_data=f"complete_challenge_{points}")]]),
        parse_mode="Markdown"
    )

# 📌 تأكيد إكمال التحدي
async def complete_challenge(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()  # تأكيد استلام البيانات
    points = int(query.data.split("_")[2])

    with sqlite3.connect("ramadan_bot.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT challenge_end_time FROM users WHERE user_id=?", (query.from_user.id,))
        end_time = cursor.fetchone()[0]

    if datetime.now() <= datetime.fromisoformat(end_time):
        with sqlite3.connect("ramadan_bot.db") as conn:
            conn.execute("UPDATE users SET score = score + ? WHERE user_id=?", (points, query.from_user.id))
        await query.message.edit_text(f"🎉 *أحسنت!* لقد أكملت التحدي بنجاح وربحت {points} نقاط.")
    else:
        await query.message.edit_text("⏰ *انتهى الوقت!* حاول مرة أخرى في التحدي القادم.")

# 📌 عرض النقاط
async def show_score(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()  # تأكيد استلام البيانات

    with sqlite3.connect("ramadan_bot.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT score FROM users WHERE user_id=?", (query.from_user.id,))
        score = cursor.fetchone()[0] or 0

    await query.message.edit_text(f"🏆 *نقاطك الحالية:* {score} نقطة.", parse_mode="Markdown")

# 📌 لوحة المتصدرين
async def leaderboard(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()  # تأكيد استلام البيانات

    with sqlite3.connect("ramadan_bot.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, score FROM users ORDER BY score DESC LIMIT 10")
        top_users = cursor.fetchall()

    leaderboard_text = "🏅 *لوحة المتصدرين:*\n\n"
    for idx, (user_id, score) in enumerate(top_users, start=1):
        leaderboard_text += f"{idx}. User {user_id}: {score} نقطة\n"

    await query.message.edit_text(leaderboard_text, parse_mode="Markdown")

# 📌 مواقيت الصلاة
async def prayer_times(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()  # تأكيد استلام البيانات

    # الحصول على مواقيت الصلاة باستخدام API
    try:
        # استبدل "CITY" و"COUNTRY" بالمدينة والبلد المطلوبة
        url = "http://api.aladhan.com/v1/timingsByCity"
        params = {
            "city": "Cairo",  # يمكن تغييرها إلى المدينة المطلوبة
            "country": "Egypt",  # يمكن تغييرها إلى البلد المطلوب
            "method": 5  # طريقة الحساب (5 للأزهر)
        }
        response = requests.get(url, params=params)
        data = response.json()

        if response.status_code == 200:
            timings = data["data"]["timings"]
            prayer_times_text = (
                f"🕌 *مواقيت الصلاة لليوم:*\n\n"
                f"الفجر: {timings['Fajr']}\n"
                f"الشروق: {timings['Sunrise']}\n"
                f"الظهر: {timings['Dhuhr']}\n"
                f"العصر: {timings['Asr']}\n"
                f"المغرب: {timings['Maghrib']}\n"
                f"العشاء: {timings['Isha']}\n"
            )
            await query.message.edit_text(prayer_times_text, parse_mode="Markdown")
        else:
            await query.message.edit_text("❌ حدث خطأ أثناء جلب مواقيت الصلاة. يرجى المحاولة لاحقًا.")
    except Exception as e:
        await query.message.edit_text(f"❌ حدث خطأ: {str(e)}")

# 📌 أذكار الصباح والمساء
async def dhikr(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()  # تأكيد استلام البيانات
    await query.message.edit_text("📖 *أذكار الصباح والمساء:*\n\nأذكار الصباح: ...\nأذكار المساء: ...", parse_mode="Markdown")

# 📌 إعداد البوت
def main():
    init_db()
    app = Application.builder().token(TOKEN).build()

    # إضافة المعالجات
    app.add_handler(CommandHandler("start", main_menu))
    app.add_handler(CallbackQueryHandler(start_challenge, pattern="start_challenge"))
    app.add_handler(CallbackQueryHandler(choose_challenge_level, pattern="(easy|medium|hard)_challenge"))
    app.add_handler(CallbackQueryHandler(complete_challenge, pattern="complete_challenge_\\d+"))
    app.add_handler(CallbackQueryHandler(show_score, pattern="show_score"))
    app.add_handler(CallbackQueryHandler(leaderboard, pattern="leaderboard"))
    app.add_handler(CallbackQueryHandler(prayer_times, pattern="prayer_times"))
    app.add_handler(CallbackQueryHandler(dhikr, pattern="dhikr"))
    app.add_handler(CallbackQueryHandler(main_menu, pattern="main_menu"))

    app.run_polling()

if __name__ == "__main__":
    main()
