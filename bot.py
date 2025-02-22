import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext,
    ConversationHandler,
)
from datetime import time, datetime, timedelta

# جلب توكن البوت من المتغيرات البيئية
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("No TOKEN provided. Please set the TOKEN environment variable.")

# حالات المحادثة
MAIN_MENU, WORD_COUNT, REVIEW_WORDS = range(3)

# قائمة الكلمات
WORDS = [
    "هذا النص هو مثال لنص يمكن أن يستبدل في نفس المساحة، لقد تم توليد هذا النص من مولد النص العربى، حيث",
    "هذا النص هو مثال لنص يمكن أن يستبدل في نفس المساحة، لقد تم توليد هذا النص من مولد النص العربى، حيث",
    "هذا النص هو مثال لنص يمكن أن يستبدل في نفس المساحة، لقد تم توليد هذا النص من مولد النص العربى، حيث",
    "هذا النص هو مثال لنص يمكن أن يستبدل في نفس المساحة، لقد تم توليد هذا النص من مولد النص العربى، حيث",
    "هذا النص هو مثال لنص يمكن أن يستبدل في نفس المساحة، لقد تم توليد هذا النص من مولد النص العربى، حيث",
    "هذا النص هو مثال لنص يمكن أن يستبدل في نفس المساحة، لقد تم توليد هذا النص من مولد النص العربى، حيث",
    "هذا النص هو مثال لنص يمكن أن يستبدل في نفس المساحة، لقد تم توليد هذا النص من مولد النص العربى، حيث",
]

# حفظ الكلمات التي تم إرسالها للمستخدم
user_data = {}

# إرسال كلمة أو كلمتين يوميًا
async def send_daily_words(context: CallbackContext):
    job = context.job
    user_id = job.chat_id
    if user_id in user_data and user_data[user_id]["memorized_words"]:
        words_to_send = user_data[user_id]["memorized_words"][:2]  # إرسال أول كلمتين
        words_text = "\n\n".join(words_to_send)
        await context.bot.send_message(chat_id=user_id, text=f"كلمات اليوم:\n\n{words_text}")

# إرسال تذكير أسبوعي بجميع الكلمات المحفوظة
async def send_weekly_reminder(context: CallbackContext):
    job = context.job
    user_id = job.chat_id
    if user_id in user_data and user_data[user_id]["memorized_words"]:
        words_text = "\n\n".join(user_data[user_id]["memorized_words"])
        await context.bot.send_message(chat_id=user_id, text=f"مراجعة الكلمات المحفوظة:\n\n{words_text}")

# القائمة الرئيسية
async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_data[user_id] = {"memorized_words": []}  # تهيئة بيانات المستخدم

    # جدولة المهام
    context.job_queue.run_daily(
        send_daily_words,
        time=time(hour=15, minute=0),  # الساعة 3 مساءً (يمكن تعديلها)
        chat_id=user_id,
    )
    context.job_queue.run_repeating(
        send_weekly_reminder,
        interval=timedelta(days=7),  # كل أسبوع
        first=datetime.now() + timedelta(days=(6 - datetime.now().weekday())),  # يوم الجمعة القادم
        chat_id=user_id,
    )

    keyboard = [
        [InlineKeyboardButton("اشترك في باقة الفوائد اليومية", callback_data="daily_faidah")],
        [InlineKeyboardButton("اشترك في برنامج حفظ الكلمات العلية", callback_data="memorize_words")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("مرحبًا! اختر من القائمة:", reply_markup=reply_markup)
    return MAIN_MENU

# معالجة اختيار باقة الفوائد اليومية
async def daily_faidah(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    keyboard = [[InlineKeyboardButton("رجوع للقائمة الرئيسية", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        "✅ تم الاشتراك في باقة الفوائد اليومية. سيتم إرسال فوائد خلال اليوم والليلة.",
        reply_markup=reply_markup,
    )
    return MAIN_MENU

# معالجة اختيار برنامج حفظ الكلمات العلية
async def memorize_words(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id

    # إذا كان المستخدم قد حفظ كلمات من قبل، نعرض خيار "مراجعة الكلمات"
    if user_data[user_id]["memorized_words"]:
        keyboard = [
            [InlineKeyboardButton("مراجعة الكلمات", callback_data="review_words")],
            [InlineKeyboardButton("رجوع للقائمة الرئيسية", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(
            "لقد قمت بحفظ كلمات من قبل. اختر مراجعة الكلمات:", reply_markup=reply_markup
        )
        return REVIEW_WORDS
    else:
        # إذا لم يحفظ كلمات من قبل، نعرض خيار "كلمة واحدة" أو "كلمتين"
        keyboard = [
            [InlineKeyboardButton("كلمة واحدة", callback_data="one_word")],
            [InlineKeyboardButton("كلمتين", callback_data="two_words")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(
            "كم عدد الكلمات التي تريد حفظها؟", reply_markup=reply_markup
        )
        return WORD_COUNT

# معالجة اختيار عدد الكلمات
async def word_count(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id
    choice = update.callback_query.data

    if choice == "one_word":
        words_to_send = WORDS[:1]  # إرسال كلمة واحدة
    else:
        words_to_send = WORDS[:2]  # إرسال كلمتين

    # حفظ الكلمات التي تم إرسالها
    user_data[user_id]["memorized_words"].extend(words_to_send)

    # إرسال الكلمات للمستخدم
    words_text = "\n\n".join(words_to_send)
    keyboard = [
        [InlineKeyboardButton("تم الحفظ", callback_data="main_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        f"الكلمات التي تم إرسالها:\n\n{words_text}", reply_markup=reply_markup
    )
    return MAIN_MENU

# معالجة مراجعة الكلمات
async def review_words(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id

    # جلب الكلمات المحفوظة
    memorized_words = user_data[user_id]["memorized_words"]
    if memorized_words:
        words_text = "\n\n".join(memorized_words)
        keyboard = [
            [InlineKeyboardButton("رجوع للقائمة الرئيسية", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(
            f"الكلمات التي قمت بحفظها:\n\n{words_text}", reply_markup=reply_markup
        )
    else:
        await update.callback_query.edit_message_text("لم تقم بحفظ أي كلمات حتى الآن.")

    return MAIN_MENU

# الرجوع للقائمة الرئيسية
async def main_menu(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    keyboard = [
        [InlineKeyboardButton("اشترك في باقة الفوائد اليومية", callback_data="daily_faidah")],
        [InlineKeyboardButton("اشترك في برنامج حفظ الكلمات العلية", callback_data="memorize_words")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("اختر من القائمة:", reply_markup=reply_markup)
    return MAIN_MENU

# إعداد البوت وتشغيله
def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(daily_faidah, pattern="^daily_faidah$"),
                CallbackQueryHandler(memorize_words, pattern="^memorize_words$"),
                CallbackQueryHandler(main_menu, pattern="^main_menu$"),
            ],
            WORD_COUNT: [
                CallbackQueryHandler(word_count, pattern="^one_word$"),
                CallbackQueryHandler(word_count, pattern="^two_words$"),
            ],
            REVIEW_WORDS: [
                CallbackQueryHandler(review_words, pattern="^review_words$"),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
