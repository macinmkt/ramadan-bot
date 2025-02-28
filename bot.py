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
DAY_SELECTION, MEMORIZE, TEST = range(3)

# قائمة الكلمات لـ 30 يومًا
WORDS = [
    "الصبر مفتاح الفرج", "الصوم جنة", "القرآن هدى", "الصدقة تطفئ الغضب", "الصلاة نور",
    "الذكر راحة", "التوبة مغفرة", "الدعاء عبادة", "الإخلاص سر النجاح", "رمضان فرصة",
    "التقوى زاد", "الصمت حكمة", "القلب مرآة", "الجار حق", "الأمل قوة",
    "الرضا كنز", "العمل صلاح", "الشكر نعمة", "العدل أساس", "التوكل يقين",
    "ليلة القدر خير", "العتق من النار", "الاجتهاد فضيلة", "التهجد قربة", "الاستغفار مفتاح",
    "القيام بركة", "الإنفاق ثواب", "الخشوع راحة", "العيد فرحة", "رمضان وداع",
]

# حفظ بيانات المستخدم
user_data = {}

# القائمة الرئيسية
async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    # إعادة تهيئة بيانات المستخدم إذا لزم الأمر
    if user_id not in user_data:
        user_data[user_id] = {"memorized_words": []}

    # إعادة تعيين البيانات المؤقتة في context
    context.user_data.clear()  # مسح أي بيانات سابقة
    context.user_data["current_words"] = WORDS
    await show_days(update, context)
    return DAY_SELECTION

async def show_days(update: Update, context: CallbackContext):
    user_id = update.callback_query.from_user.id if update.callback_query else update.message.from_user.id
    words = context.user_data["current_words"]

    keyboard = []
    for i in range(0, 30, 3):  # عرض 3 أيام في كل صف
        row = [
            InlineKeyboardButton(
                f"اليوم {i+1}{' ✅' if words[i] in user_data[user_id]['memorized_words'] else ''}",
                callback_data=f"day_{i}"
            ),
            InlineKeyboardButton(
                f"اليوم {i+2}{' ✅' if words[i+1] in user_data[user_id]['memorized_words'] else ''}",
                callback_data=f"day_{i+1}"
            ) if i + 1 < len(words) else None,
            InlineKeyboardButton(
                f"اليوم {i+3}{' ✅' if words[i+2] in user_data[user_id]['memorized_words'] else ''}",
                callback_data=f"day_{i+2}"
            ) if i + 2 < len(words) else None,
        ]
        keyboard.append([btn for btn in row if btn])

    if user_data[user_id]["memorized_words"]:
        keyboard.append([InlineKeyboardButton("📖 مراجعة", callback_data="review")])
        keyboard.append([InlineKeyboardButton("📚 اختبار شامل", callback_data="test_all")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    message = (
        "🌙 *برنامج حفظ الكلمات العلية في شهر رمضان* 🌙\n\n"
        "حفظ كلمة علية يوميًا من كلمات مولانا الإمام شمس الزمان طارق بن محمد السعدي  \n"
        "قدَّس الله تعالى سرَّه العلي  \n"
        "وبعد اكتمال كل قسم من أقسام رمضان يمكنك خوض الاختبار!\n\n"
        "اختر يومًا:"
    )
    if update.callback_query:
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")
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

    await update.callback_query.edit_message_text("✅ *تم الحفظ!*", parse_mode="Markdown")
    await show_days(update, context)  # عرض قائمة الأيام مباشرة
    return DAY_SELECTION

# مراجعة الكلمات المحفوظة
async def review(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id
    memorized = user_data[user_id]["memorized_words"]

    if not memorized:
        await update.callback_query.edit_message_text(
            "📖 *لا توجد كلمات محفوظة بعد!*",
            parse_mode="Markdown"
        )
    else:
        review_text = "📖 *الكلمات المحفوظة:*\n\n" + "\n".join(memorized)
        keyboard = [[InlineKeyboardButton("🔙 رجوع للأيام", callback_data="back_to_days")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(
            review_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    return DAY_SELECTION

# اختبار شامل
async def start_test(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id
    memorized = user_data[user_id]["memorized_words"]

    if not memorized:
        await update.callback_query.edit_message_text(
            "📚 *لا توجد كلمات محفوظة للاختبار!*",
            parse_mode="Markdown"
        )
        return DAY_SELECTION

    context.user_data["test_words"] = memorized.copy()
    context.user_data["current_score"] = 0
    context.user_data["current_question_index"] = 0

    await ask_next_question(update, context)
    return TEST

async def ask_next_question(update: Update, context: CallbackContext):
    words = context.user_data["test_words"]
    index = context.user_data["current_question_index"]

    if index >= min(5, len(words)):  # حد 5 أسئلة أو عدد الكلمات المحفوظة
        score = context.user_data["current_score"]
        keyboard = [[InlineKeyboardButton("🔙 رجوع للأيام", callback_data="back_to_days")]]
        await (update.callback_query.edit_message_text if hasattr(update, 'callback_query') and update.callback_query else update.message.reply_text)(
            f"🏆 *انتهى الاختبار!* درجاتك: {score}/{min(5, len(words))}",
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
    await (update.callback_query.edit_message_text if hasattr(update, 'callback_query') and update.callback_query else update.message.reply_text)(
        f"📝 *املأ الفراغ ({index + 1}/{min(5, len(words))})*:\n\n{question}",
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
        result = "✅ *إجابة صحيحة! رائع جدًا 🌟*"
    else:
        result = f"❌ *إجابة خاطئة!* الإجابة الصحيحة: {question['a']}"

    await update.message.reply_text(result, reply_markup=reply_markup, parse_mode="Markdown")
    return TEST

async def continue_test(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await ask_next_question(update, context)
    return TEST

# الرجوع لاختيار اليوم
async def back_to_days(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await show_days(update, context)  # عرض قائمة الأيام مباشرة
    return DAY_SELECTION

# معالجة الكتابة العشوائية
async def handle_text(update: Update, context: CallbackContext):
    current_state = context.user_data.get("state", DAY_SELECTION)
    if current_state != TEST:
        await update.message.reply_text("يرجى الاختيار من القائمة!", parse_mode="Markdown")

# إعداد البوت وتشغيله
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # معالج منفصل للأمر /start لضمان إعادة البدء
    app.add_handler(CommandHandler("start", start), group=1)

    # معالج المحادثة
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            DAY_SELECTION: [
                CallbackQueryHandler(select_day, pattern="^day_"),
                CallbackQueryHandler(review, pattern="^review$"),
                CallbackQueryHandler(start_test, pattern="^test_all$"),
                CallbackQueryHandler(back_to_days, pattern="^back_to_days$"),
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
        fallbacks=[
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text),
            CommandHandler("start", start),  # إضافة /start كـ fallback
        ],
    )

    app.add_handler(conv_handler, group=0)
    app.run_polling()

if __name__ == "__main__":
    main()
