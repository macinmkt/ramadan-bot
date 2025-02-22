from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
import requests
import datetime

# قائمة الاشتراكات
subscribed_users = set()
word_memorization_users = {}

# القائمة الرئيسية
def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("🕌 مواقيت الصلاة", callback_data='prayer_times')],
        [InlineKeyboardButton("📜 اشترك في باقة الفوائد اليومية", callback_data='subscribe_fawaid')],
        [InlineKeyboardButton("🔠 اشترك في برنامج حفظ الكلمات العلية", callback_data='subscribe_words')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("مرحبًا بك! اختر أحد الخيارات من القائمة أدناه:", reply_markup=reply_markup)

# معالجة الاختيارات من القائمة
def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    if query.data == "prayer_times":
        query.message.reply_text("📍 من فضلك، اكتب اسم مدينتك:")
        context.user_data['waiting_for_city'] = True

    elif query.data == "subscribe_fawaid":
        subscribed_users.add(query.message.chat_id)
        keyboard = [[InlineKeyboardButton("↩️ العودة للقائمة الرئيسية", callback_data='back_to_main')]]
        query.message.reply_text("✅ تم الاشتراك في باقة الفوائد اليومية! سيتم إرسال فوائد خلال اليوم.", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "subscribe_words":
        keyboard = [
            [InlineKeyboardButton("كلمة واحدة", callback_data='words_1')],
            [InlineKeyboardButton("كلمتان", callback_data='words_2')],
            [InlineKeyboardButton("↩️ العودة للقائمة الرئيسية", callback_data='back_to_main')]
        ]
        query.message.reply_text("📌 كم عدد الكلمات التي تريد حفظها يوميًا؟", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "back_to_main":
        start(update, context)

    elif query.data in ["words_1", "words_2"]:
        num_words = 1 if query.data == "words_1" else 2
        word_memorization_users[query.message.chat_id] = num_words
        keyboard = [[InlineKeyboardButton("↩️ العودة للقائمة الرئيسية", callback_data='back_to_main')]]
        query.message.reply_text(f"✅ تم الاشتراك في برنامج حفظ الكلمات العلية ({num_words} كلمات يوميًا).", reply_markup=InlineKeyboardMarkup(keyboard))

# استلام اسم المدينة وجلب مواقيت الصلاة
def receive_city(update: Update, context: CallbackContext) -> None:
    if context.user_data.get('waiting_for_city'):
        city = update.message.text
        prayer_times = get_prayer_times(city)
        update.message.reply_text(prayer_times)
        context.user_data['waiting_for_city'] = False

# جلب مواقيت الصلاة من API
def get_prayer_times(city):
    try:
        url = f"https://api.aladhan.com/v1/timingsByCity?city={city}&country=SA&method=4"
        response = requests.get(url).json()
        timings = response['data']['timings']
        hijri_date = response['data']['date']['hijri']['date']
        return f"""🕌 مواقيت الصلاة في {city} - 📆 {hijri_date}:
        
        🌅 الفجر: {timings['Fajr']}
        ☀️ الشروق: {timings['Sunrise']}
        🕛 الظهر: {timings['Dhuhr']}
        🌇 العصر: {timings['Asr']}
        🌆 المغرب: {timings['Maghrib']}
        🌙 العشاء: {timings['Isha']}
        """
    except:
        return "❌ لم يتم العثور على المدينة. تأكد من كتابتها بشكل صحيح."

# إرسال فوائد يومية للمشتركين
def send_daily_fawaid(context: CallbackContext):
    message = "📜 فائدة اليوم: الصبر مفتاح الفرج."
    for user in subscribed_users:
        context.bot.send_message(chat_id=user, text=message)

# إرسال الكلمات اليومية للمشتركين
def send_daily_words(context: CallbackContext):
    for user, num_words in word_memorization_users.items():
        words = ["الإخلاص", "التوكل", "الصبر", "العزيمة", "الإحسان"][:num_words]
        message = "🔠 كلمات اليوم لحفظها:\n" + "\n".join(words) + "\n\n✅ اضغط على 'تم الحفظ' بعد الحفظ."
        keyboard = [[InlineKeyboardButton("✅ تم الحفظ", callback_data='word_saved')]]
        context.bot.send_message(chat_id=user, text=message, reply_markup=InlineKeyboardMarkup(keyboard))

# إرسال تذكير أسبوعي يوم الجمعة
def send_weekly_review(context: CallbackContext):
    for user in word_memorization_users.keys():
        context.bot.send_message(chat_id=user, text="📌 تذكير بالكلمات المحفوظة هذا الأسبوع! راجعها جيدًا. ✅")

def main():
    TOKEN = "YOUR_BOT_TOKEN"  # ضع التوكن الخاص بك هنا
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # الأوامر الأساسية
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, receive_city))

    # جدولة الإرسال اليومي
    job_queue = updater.job_queue
    job_queue.run_daily(send_daily_fawaid, time=datetime.time(hour=9, minute=0))  # كل يوم الساعة 9 صباحًا
    job_queue.run_daily(send_daily_words, time=datetime.time(hour=15, minute=0))  # كل يوم العصر
    job_queue.run_daily(send_weekly_review, time=datetime.time(hour=14, minute=0, day=4))  # كل يوم جمعة

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
