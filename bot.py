import os
import random
import re
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

# دالة لإزالة علامات الترقيم من النصوص
def remove_punctuation(text):
    return re.sub(r'[^\w\s]', '', text)

# دالة لإزالة التشكيل من النصوص
def remove_tashkeel(text):
    tashkeel = (
        '\u064B', '\u064C', '\u064D', '\u064E', '\u064F', '\u0650', '\u0651', '\u0652',
        '\u0653', '\u0654', '\u0655', '\u0656', '\u0657', '\u0658', '\u0659', '\u065A',
        '\u065B', '\u065C', '\u065D', '\u065E', '\u065F', '\u0670'
    )
    for mark in tashkeel:
        text = text.replace(mark, '')
    return text

# دالة لتنظيف الإجابة: إزالة التشكيل، علامات الترقيم والمسافات، وتحويل النص للحروف الصغيرة
def clean_answer(text):
    return remove_tashkeel(remove_punctuation(text)).replace(" ", "").lower()

# جلب توكن البوت من المتغيرات البيئية
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("No TOKEN provided. Please set the TOKEN environment variable.")

# حالات المحادثة
DAY_SELECTION, MEMORIZE, TEST = range(3)

# قائمة الكلمات لـ 30 يومًا (بعد التعديل)
WORDS = [
    "رمضانُ شهٌر مليٌء بالإحسان!",  # اليوم 1
    "راء رَمَضَان: رَحْمَةُ الله للصَّائِمِين، وَالمِيمُ: مَغْفِرَتُهُ لِلمُؤَمِّنِينَ، وَالضَّادُ: ضَمَانُهُ لِجَزَاءِ الصَّائِمِينَ، وَالأَلْفُ: إِحْسَانُهُ للطَائِعين، والنونُ: نُورُه لِلمُحْسِنِينَ",  # اليوم 2
    "رَمَضَانُ شَهْرُ الإحْسَانِ! مَثَلُهُ كَالأمِّ؛ لاَ يَصُدُّ عَنْ أَبْنَائِهَا الْتَّحْنَانَ عُقُوْقٌ وَلاَ افْتِتَانٌ",  # اليوم 3
    "فَصْلُ رَحْمَةِ رَمَضَانَ يَسْتَدْعِيْ تَحْسِيْنَ الإِيْمَانِ",  # اليوم 4
    "شَرْطُ رَحْمَةِ الْمُكَلَّفِيْنَ: الْوَلاءُ! وحُظُوْظُ الْمَرْحُوْمِيْنَ بِقَدْرِ الإسْوَاءِ والْصَّفَاء",  # اليوم 5
    "الْرَّحْمَةُ: صِفَةٌ تَتَعَلَّقُ بِالْقُصُوْرِ، عَلَى وَجْهِ الْجَبْر",  # اليوم 6
    "نُزُوْلُ الْرَّحْمَةِ مُرَتَّبٌ؛ بِإِعْدَادِ الْرَّحْمَنِ لِلْمُقَرَّبِ، وَإِمْدَادِ الْرَّحِيْمِ بِالْمَطْلَبِ",  # اليوم 7
    "الرحمن وصفٌ يتعلق بالإعداد! والرحيم وصف يتعلق بالإمداد",  # اليوم 8
    "الرَّحْمَةُ الرَّبَّانِيَّة: تُوَسَّعُ عَلَى المُسْتَحِقِّيْن بِتَجَلِّيَاتٍ رَحْمَانِيَّة، وَتُرْسَلُ عَلَيهِم بِتَجَلِّيات رَحِيْمِيَّة",  # اليوم 9
    "رمَضُ الرَّحْمَة الرَّبَّانِيَّة يهم بالارتحال! ألا مَن حُرِم الوِصال فليَستدرك الاتصال؛ فإنَّه لا يَقْنَطُ مِن رحْمة الله إلا الضُّلَّال",  # اليوم 10
    "ها قَد حَلَّ المَوْسِمُ الثاني لِرَمَضان، فَلْيُقْبِل بالتوْبة الظالِمُون لأنفُسِهم بالعِصْيان، فَقد تَجَلَّى رَبُّنا مُقْبِلا بالغُفْران",  # اليوم 11
    "ليس خُلُقيا الإعراضُ عن الغفران، ولاسيما في ظروف الإحسان. يا بني! قابِل فتنتك بالاستغفار؛ وإنه لو كان بمثاقيل الحَصَى أزال ذنوبا كالأطوار",  # اليوم 12
    "رَبَّنَا هَبْ لَنَا مِنْ لَدُنْكَ عَفْوًا، وَهَيِّئْ لَنَا مِنْ أَمْرِنَا رَشَدًا",  # اليوم 13
    "فصل مغفرة رمضان يستدعي تحسين الإذعان",  # اليوم 14
    "الْمَغْفِرَةُ صِفَةٌ تَتَعَلَّقُ بِالْعِصْيَانِ عَلَى وَجْهِ الْصَّفح",  # اليوم 15
    "التَّوْبَة صِفَة تَتَعَلَّق بالمُخالَفة عَلَى وَجْه التَّكْفِير! فالتَّوَّاب: هو المُكَفِّر، والتائب: الرَّاجِع بالاستِغفار والتَّجْبِيْر",  # اليوم 16
    "يا بُنَي! اعلَم أن أَقَلّ الاستغفار الإقْرار، وأوسَطه الاسْتِنْصار، وأتمّه الإبْرار! فاسْتَغْفِرْ لِذَنْبِك ولا يَصُدَّنَّك عَنْه كَفَّار",  # اليوم 17
    "أيُّها المؤمنون! لا تُعْرِضُوا عن التوبة لِوَسْوَسَة التَّعَلُّق بالمَعصِية وتِكْرار الخِذْلان؛ فَليس التائب في وَقْته كاذبا على الرَّحمن",  # اليوم 18
    "أوَّلُ دَرْس اختَبرَته البَشَريةُ: آفَّة المَعصِيَة الكوْنِيَّة؛ فتُصِيْب العاصي بآثارها الذَّاتِيَّة، في مَعْزِل عَن حال الأحكام الشرعية",  # اليوم 19
    "شجرة آدم عليه السلام حملت مادَّة يَنْتج عن إصابتها للبَشر حَياة العَناصِر الدنيَوِية، فلما ذاق منها أُصِيب وأصيبَت به في صُلبه الذُّرِّية",  # اليوم 20
    "ها قَد حَلَّ مَوْسِم التَّحْرِيْر، فَلْيُبَادِر بِالتَّحَرُّر مِن رِقِّ الدُّنيا كُلُّ أَسِيْر، فَقَد تَجَلَّى بالعِتْق رَبُّنا القَدِيْر",  # اليوم 21
    "فَصْلُ عِتْقِ رَمَضَانَ يَسْتَدْعِيْ تَحْسِيْنَ الإِتْقَانِ",  # اليوم 22
    "\"العِتْقُ مِن النَّار\" فَيْضٌ يتَعَلَّق بالدَّنَاءَةِ عَلَى وَجْهِ البَرَاءَة",  # اليوم 23
    "الدَّناءة: آثار أَرْضَيَّة تُصِيْب النُّفُوْسَ باقتراف الأسْباب الدُّنْيَوِيَّة، وآثار عُدْوانِيَّة تُصِيبها بانتهاك الحُرُمات الشَّرعِية",  # اليوم 24
    "فَضْلُ لَيْلة القَدْر: بقَدْرها المُبْرَم، ومِيْقاتها المُحْكَم، وحَدَثِها المُعظَّم! أَجْرُ مُوافِقِها مُضَخَّم، والمُعْرِض عنها مُعْدَم",  # اليوم 25
    "لَيْلَةُ الْقَدْرِ نِعْمَةٌ لَا تَنْحَصِرُ بالمُكاشَفِيْن؛ فَخَيْرُهَا يُصِيْبُ كَافَّةَ المُحْيِيْنَ",  # اليوم 26
    "ربَّنا هَبْ لَنَا مِنْ لَدُنْكَ عَفْوًا، وَهَيِّئْ لَنَا مِنْ أَمْرِنَا رَشَدًا",  # اليوم 27
    "الفـائـدةُ التَّـامَّـة من لـيلة القَــدْر معْـقُـودَةٌ بحـفْـظ حُـقـوق اللَّـيالي العَشر!",  # اليوم 28
    "يَرْتَحِلُ رَمَضَانُ بالصَّالحِيْنَ فخُوْرٌ، وفِي الْمُقَصِّرِيْنَ مَقْهُوْرٌ، وَعَلَى الغَافِلِيْنَ شَاهِدٌ وَقُوْرٌ",  # اليوم 29
    "رَبَّنَا أَرْسِلْ لَنَا مِنْ لَدُنْكَ سَعْدًا، وَاحْفَظْ لَنَا فِيْ شُؤُوْنِنَا رُشْدًا",  # اليوم 30
]

# الكلمات المستخدمة مباشرة كاملة
FULL_WORDS = WORDS

# القائمة الرئيسية
async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {"memorized_words": []}

    context.user_data.clear()
    context.user_data["current_words"] = FULL_WORDS
    await show_days(update, context)
    return DAY_SELECTION

async def show_days(update: Update, context: CallbackContext):
    user_id = update.callback_query.from_user.id if update.callback_query else update.message.from_user.id
    words = context.user_data["current_words"]

    keyboard = []
    for i in range(0, 30, 3):
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
        "🌙 *رحلة حفظ الكلمات العلية في شهر رمضان المبارك* 🌙\n\n"
        "✨ انطلق في مغامرة يومية مع كلمات الحكمة والمعرفة في شهر الخير\n"
        "📅 اختر اليوم واحفظ الكلمة ثم اضغط *تم الحفظ* 🌟\n"
        "📖 استمتع بمراجعة كنوزك المحفوظة عبر زر *مراجعة* ✨\n"
        "📝 أو تحدَّ نفسك باختبار شامل من خلال زر *اختبار شامل* 🏆"
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
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_days")],
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("✅ تم الحفظ", callback_data=f"memorize_{day_index}")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_days")],
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

    await update.callback_query.edit_message_text("✅ *تم الحفظ بنجاح!*", parse_mode="Markdown")
    await show_days(update, context)
    return DAY_SELECTION

# مراجعة الكلمات المحفوظة
async def review(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id
    memorized = user_data[user_id]["memorized_words"]

    if not memorized:
        await update.callback_query.edit_message_text(
            "📖 *لم تضف كلمات إلى كنزك بعد!*",
            parse_mode="Markdown"
        )
    else:
        review_text = "📖 *كنوزك المحفوظة:*\n\n" + "\n".join(memorized)
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_days")]]
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
            "📚 *لا كلمات محفوظة لاختبارها بعد!*",
            parse_mode="Markdown"
        )
        return DAY_SELECTION

    context.user_data["test_words"] = memorized  # استخدام الكلمات الكاملة مباشرة
    context.user_data["last_question"] = None
    await ask_next_question(update, context)
    return TEST

async def ask_next_question(update: Update, context: CallbackContext):
    words = context.user_data["test_words"]
    last_question = context.user_data.get("last_question")

    word_phrase = random.choice(words)
    while words and len(words) > 1 and last_question and last_question["q"].split(" ")[0] in word_phrase:
        word_phrase = random.choice(words)

    # نقسم العبارة لاستخلاص الكلمة التي سيتم حذفها منها
    word_parts = word_phrase.split()
    if len(word_parts) < 2:
        question = word_phrase
        raw_answer = word_phrase
    else:
        blank_pos = random.randint(0, len(word_parts) - 1)
        if last_question and len(words) >= 1:
            try:
                last_blank_pos = last_question["q"].split().index("ـــــــ")
            except ValueError:
                last_blank_pos = -1
            while blank_pos == last_blank_pos and len(word_parts) > 1:
                blank_pos = random.randint(0, len(word_parts) - 1)
        raw_answer = word_parts[blank_pos]
        word_parts[blank_pos] = "ـــــــ"
        question = " ".join(word_parts)

    # تنظيف الإجابة لتكون بدون تشكيل، علامات ترقيم ومسافات
    cleaned_answer = clean_answer(raw_answer)
    context.user_data["current_question"] = {"q": question, "a": cleaned_answer}
    context.user_data["last_question"] = {"q": question, "a": cleaned_answer}

    if update.callback_query:
        await update.callback_query.edit_message_text(
            f"📝 *املأ الفراغ:*\n\n{question}",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            f"📝 *املأ الفراغ:*\n\n{question}",
            parse_mode="Markdown",
        )

async def handle_test_answer(update: Update, context: CallbackContext):
    user_answer = update.message.text.strip()
    question = context.user_data["current_question"]

    # مقارنة الإجابة بعد تنظيفها من التشكيل، علامات الترقيم والمسافات
    user_answer_clean = clean_answer(user_answer)
    correct_answer_clean = question["a"]

    keyboard = [
        [InlineKeyboardButton("➡️ سؤال آخر", callback_data="next_question")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_days")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if user_answer_clean == correct_answer_clean:
        result = "✅ *إجابة صحيحة!*\n\n" + f"الإجابة: {correct_answer_clean}"
    else:
        result = f"❌ *إجابة خاطئة!* الإجابة الصحيحة: {correct_answer_clean}"

    await update.message.reply_text(result, reply_markup=reply_markup, parse_mode="Markdown")
    return TEST

async def next_question(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await ask_next_question(update, context)
    return TEST

# الرجوع لاختيار اليوم
async def back_to_days(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await show_days(update, context)
    return DAY_SELECTION

# معالجة الكتابة العشوائية وإعادة المستخدم للقائمة الرئيسية
async def handle_text(update: Update, context: CallbackContext):
    current_state = context.user_data.get("state", DAY_SELECTION)
    if current_state != TEST:
        await show_days(update, context)
        return DAY_SELECTION

# إعداد البوت وتشغيله
def main():
    app = ApplicationBuilder().token(TOKEN).build()

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
                CallbackQueryHandler(next_question, pattern="^next_question$"),
                CallbackQueryHandler(back_to_days, pattern="^back_to_days$"),
            ],
        },
        fallbacks=[
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text),
            CommandHandler("start", start),
        ],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
