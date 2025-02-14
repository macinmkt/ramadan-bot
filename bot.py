import os
import random
import sqlite3
import calendar
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler

# 🔴 ضع توكن البوت الخاص بك هنا
TOKEN = os.getenv("TOKEN")

# 🛠️ قاعدة البيانات لحفظ تقدم المستخدمين
conn = sqlite3.connect("ramadan_bot.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        daily_count INTEGER DEFAULT 1,
        selected_day INTEGER,
        saved_words TEXT
    )
""")
conn.commit()
conn.close()

# 📌 الكلمات العلية للحفظ
words_list = ["إخلاص", "تقوى", "عبادة", "صبر", "إحسان", "توبة", "خشوع", "رحمة", "مغفرة", "يقين"]

# 📌 القائمة الرئيسية
async def main_menu(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("📖 برنامج حفظ الكلمات العلية", callback_data="start_saving")],
        [InlineKeyboardButton("📅 ذكرني بكلمات اليوم السابق", callback_data="remind_previous")],
        [InlineKeyboardButton("🔙 الرجوع للبداية", callback_data="restart")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📌 *اختر من القائمة الرئيسية:*", reply_markup=reply_markup, parse_mode="Markdown")

# 📌 اختيار عدد الكلمات اليومية
async def start_saving(update: Update, context: CallbackContext):
    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton("📌 كلمة واحدة", callback_data="count_1"),
         InlineKeyboardButton("📌 كلمتين", callback_data="count_2"),
         InlineKeyboardButton("📌 ثلاث كلمات", callback_data="count_3")],
        [InlineKeyboardButton("🔙 الرجوع للقائمة الرئيسية", callback_data="restart")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text("📝 اختر عدد الكلمات اليومية:", reply_markup=reply_markup)

# 📌 عرض تقويم رمضان لاختيار اليوم بشكل جميل
async def select_day(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    count = int(query.data.split("_")[1])

    # تحديث عدد الكلمات في قاعدة البيانات
    conn = sqlite3.connect("ramadan_bot.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (user_id, daily_count, selected_day, saved_words) VALUES (?, ?, ?, ?)",
                   (user_id, count, None, ""))
    conn.commit()
    conn.close()

    # إعداد تقويم رمضان بشكل مرتب
    keyboard = []
    year = datetime.now().year
    month = 3  # رمضان غالبًا في مارس أو أبريل
    days_in_month = calendar.monthrange(year, month)[1]

    row = []
    for day in range(1, days_in_month + 1):
        row.append(InlineKeyboardButton(f"{day}", callback_data=f"day_{day}"))
        if len(row) == 7:  # كل 7 أيام في صف واحد
            keyboard.append(row)
            row = []
    
    if row:  # إضافة أي أيام متبقية في الصف الأخير
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("🔙 الرجوع للخلف", callback_data="start_saving")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text("📆 *اختر يومًا من رمضان:*", reply_markup=reply_markup, parse_mode="Markdown")

# 📌 عرض الكلمات المختارة للحفظ بعد اختيار اليوم
async def show_words(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    day = int(query.data.split("_")[1])

    # جلب عدد الكلمات المحفوظة للمستخدم
    conn = sqlite3.connect("ramadan_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT daily_count FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    conn.close()

    daily_count = result[0] if result else 1
    selected_words = random.sample(words_list, min(daily_count, len(words_list)))

    # حفظ اليوم والكلمات المختارة
    conn = sqlite3.connect("ramadan_bot.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET selected_day = ?, saved_words = ? WHERE user_id=?", 
                   (day, ",".join(selected_words), user_id))
    conn.commit()
    conn.close()

    keyboard = [
        [InlineKeyboardButton("✅ تم الحفظ", callback_data="saved")],
        [InlineKeyboardButton("🔙 الرجوع للخلف", callback_data="select_day")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(f"📖 *كلمات يوم {day} من رمضان:*\n{', '.join(selected_words)}", reply_markup=reply_markup)

# 📌 تأكيد الحفظ
async def confirm_saved(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.message.edit_text("✅ تم تسجيل حفظك بنجاح!")

# 📌 تذكير بكلمات اليوم السابق
async def remind_previous(update: Update, context: CallbackContext):
    user_id = update.callback_query.from_user.id

    conn = sqlite3.connect("ramadan_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT selected_day, saved_words FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    conn.close()

    if result and result[0] and result[1]:
        previous_day = result[0] - 1
        words = result[1]

        await update.callback_query.message.edit_text(f"🔄 *تذكير بكلمات يوم {previous_day}:*\n{words}")
    else:
        await update.callback_query.message.edit_text("❌ لا يوجد لديك كلمات محفوظة من اليوم السابق.")

# 📌 إعادة تشغيل البوت والعودة للبداية
async def restart(update: Update, context: CallbackContext):
    await main_menu(update, context)

# 📌 إعداد البوت
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", main_menu))
    app.add_handler(CallbackQueryHandler(start_saving, pattern="start_saving"))
    app.add_handler(CallbackQueryHandler(select_day, pattern="count_\\d+"))
    app.add_handler(CallbackQueryHandler(show_words, pattern="day_\\d+"))
    app.add_handler(CallbackQueryHandler(confirm_saved, pattern="saved"))
    app.add_handler(CallbackQueryHandler(remind_previous, pattern="remind_previous"))
    app.add_handler(CallbackQueryHandler(restart, pattern="restart"))
    app.add_handler(CallbackQueryHandler(main_menu, pattern="main_menu"))

    app.run_polling()

if __name__ == "__main__":
    main() 
