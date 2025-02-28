import os
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext,
    ConversationHandler,
    MessageHandler,
    filters,
)

# جلب توكن البوت من المتغيرات البيئية
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("No TOKEN provided. Please set the TOKEN environment variable.")

# حالات المحادثة
PERIOD_SELECTION, DAY_SELECTION, MEMORIZE, TEST = range(4)

# قوائم الكلمات لكل فترة
WORDS_FIRST_TEN = [
    "الصبر مفتاح الفرج", "الصوم جنة", "القرآن هدى", "الصدقة تطفئ الغضب", "الصلاة نور",
    "الذكر راحة", "التوبة مغفرة", "الدعاء عبادة", "الإخلاص سر النجاح", "رمضان فرصة",
]

WORDS_MIDDLE_TEN = [
    "التقوى زاد", "الصمت حكمة", "القلب مرآة", "الجار حق", "الأمل قوة",
    "الرضا كنز", "العمل صلاح", "الشكر نعمة", "العدل أساس", "التوكل يقين",
]

WORDS_LAST_TEN = [
    "ليلة القدر خير", "العتق من النار", "الاجتهاد فضيلة", "التهجد قربة", "الاستغفار مفتاح",
    "القيام بركة", "الإنفاق ثواب", "الخشوع راحة", "العيد فرحة", "رمضان وداع",
]

# حفظ بيانات المستخدم
user_data = {}

# القائمة الرئيسية
async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {"memorized_words": [], "points": 0}

    welcome_message = "🌙 *مسابقة حفظ الكلمات العلية* 🌙\n\nاختر فترة من رمضان:"

    keyboard = [
        [InlineKeyboardButton("العشر الأوائل من رمضان", callback_data="first_ten")],
        [InlineKeyboardButton("العشر الوسطى من رمضان", callback_data="middle_ten")],
        [InlineKeyboardButton("العشر الأواخر من رمضان", callback_data="last_ten")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode="Markdown")
    return PERIOD_SELECTION

# اختيار اليوم
async def select_period(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id
    period = update.callback_query.data

    if period == "first_ten":
        context.user_data["current_words"] = WORDS_FIRST_TEN
    elif period == "middle_ten":
        context.user_data["current_words"] = WORDS_MIDDLE_TEN
    elif period == "last_ten":
        context.user_data["current_words"] = WORDS_LAST_TEN

    keyboard = []
    words = context.user_data["current_words"]
    for i in range(0, 10, 2):
        row = [
            InlineKeyboardButton(
                f"اليوم {i+1}{' ✅' if words[i] in user_data[user_id]['memorized_words'] else ''}",
                callback_data=f"day_{i}"
            ),
            InlineKeyboardButton(
                f"اليوم {i+2}{' ✅' if words[i+1] in user_data[user_id]['memorized_words'] else ''}",
                callback_data=f"day_{i+1}"
            ) if i + 1 < len(words) else None
        ]
        keyboard.append([btn for btn in row if btn])

    if words[-1] in user_data[user_id]["memorized_words"]:
        keyboard.append([InlineKeyboardButton(f"📝 اختبار {period.replace('_', ' ')}", callback_data="test_period")])
        if period == "last_ten" and len(user_data[user_id]["memorized_words"]) >= 30:
            keyboard.append([InlineKeyboardButton("📚 اختبار شامل", callback_data="test_all")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_to_periods")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        f"🌟 *اختر يومًا من {period.replace('_', ' ')}* 🌟",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return DAY_SELECTION

# عرض الكلمة للحفظ أو المراجعة
async def select_day(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id
    day_index = int(update.callback_query.data.split("_")[1])
    words = context.user_data["current_words"]
    word = words[day_index]

    if word in user_data[user_id]["memorized_words"]:
        keyboard = [
            [InlineKeyboardButton("🔙 رجوع للأيام", callback_data="back_to_days")],
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("✅ تم الحفظ", callback_data=f"memorize_{day_index}")],
            [InlineKeyboardButton("🔙 رجوع للأيام", callback_data="back_to_days")],
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        f"📜 *اليوم {day_index + 1}*\n\n{word}",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return MEMORIZE

# معالجة الحفظ
async def memorize_word(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id
    day_index = int(update.callback_query.data.split("_")[1])
    word = context.user_data["current_words"][day_index]

    if word not in user_data[user_id]["memorized_words"]:
        user_data[user_id]["memorized_words"].append(word)
        user_data[user_id]["points"] += 10

    keyboard = [
        [InlineKeyboardButton("🔙 رجوع للأيام", callback_data="back_to_days")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        f"✅ *تم الحفظ!* نقاطك الآن: {user_data[user_id]['points']}",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return DAY_SELECTION

# اختبار الفترة أو الشامل
async def start_test(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id
    test_type = update.callback_query.data

    if test_type == "test_period":
        words = context.user_data["current_words"]
    elif test_type == "test_all":
        words = WORDS_FIRST_TEN + WORDS_MIDDLE_TEN + WORDS_LAST_TEN

    context.user_data["test_words"] = words.copy()
    context.user_data["current_score"] = 0
    context.user_data["current_question_index"] = 0

    await ask_next_question(update, context)
    return TEST

async def ask_next_question(update: Update, context: CallbackContext):
    words = context.user_data["test_words"]
    index = context.user_data["current_question_index"]

    if index >= 5:  # حد 5 أسئلة
        score = context.user_data["current_score"]
        keyboard = [[InlineKeyboardButton("🔙 رجوع للأيام", callback_data="back_to_days")]]
        await (update.callback_query.edit_message_text if update.callback_query else update.message.reply_text)(
            f"🏆 *انتهى الاختبار!* درجاتك: {score}/5",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        return DAY_SELECTION

    word_phrase = random.choice(words)
    word_parts = word_phrase.split()
    blank_pos = random.randint(0, len(word_parts) - 1)
    correct_answer = word_parts[blank_pos]
    word_parts[blank_pos] = "______"
    question = " ".join(word_parts)

    context.user_data["current_question"] = {"q": question, "a": correct_answer}
    await (update.callback_query.edit_message_text if update.callback_query else update.message.reply_text)(
        f"📝 *املأ الفراغ ({index + 1}/5)*:\n\n{question}",
        parse_mode="Markdown",
    )
    context.user_data["current_question_index"] += 1

async def handle_test_answer(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_answer = update.message.text.strip()
    question = context.user_data["current_question"]

    keyboard = [
        [InlineKeyboardButton("➡️ استمرار", callback_data="continue_test")],
        [InlineKeyboardButton("🔙 رجوع للأيام", callback_data="back_to_days")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if user_answer.lower() == question["a"].lower():
        context.user_data["current_score"] += 1
        result = "✅ *إجابة صحيحة!*"
    else:
        result = f"❌ *إجابة خاطئة!* الإجابة الصحيحة: {question['a']}"

    await update.message.reply_text(result, reply_markup=reply_markup, parse_mode="Markdown")
    return TEST

async def continue_test(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await ask_next_question(update, context)
    return TEST

# الرجوع لاختيار الفترة
async def back_to_periods(update: Update, context: CallbackContext):
    await start(update, context)
    return PERIOD_SELECTION

# الرجوع لاختيار اليوم
async def back_to_days(update: Update, context: CallbackContext):
    period = "first_ten" if context.user_data["current_words"] == WORDS_FIRST_TEN else \
            "middle_ten" if context.user_data["current_words"] == WORDS_MIDDLE_TEN else "last_ten"
    update.callback_query.data = period
    await select_period(update, context)
    return DAY_SELECTION

# إعداد البوت وتشغيله
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PERIOD_SELECTION: [
                CallbackQueryHandler(select_period, pattern="^(first_ten|middle_ten|last_ten)$"),
            ],
            DAY_SELECTION: [
                CallbackQueryHandler(select_day, pattern="^day_"),
                CallbackQueryHandler(start_test, pattern="^(test_period|test_all)$"),
                CallbackQueryHandler(back_to_periods, pattern="^back_to_periods$"),
            ],
            MEMORIZE: [
                CallbackQueryHandler(memorize_word, pattern="^memorize_"),
                CallbackQueryHandler(back_to_days, pattern="^back_to_days$"),
            ],
            TEST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_test_answer),
                CallbackQueryHandler(continue_test, pattern="^continue_test$"),
                CallbackQueryHandler(back_to_days, pattern="^back_to_days$"),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
