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
MAIN_MENU, SECTION_MENU, WORD_DISPLAY, TEST_SECTION, FINAL_TEST = range(5)

# قائمة الكلمات لكل قسم
WORDS = {
    "القسم الأول": [
        "الكلمة الأولى في القسم الأول",
        "الكلمة الثانية في القسم الأول",
        "الكلمة الثالثة في القسم الأول",
        "الكلمة الرابعة في القسم الأول",
        "الكلمة الخامسة في القسم الأول",
        "الكلمة السادسة في القسم الأول",
        "الكلمة السابعة في القسم الأول",
        "الكلمة الثامنة في القسم الأول",
        "الكلمة التاسعة في القسم الأول",
        "الكلمة العاشرة في القسم الأول",
    ],
    "القسم الثاني": [
        "الكلمة الأولى في القسم الثاني",
        "الكلمة الثانية في القسم الثاني",
        "الكلمة الثالثة في القسم الثاني",
        "الكلمة الرابعة في القسم الثاني",
        "الكلمة الخامسة في القسم الثاني",
        "الكلمة السادسة في القسم الثاني",
        "الكلمة السابعة في القسم الثاني",
        "الكلمة الثامنة في القسم الثاني",
        "الكلمة التاسعة في القسم الثاني",
        "الكلمة العاشرة في القسم الثاني",
    ],
    "القسم الثالث": [
        "الكلمة الأولى في القسم الثالث",
        "الكلمة الثانية في القسم الثالث",
        "الكلمة الثالثة في القسم الثالث",
        "الكلمة الرابعة في القسم الثالث",
        "الكلمة الخامسة في القسم الثالث",
        "الكلمة السادسة في القسم الثالث",
        "الكلمة السابعة في القسم الثالث",
        "الكلمة الثامنة في القسم الثالث",
        "الكلمة التاسعة في القسم الثالث",
        "الكلمة العاشرة في القسم الثالث",
    ],
}

# قائمة الجمل الناقصة لكل قسم
GAP_SENTENCES = {
    "القسم الأول": [
        {"sentence": "هذا النص هو مثال لنص يمكن أن ______ في نفس المساحة.", "answer": "يستبدل"},
        {"sentence": "لقد تم توليد هذا النص من مولد النص العربى، ______.", "answer": "حيث"},
    ],
    "القسم الثاني": [
        {"sentence": "الجملة الناقصة الأولى في القسم الثاني ______.", "answer": "الجواب الأول"},
        {"sentence": "الجملة الناقصة الثانية في القسم الثاني ______.", "answer": "الجواب الثاني"},
    ],
    "القسم الثالث": [
        {"sentence": "الجملة الناقصة الأولى في القسم الثالث ______.", "answer": "الجواب الأول"},
        {"sentence": "الجملة الناقصة الثانية في القسم الثالث ______.", "answer": "الجواب الثاني"},
    ],
}

# حفظ بيانات المستخدم
user_data = {}

# القائمة الرئيسية
async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_data[user_id] = {"memorized_words": [], "points": 0, "sections_completed": []}  # تهيئة بيانات المستخدم

    # زر البدء
    keyboard = [[InlineKeyboardButton("🌟 البدء 🌟", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🌙 *مرحبًا بك في بوت حفظ الكلمات العلية* 🌙\n\n"
        "اضغط على الزر أدناه للبدء:",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return MAIN_MENU

# القائمة الرئيسية
async def main_menu(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id

    # التحقق من إكمال الأقسام الثلاثة
    sections_completed = user_data[user_id].get("sections_completed", [])
    if len(sections_completed) == 3:
        keyboard = [
            [InlineKeyboardButton("📝 الاختبار الشامل", callback_data="final_test")],
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("📖 القسم الأول", callback_data="section_1")],
            [InlineKeyboardButton("📖 القسم الثاني", callback_data="section_2")],
            [InlineKeyboardButton("📖 القسم الثالث", callback_data="section_3")],
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        "🌙 *اختر القسم* 🌙",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return SECTION_MENU

# قائمة الأقسام
async def section_menu(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    section = update.callback_query.data

    # تحديد القسم المختار
    if section == "section_1":
        context.user_data["current_section"] = "القسم الأول"
    elif section == "section_2":
        context.user_data["current_section"] = "القسم الثاني"
    elif section == "section_3":
        context.user_data["current_section"] = "القسم الثالث"
    elif section == "final_test":
        return await final_test(update, context)

    keyboard = [
        [InlineKeyboardButton("📜 عرض الكلمات", callback_data="display_words")],
        [InlineKeyboardButton("📝 اختبار حفظك", callback_data="test_section")],
        [InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="main_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        f"🌙 *{context.user_data['current_section']}* 🌙\n\n"
        "اختر من القائمة أدناه:",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return SECTION_MENU

# عرض الكلمات
async def display_words(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id
    section = context.user_data["current_section"]

    # عرض 10 أرقام للكلمات
    keyboard = []
    for i in range(1, 11):
        keyboard.append([InlineKeyboardButton(f"الكلمة {i}", callback_data=f"word_{i}")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="section_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        f"🌙 *{section}* 🌙\n\n"
        "اختر الكلمة التي تريد عرضها:",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return WORD_DISPLAY

# عرض كلمة محددة
async def show_word(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id
    section = context.user_data["current_section"]
    word_index = int(update.callback_query.data.split("_")[1]) - 1

    word = WORDS[section][word_index]
    keyboard = [
        [InlineKeyboardButton("✅ تم الحفظ", callback_data="memorized")],
        [InlineKeyboardButton("🔄 احتاج مراجعتها", callback_data="need_review")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="display_words")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        f"🌙 *الكلمة {word_index + 1}* 🌙\n\n{word}",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return WORD_DISPLAY

# معالجة اختيار تم الحفظ أو احتاج مراجعتها
async def handle_word_action(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id
    action = update.callback_query.data

    if action == "memorized":
        await update.callback_query.edit_message_text("✅ تم الحفظ بنجاح!")
    elif action == "need_review":
        await update.callback_query.edit_message_text("🔄 سيتم إضافة الكلمة إلى قائمة المراجعة.")

    # العودة إلى القائمة الرئيسية
    return await main_menu(update, context)

# اختبار القسم
async def test_section(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    section = context.user_data["current_section"]

    # اختيار جملة ناقصة عشوائية
    gap_sentence = random.choice(GAP_SENTENCES[section])
    context.user_data["current_gap"] = gap_sentence

    await update.callback_query.edit_message_text(
        f"📝 *اختبار حفظك* 📝\n\n{gap_sentence['sentence']}"
    )
    return TEST_SECTION

# معالجة إجابة المستخدم على الاختبار
async def handle_test_answer(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_answer = update.message.text.strip()
    gap_sentence = context.user_data.get("current_gap")

    if gap_sentence and user_answer.lower() == gap_sentence["answer"].lower():
        user_data[user_id]["points"] += 10
        await update.message.reply_text("✅ إجابة صحيحة! نقاطك الآن: {}".format(user_data[user_id]["points"]))
    else:
        await update.message.reply_text("❌ إجابة خاطئة، حاول مرة أخرى!")

    # العودة إلى القائمة الرئيسية
    return await main_menu(update, context)

# الاختبار الشامل
async def final_test(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id

    # جمع جميع الجمل الناقصة من الأقسام الثلاثة
    all_gaps = []
    for section in GAP_SENTENCES.values():
        all_gaps.extend(section)

    # اختيار 5 جمل عشوائية
    selected_gaps = random.sample(all_gaps, 5)
    context.user_data["final_test_gaps"] = selected_gaps
    context.user_data["final_test_index"] = 0

    await update.callback_query.edit_message_text(
        "📝 *الاختبار الشامل* 📝\n\n"
        "ستتم اختبارك في 5 جمل ناقصة. هيا بنا!"
    )
    return FINAL_TEST

# معالجة إجابات الاختبار الشامل
async def handle_final_test_answer(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_answer = update.message.text.strip()
    gaps = context.user_data["final_test_gaps"]
    index = context.user_data["final_test_index"]

    if user_answer.lower() == gaps[index]["answer"].lower():
        user_data[user_id]["points"] += 10
        await update.message.reply_text("✅ إجابة صحيحة!")
    else:
        await update.message.reply_text("❌ إجابة خاطئة!")

    # الانتقال إلى الجملة التالية
    context.user_data["final_test_index"] += 1
    if context.user_data["final_test_index"] < len(gaps):
        await update.message.reply_text(
            f"📝 الجملة التالية:\n\n{gaps[context.user_data['final_test_index']]['sentence']}"
        )
        return FINAL_TEST
    else:
        # حساب النتيجة النهائية
        total_points = user_data[user_id]["points"]
        if total_points >= 40:
            await update.message.reply_text("🎉 *مبروك! لقد نجحت في الاختبار الشامل!* �", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ لم تحقق النسبة المطلوبة. حاول مرة أخرى!")

        # العودة إلى القائمة الرئيسية
        return await main_menu(update, context)

# إعداد البوت وتشغيله
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(main_menu, pattern="^main_menu$"),
                CallbackQueryHandler(section_menu, pattern="^section_"),
                CallbackQueryHandler(final_test, pattern="^final_test$"),
            ],
            SECTION_MENU: [
                CallbackQueryHandler(display_words, pattern="^display_words$"),
                CallbackQueryHandler(test_section, pattern="^test_section$"),
                CallbackQueryHandler(main_menu, pattern="^main_menu$"),
            ],
            WORD_DISPLAY: [
                CallbackQueryHandler(show_word, pattern="^word_"),
                CallbackQueryHandler(handle_word_action, pattern="^(memorized|need_review)$"),
                CallbackQueryHandler(section_menu, pattern="^section_menu$"),
            ],
            TEST_SECTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_test_answer),
            ],
            FINAL_TEST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_final_test_answer),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
