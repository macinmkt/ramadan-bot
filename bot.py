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

# النص الأساسي الذي يبدأ به كل يوم
BASE_TEXT = "قال مولانا شمس الزمان الإمام طارق بن محمد السعدي قدس الله سره العلي:"

# قائمة الكلمات لـ 30 يومًا (الجزء بعد "العلي:" فقط)
WORDS = [
    "مقدار رحمة البرية بقدر ما في قلوبهم من المحبة الحية",  # اليوم 1
    "العبادةُ مصدرٌ من مصادرِ صحّةِ حياةِ الجنّ والإنس",  # اليوم 2
    "الإيثار خُلق أشاد به الواحد القهّار، وحبيبه المختار، وخلفاؤه الأخيار",  # اليوم 3
    "المُريد يكون إلى شيخه أقرب منه إلى نفسه، فلا يُخفي عنه شاردة ولا واردة",  # اليوم 4
    "إِذَا أَرَدْتَ أَنْ يَكُوْنَ اللهُ تَعَالَى مَعَك! فَاسْتَقِمْ كَمَا أَمَرَك، وَاتَّقِ مَا فَتَنَك",  # اليوم 5
    "لا يزال الله يتجلَّى على البريَّة عمومًا وخصوصًا، من بدايةِ التَّكوينِ إلى أبدِ الآبدِيْن",  # اليوم 6
    "الحياة الدُّنيا فيها مادة جُرثوميَّة! تُميت خَلْق وخُلُق النَّاس، بحسب قَدْرها في نفوسهم",  # اليوم 7
    "كثرة الزّلل؛ تُحدِث الخَلل، وتمنع العمل",  # اليوم 8
    "الفضول من عوائق الوصول",  # اليوم 9
    "بالمَحَبَّة تَتَحَقَّق الحَياة، وبانْعِدامِها تَحْصَل الآفات",  # اليوم 10
    "لا يَزَالُ الْمُتَصَوِّفُ عَلَى الْعَهْدِ فِي الْقُرْبَان حَتَّى يُصَفِّيْهِ الْرَّحْمَن",  # اليوم 11
    "أَصْلُ الإِغْرَاءِ: فِتْنَةُ الْمَرْءِ بِالْشَّهَوَاتِ",  # اليوم 12
    "أَصْلُ الإِغْوَاءِ: فِتْنَةُ الْمَرْءِ بِالْمُفْسِدَاتِ",  # اليوم 13
    "الْمُتَصَوِّفُ: غَرِيْبُ الأَكْوَان؛ لا يَزَالُ يَعْبُرهَا بِإِحْسَانٍ، حَتَّى يُصَفِّيْهِ الرَّحْمَنُ",  # اليوم 14
    "الاخْتِبَارُ دَعْوَةٌ لِتَصْحِيْحِ المَسَارِ بالاعْتِبَار",  # اليوم 15
    "عَدَمُ الاعْتِبَارِ مِنَ الإصْرَارِ وَالاسْتِكْبَار",  # اليوم 16
    "على قَدْرِ حُضور الجنان ينتفع العبد بفيوض الرحمن",  # اليوم 17
    "إنفاق الأموال: سُلّم إلى الواحد المُتعال، فلا تمنوا على الله تعالى ما أعطاكم، ولا تقبضوا اليد فيما اشتراه منكم إذ اشتراكم",  # اليوم 18
    "المَطْلُوْبُ: إِدْرَاكُ مَا لا بُدَّ مِنْهُ فِي الطَّاعَةِ وَالاسْتِقَامَةِ للهِ عَلامِ الغُيُوْبِ",  # اليوم 19
    "يُحْفَظُ الْعِلْمُ بِالْفِكْرِ، وَالاسْتِقَامَةُ بِالْذِّكْرِ، وَالْزِّيَادَةُ بِالْشُّكْرِ",  # اليوم 20
    "الْسَّالِكُ إِلَى عَلَّامِ الغُيُوْبِ: يَعْزِمَ عَلَى حِفْظِ المَطْلُوْبِ، وَمُجَاهَدَةِ الْخُطُوْبِ، وَالاتِّقَاءِ بِالْمَحْبُوْبِ",  # اليوم 21
    "العَاقِلُ الْمُكْرَم: يَبْنِي أَحْكَامَهُ عَلَى الْمُحْكَم؛ ابْتِغَاءَ وَجْهِ رَبِّهِ الأَحْكَمْ",  # اليوم 22
    "المعصية كالثمر؛ تحمل في نفسها الضرر! فإذا تعاطاها العاصي أوقع نفسه في الخطر",  # اليوم 23
    "الرَّحْـمَـة تَـتعلَّق بالشيء إمَّا لِـرَقْعِه أو لِرفْعه",  # اليوم 24
    "دَلِيْلُ قُرْبِكَ مِنَ اللهِ تَعَالَى: تَقُرُّبُكَ وَقُرْبُكَ فِيْ الْعِبَادَة",  # اليوم 25
    "دَلِيْلُ مَحَبَّتِكَ للهِ العَظِيْم: مَحَبَّتُكَ لِعِبَادَتِهِ عَلَى الصِّرَاطِ المُسْتَقِيْم",  # اليوم 26
    "بِقدْر حُضُورِك يَعظُم نُورُك",  # اليوم 27
    "بقدر بُعدك عن المُخالفات وتَقدِيرك للطاعات تَحْضر في العِبَادات",  # اليوم 28
    "على قدرِ الاستِعْداد يكونُ الإمْداد",  # اليوم 29
    "أمان الأحكام بحفظ المقام",  # اليوم 30
]

# دمج النص الأساسي مع الكلمات لعرضها عند اختيار اليوم
FULL_WORDS = [f"{BASE_TEXT} {word}" for word in WORDS]

# حفظ بيانات المستخدم
user_data = {}

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
        "📝 أو تحدَّ نفسك باختبار شامل من خلال زر *اختبار شامل* 🏆"
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
async def memorize
