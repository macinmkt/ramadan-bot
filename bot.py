import os
import random
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler

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
        saved_tweets TEXT
    )
""")
conn.commit()
conn.close()

# 📌 دالة اختيار عدد التغريدات اليومية
async def set_tweets(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("📌 1 تغريدة", callback_data="1"),
         InlineKeyboardButton("📌 5 تغريدات", callback_data="5"),
         InlineKeyboardButton("📌 10 تغريدات", callback_data="10")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📝 اختر عدد التغريدات اليومية التي ترغب في حفظها:", reply_markup=reply_markup)

async def save_choice(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    daily_count = int(query.data)

    # حفظ عدد التغريدات في قاعدة البيانات
    conn = sqlite3.connect("ramadan_bot.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (user_id, daily_count, saved_tweets) VALUES (?, ?, ?)",
                   (user_id, daily_count, ""))
    conn.commit()
    conn.close()

    await query.message.reply_text(f"✅ تم تحديد {daily_count} تغريدة يوميًا لحفظها!")

    # ⬅️ إرسال التغريدات فورًا بعد الاختيار
    await send_tweets(query, context, user_id)

# 📌 إرسال التغريدات اليومية مباشرة بعد تحديد العدد
async def send_tweets(update_or_query, context: CallbackContext, user_id=None):
    if user_id is None:  # إذا كان الاستدعاء من أمر وليس من الاختيار
        user_id = update_or_query.message.from_user.id

    conn = sqlite3.connect("ramadan_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT daily_count FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        daily_count = result[0]
    else:
        daily_count = 1  # إذا لم يحدد المستخدم عدد التغريدات، يتم تحديد 1 تلقائيًا

    selected_tweets = random.sample(tweets_list, min(daily_count, len(tweets_list)))
    tweet_text = "\n\n".join(selected_tweets)

    keyboard = [[InlineKeyboardButton("✅ تم الحفظ", callback_data="saved")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if isinstance(update_or_query, Update):
        await update_or_query.message.reply_text(f"🌙 **تغريدات اليوم لحفظها:**\n\n{tweet_text}", reply_markup=reply_markup)
    else:  # إذا كان استدعاء من CallbackQuery
        await update_or_query.message.reply_text(f"🌙 **تغريدات اليوم لحفظها:**\n\n{tweet_text}", reply_markup=reply_markup)

async def confirm_saved(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    # حفظ أن المستخدم أكمل الحفظ
    conn = sqlite3.connect("ramadan_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT saved_tweets FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    saved_tweets = result[0] if result else ""

    cursor.execute("UPDATE users SET saved_tweets = ? WHERE user_id=?", (saved_tweets + "\n" + "✅ تم الحفظ", user_id))
    conn.commit()
    conn.close()

    await query.message.reply_text("🎯 أحسنت! تم تسجيل حفظك للتغريدات.")

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

# 📌 إصدار الشهادة الإلكترونية
async def certificate(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    await update.message.reply_text(f"🎉 مبارك! لقد أكملت الحفظ بنجاح.\n🎓 **شهادة حفظ التغريدات الرمضانية** للمستخدم @{update.message.from_user.username}.")

# 🏗️ إعداد البوت
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", set_tweets))
    app.add_handler(CommandHandler("tweets_today", send_tweets))
    app.add_handler(CommandHandler("review", review_tweets))
    app.add_handler(CommandHandler("final_test", final_test))
    app.add_handler(CommandHandler("certificate", certificate))
    app.add_handler(CallbackQueryHandler(save_choice, pattern="^\\d+$"))
    app.add_handler(CallbackQueryHandler(confirm_saved, pattern="saved"))

    app.run_polling()

if __name__ == "__main__":
    main()
