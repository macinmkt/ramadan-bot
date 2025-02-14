import os
import random
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler
import asyncio

# 🔴 ضع توكن البوت الخاص بك هنا
TOKEN = os.getenv("TOKEN")

# 📌 قائمة التغريدات الرمضانية المحفوظة
tweets_list = [
    "📜 **راءُ رَمَضَان:** رَحْمَةُ الله للصَّائِمِين، وَالمِيمُ: مَغْفِرَتُهُ لِلمُؤَمِّنِينَ...",
    "🌙 **يا بُنَيَّ!** إن رَمَضان نِعْمَة للمسلِمين؛ يَجِيْء بالرحمة والمغفرة والعِتق...",
    "💡 **فائدة:** الظروف الأرضية تجعل ليلة القدر متحركة، وأما في السموات فثابتة!",
    "📌 **قال ﷺ:** الصيام جُنَّة، فإذا كان يوم صوم أحدكم فلا يرفث ولا يصخب...",
    "🌠 **ليلة القدر خير من ألف شهر، فاجتهد في العشر الأواخر بالصلاة والدعاء**."
]

# 🛠️ تهيئة قاعدة البيانات لحفظ تقدم المستخدمين
conn = sqlite3.connect("ramadan_bot.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        daily_count INTEGER DEFAULT 1,
        saved_tweets TEXT,
        receive_daily BOOLEAN DEFAULT 0
    )
""")
conn.commit()
conn.close()

# 📌 القائمة الرئيسية
async def main_menu(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("📌 اختر عدد التغريدات اليومية", callback_data="set_tweets")],
        [InlineKeyboardButton("📅 أرسل لي كلمة رمضانية يوميًا", callback_data="daily_ramadan")],
        [InlineKeyboardButton("📖 مراجعة التغريدات المحفوظة", callback_data="review_tweets")],
        [InlineKeyboardButton("🎓 الاختبار النهائي", callback_data="final_test")],
        [InlineKeyboardButton("🔙 الرجوع للقائمة الرئيسية", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📌 *اختر من القائمة الرئيسية:*", reply_markup=reply_markup, parse_mode="Markdown")

# 📌 اختيار عدد التغريدات اليومية
async def set_tweets(update: Update, context: CallbackContext):
    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton("📌 1 تغريدة", callback_data="tweets_1"),
         InlineKeyboardButton("📌 5 تغريدات", callback_data="tweets_5"),
         InlineKeyboardButton("📌 10 تغريدات", callback_data="tweets_10")],
        [InlineKeyboardButton("🔙 الرجوع للقائمة الرئيسية", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text("📝 اختر عدد التغريدات اليومية:", reply_markup=reply_markup)

# 📌 حفظ اختيار المستخدم وإرسال التغريدات
async def save_choice(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    daily_count = int(query.data.split("_")[1])

    conn = sqlite3.connect("ramadan_bot.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (user_id, daily_count, saved_tweets, receive_daily) VALUES (?, ?, ?, ?)",
                   (user_id, daily_count, "", 1))
    conn.commit()
    conn.close()

    await query.message.reply_text(f"✅ تم تحديد {daily_count} تغريدة يوميًا لحفظها!")

    # ⬅️ إرسال التغريدات فورًا بعد الاختيار
    await send_tweets(query, context, user_id)

# 📌 إرسال التغريدات اليومية
async def send_tweets(update_or_query, context: CallbackContext, user_id=None):
    if user_id is None:
        user_id = update_or_query.message.from_user.id

    conn = sqlite3.connect("ramadan_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT daily_count FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    conn.close()

    daily_count = result[0] if result else 1  # الافتراضي 1 تغريدة يوميًا
    selected_tweets = random.sample(tweets_list, min(daily_count, len(tweets_list)))
    tweet_text = "\n\n".join(selected_tweets)

    keyboard = [
        [InlineKeyboardButton("✅ تم الحفظ", callback_data="saved")],
        [InlineKeyboardButton("🔙 الرجوع للقائمة الرئيسية", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if isinstance(update_or_query, Update):
        await update_or_query.message.reply_text(f"🌙 **تغريدات اليوم:**\n\n{tweet_text}", reply_markup=reply_markup)
    else:
        await update_or_query.message.edit_text(f"🌙 **تغريدات اليوم:**\n\n{tweet_text}", reply_markup=reply_markup)

# 📌 تذكير يومي بالكلمات الرمضانية
async def daily_ramadan(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    conn = sqlite3.connect("ramadan_bot.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET receive_daily = 1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

    await query.message.reply_text("✅ سيتم إرسال كلمة رمضانية يوميًا لك!")

# 📌 مراجعة التغريدات المحفوظة
async def review_tweets(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    conn = sqlite3.connect("ramadan_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT saved_tweets FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    conn.close()

    if result and result[0]:
        await update.message.reply_text(f"📖 **تغريداتك المحفوظة:**\n{result[0]}")
    else:
        await update.message.reply_text("❌ لا يوجد لديك تغريدات محفوظة بعد. استخدم /tweets_today لحفظ تغريدات جديدة!")

# 📌 الاختبار النهائي
async def final_test(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    conn = sqlite3.connect("ramadan_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT saved_tweets FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    conn.close()

    if result and result[0]:
        await update.message.reply_text("🎓 **الاختبار النهائي:**\nأعد كتابة التغريدات التي حفظتها بدون النظر إليها!")
    else:
        await update.message.reply_text("❌ لا يوجد لديك تغريدات محفوظة بعد!")

# 📌 إعداد البوت
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", main_menu))
    app.add_handler(CallbackQueryHandler(set_tweets, pattern="set_tweets"))
    app.add_handler(CallbackQueryHandler(save_choice, pattern="tweets_\\d+"))
    app.add_handler(CallbackQueryHandler(daily_ramadan, pattern="daily_ramadan"))
    app.add_handler(CallbackQueryHandler(review_tweets, pattern="review_tweets"))
    app.add_handler(CallbackQueryHandler(final_test, pattern="final_test"))
    app.add_handler(CallbackQueryHandler(main_menu, pattern="main_menu"))

    app.run_polling()

if __name__ == "__main__":
    main()
