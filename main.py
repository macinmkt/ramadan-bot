import os
import re
import random
import logging
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

from database import (
    init_db,
    get_or_create_user,
    update_user_activity,
    memorize_word as db_memorize_word,
    get_memorized_days,
    get_memorized_count,
    get_user_stats,
    get_user_points,
    complete_challenge as db_complete_challenge,
    is_challenge_completed,
    check_and_unlock_achievements,
    get_user_achievements,
    toggle_reminder,
    save_test_result,
    ACHIEVEMENTS,
)
from content import (
    WORDS,
    DAILY_DUAS,
    DAILY_HADITHS,
    DAILY_CHALLENGES,
    DAILY_TIPS,
    WELCOME_MESSAGE,
    CATEGORY_HEADERS,
    CATEGORY_EMOJIS,
    get_day_content,
    get_progress_bar,
)
from keyboards import (
    main_menu_keyboard,
    section_keyboard,
    day_content_keyboard,
    word_detail_keyboard,
    back_keyboard,
    test_keyboard,
    challenge_keyboard,
    settings_keyboard,
    mcq_keyboard,
)

# ─── إعداد التسجيل ───
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─── جلب التوكن ───
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("لم يتم تعيين TOKEN. يرجى تعيين متغير البيئة TOKEN.")

# ─── حالات المحادثة ───
DAY_SELECTION, DAY_VIEW, MEMORIZE, TEST = range(4)


# ─── دوال مساعدة ───

def remove_punctuation(text):
    """إزالة علامات الترقيم"""
    return re.sub(r'[^\w\s]', '', text)


def remove_tashkeel(text):
    """إزالة التشكيل من النصوص العربية"""
    tashkeel = (
        '\u064B', '\u064C', '\u064D', '\u064E', '\u064F', '\u0650', '\u0651', '\u0652',
        '\u0653', '\u0654', '\u0655', '\u0656', '\u0657', '\u0658', '\u0659', '\u065A',
        '\u065B', '\u065C', '\u065D', '\u065E', '\u065F', '\u0670'
    )
    for mark in tashkeel:
        text = text.replace(mark, '')
    return text


def clean_answer(text):
    """تنظيف الإجابة للمقارنة"""
    return remove_tashkeel(remove_punctuation(text)).replace(" ", "").lower()


# ═══════════════════════════════════════════════════════════
#  القائمة الرئيسية
# ═══════════════════════════════════════════════════════════

async def start(update: Update, context: CallbackContext):
    """بدء البوت وعرض القائمة الرئيسية"""
    user = update.message.from_user
    db_user = get_or_create_user(user.id, user.username, user.first_name)
    update_user_activity(user.id)

    context.user_data.clear()
    memorized_days = get_memorized_days(user.id)
    memorized_count = len(memorized_days)

    # شريط التقدم
    progress = get_progress_bar(memorized_count, 30)

    message = WELCOME_MESSAGE + f"\n📈 *تقدمك:* {progress}\n🌟 *النقاط:* {db_user['total_points']}\n📜 *الكلمات المحفوظة:* {memorized_count}/30"

    reply_markup = main_menu_keyboard(memorized_days)
    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")
    return DAY_SELECTION


async def show_days(update: Update, context: CallbackContext):
    """عرض القائمة الرئيسية"""
    user_id = update.callback_query.from_user.id if update.callback_query else update.message.from_user.id
    db_user = get_or_create_user(user_id)
    update_user_activity(user_id)

    memorized_days = get_memorized_days(user_id)
    memorized_count = len(memorized_days)
    progress = get_progress_bar(memorized_count, 30)

    message = WELCOME_MESSAGE + f"\n📈 *تقدمك:* {progress}\n🌟 *النقاط:* {db_user['total_points']}\n📜 *الكلمات المحفوظة:* {memorized_count}/30"

    reply_markup = main_menu_keyboard(memorized_days)

    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
        except Exception:
            await update.callback_query.message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")
    return DAY_SELECTION


# ═══════════════════════════════════════════════════════════
#  عرض الأقسام
# ═══════════════════════════════════════════════════════════

async def show_section(update: Update, context: CallbackContext):
    """عرض قسم معين (رحمة / مغفرة / عتق)"""
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id
    start_day = int(update.callback_query.data.split("_")[1])
    memorized_days = get_memorized_days(user_id)

    if start_day == 0:
        header = CATEGORY_HEADERS["رحمة"]
        desc = "العشر الأوائل من رمضان — أيام الرحمة الإلهية التي يفيض فيها الله على عباده بالرحمة والحنان"
    elif start_day == 10:
        header = CATEGORY_HEADERS["مغفرة"]
        desc = "العشر الأواسط من رمضان — أيام المغفرة التي يغفر فيها الله الذنوب ويصفح عن العباد"
    else:
        header = CATEGORY_HEADERS["عتق"]
        desc = "العشر الأواخر من رمضان — أيام العتق من النار وفيها ليلة القدر المباركة"

    message = f"{header}\n\n{desc}\n\n📅 اختر اليوم:"
    reply_markup = section_keyboard(start_day, memorized_days)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
    return DAY_SELECTION


# ═══════════════════════════════════════════════════════════
#  عرض محتوى اليوم
# ═══════════════════════════════════════════════════════════

async def select_day(update: Update, context: CallbackContext):
    """عرض صفحة اليوم مع جميع الفقرات"""
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id
    day_index = int(update.callback_query.data.split("_")[1])
    context.user_data["current_day"] = day_index

    content = get_day_content(day_index)
    word_data = content["word"]
    memorized_days = get_memorized_days(user_id)
    is_memorized = day_index in memorized_days
    challenge_done = is_challenge_completed(user_id, day_index)
    category_emoji = content["category_emoji"]

    message = (
        f"{'═' * 20}\n"
        f"{category_emoji} *اليوم {day_index + 1} — {word_data['title']}*\n"
        f"{'═' * 20}\n\n"
        f"🔮 *الكلمة النورانية:*\n"
        f"_{word_data['word']}_\n\n"
        f"{'━' * 20}\n"
        f"👇 *اختر ما تريد الاطلاع عليه:*"
    )

    reply_markup = day_content_keyboard(day_index, is_memorized, challenge_done)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
    return DAY_VIEW


async def show_word_detail(update: Update, context: CallbackContext):
    """عرض الكلمة النورانية بالتفصيل"""
    await update.callback_query.answer()
    day_index = int(update.callback_query.data.split("_")[1])
    word_data = WORDS[day_index]
    category_emoji = CATEGORY_EMOJIS.get(word_data["category"], "🌙")

    message = (
        f"{category_emoji} *اليوم {day_index + 1} — {word_data['title']}*\n\n"
        f"{'─' * 25}\n"
        f"🔮 *الكلمة النورانية:*\n\n"
        f"❝ {word_data['word']} ❞\n"
        f"{'─' * 25}"
    )

    reply_markup = word_detail_keyboard(day_index)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
    return DAY_VIEW


async def show_explanation(update: Update, context: CallbackContext):
    """عرض شرح الكلمة"""
    await update.callback_query.answer()
    day_index = int(update.callback_query.data.split("_")[1])
    word_data = WORDS[day_index]

    message = (
        f"💡 *شرح كلمة اليوم {day_index + 1}:*\n\n"
        f"📜 *الكلمة:*\n_{word_data['word']}_\n\n"
        f"{'─' * 25}\n\n"
        f"📖 *الشرح:*\n{word_data['explanation']}"
    )

    reply_markup = back_keyboard(day_index)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
    return DAY_VIEW


async def show_dua(update: Update, context: CallbackContext):
    """عرض دعاء اليوم"""
    await update.callback_query.answer()
    day_index = int(update.callback_query.data.split("_")[1])
    dua = DAILY_DUAS[day_index]

    message = (
        f"🤲 *دعاء اليوم {day_index + 1}:*\n\n"
        f"{'─' * 25}\n\n"
        f"❝ {dua} ❞\n\n"
        f"{'─' * 25}\n\n"
        f"🌙 _اللهم تقبل منا الصيام والقيام والدعاء_"
    )

    reply_markup = back_keyboard(day_index)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
    return DAY_VIEW


async def show_hadith(update: Update, context: CallbackContext):
    """عرض حديث اليوم"""
    await update.callback_query.answer()
    day_index = int(update.callback_query.data.split("_")[1])
    hadith = DAILY_HADITHS[day_index]

    message = (
        f"📿 *حديث اليوم {day_index + 1}:*\n\n"
        f"{'─' * 25}\n\n"
        f"❝ {hadith['text']} ❞\n\n"
        f"📚 *المصدر:* {hadith['source']}\n"
        f"{'─' * 25}"
    )

    reply_markup = back_keyboard(day_index)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
    return DAY_VIEW


async def show_tip(update: Update, context: CallbackContext):
    """عرض الفائدة الفقهية"""
    await update.callback_query.answer()
    day_index = int(update.callback_query.data.split("_")[1])
    tip = DAILY_TIPS[day_index]

    message = (
        f"💡 *فائدة فقهية — اليوم {day_index + 1}:*\n\n"
        f"{'─' * 25}\n\n"
        f"📌 {tip}\n\n"
        f"{'─' * 25}"
    )

    reply_markup = back_keyboard(day_index)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
    return DAY_VIEW


# ═══════════════════════════════════════════════════════════
#  التحديات اليومية
# ═══════════════════════════════════════════════════════════

async def show_challenge(update: Update, context: CallbackContext):
    """عرض تحدي اليوم"""
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id
    day_index = int(update.callback_query.data.split("_")[1])
    challenge = DAILY_CHALLENGES[day_index]
    completed = is_challenge_completed(user_id, day_index)

    status = "✅ *أتممت هذا التحدي!*" if completed else "⏳ *لم يُكتمل بعد*"

    message = (
        f"💪 *تحدي اليوم {day_index + 1}:*\n\n"
        f"{'─' * 25}\n\n"
        f"{challenge['icon']} *{challenge['title']}*\n\n"
        f"📋 {challenge['desc']}\n\n"
        f"{'─' * 25}\n\n"
        f"{status}\n"
        f"🌟 *المكافأة:* +5 نقاط"
    )

    reply_markup = challenge_keyboard(day_index, completed)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
    return DAY_VIEW


async def complete_challenge(update: Update, context: CallbackContext):
    """إكمال التحدي اليومي"""
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id
    day_index = int(update.callback_query.data.split("_")[2])

    db_complete_challenge(user_id, day_index)

    # التحقق من الإنجازات
    new_achievements = check_and_unlock_achievements(user_id)
    achievement_msg = ""
    if new_achievements:
        achievement_msg = "\n\n🎉 *إنجاز جديد!*\n"
        for a in new_achievements:
            achievement_msg += f"{a['title']} — {a['desc']}\n"

    message = (
        f"✅ *أحسنت! تم إكمال التحدي بنجاح!*\n\n"
        f"🌟 +5 نقاط{achievement_msg}"
    )

    keyboard = [
        [InlineKeyboardButton("🔙 رجوع لليوم", callback_data=f"dayback_{day_index}")],
        [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back_to_days")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
    return DAY_VIEW


# ═══════════════════════════════════════════════════════════
#  الحفظ
# ═══════════════════════════════════════════════════════════

async def memorize_word_handler(update: Update, context: CallbackContext):
    """تسجيل حفظ الكلمة"""
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id
    day_index = int(update.callback_query.data.split("_")[1])

    is_new = db_memorize_word(user_id, day_index)

    # التحقق من الإنجازات
    new_achievements = check_and_unlock_achievements(user_id)
    achievement_msg = ""
    if new_achievements:
        achievement_msg = "\n\n🎉 *إنجازات جديدة!*\n"
        for a in new_achievements:
            achievement_msg += f"{a['title']} — {a['desc']}\n"

    memorized_count = get_memorized_count(user_id)
    progress = get_progress_bar(memorized_count, 30)

    if is_new:
        message = (
            f"✅ *تم حفظ كلمة اليوم {day_index + 1} بنجاح!*\n\n"
            f"🌟 +10 نقاط\n"
            f"📈 *تقدمك:* {progress}\n"
            f"📜 *المحفوظ:* {memorized_count}/30{achievement_msg}"
        )
    else:
        message = f"📜 *كلمة اليوم {day_index + 1} محفوظة مسبقاً*\n\n📈 *تقدمك:* {progress}"

    keyboard = [
        [InlineKeyboardButton("🔙 رجوع لليوم", callback_data=f"dayback_{day_index}")],
        [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back_to_days")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
    return DAY_VIEW


async def back_to_day(update: Update, context: CallbackContext):
    """الرجوع لصفحة اليوم"""
    await update.callback_query.answer()
    day_index = int(update.callback_query.data.split("_")[1])
    # إعادة استخدام select_day
    update.callback_query.data = f"day_{day_index}"
    return await select_day(update, context)


# ═══════════════════════════════════════════════════════════
#  المراجعة
# ═══════════════════════════════════════════════════════════

async def review(update: Update, context: CallbackContext):
    """مراجعة الكلمات المحفوظة"""
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id
    memorized_days = get_memorized_days(user_id)

    if not memorized_days:
        message = (
            "📖 *كنوزك المحفوظة*\n\n"
            "{'─' * 25}\n\n"
            "📭 لم تحفظ أي كلمة بعد!\n"
            "ابدأ رحلتك باختيار أي يوم من القائمة 🌟"
        )
    else:
        message = f"📖 *كنوزك المحفوظة ({len(memorized_days)}/30):*\n\n{'─' * 25}\n\n"
        for day_idx in memorized_days:
            word_data = WORDS[day_idx]
            emoji = CATEGORY_EMOJIS.get(word_data["category"], "🌙")
            message += f"{emoji} *اليوم {day_idx + 1}* — {word_data['title']}\n"
            # اختصار الكلمة إذا كانت طويلة
            word_preview = word_data["word"][:80] + "..." if len(word_data["word"]) > 80 else word_data["word"]
            message += f"  _{word_preview}_\n\n"

    keyboard = [[InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back_to_days")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
    return DAY_SELECTION


# ═══════════════════════════════════════════════════════════
#  الإحصائيات
# ═══════════════════════════════════════════════════════════

async def show_stats(update: Update, context: CallbackContext):
    """عرض إحصائيات المستخدم"""
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id
    stats = get_user_stats(user_id)
    progress = get_progress_bar(stats["memorized_count"], 30)

    message = (
        f"📊 *إحصائياتك الرمضانية*\n\n"
        f"{'═' * 25}\n\n"
        f"📈 *التقدم:* {progress}\n\n"
        f"📜 *الكلمات المحفوظة:* {stats['memorized_count']}/30\n"
        f"📝 *الاختبارات المكتملة:* {stats['tests_count']}\n"
        f"🎯 *متوسط الدرجات:* {stats['avg_score']}\n"
        f"💪 *التحديات المكتملة:* {stats['challenges_done']}/30\n"
        f"🏆 *الإنجازات:* {stats['achievements_count']}/{len(ACHIEVEMENTS)}\n\n"
        f"{'═' * 25}\n\n"
        f"🌟 *مجموع النقاط:* {stats['total_points']}"
    )

    keyboard = [[InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back_to_days")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
    return DAY_SELECTION


# ═══════════════════════════════════════════════════════════
#  الإنجازات
# ═══════════════════════════════════════════════════════════

async def show_achievements(update: Update, context: CallbackContext):
    """عرض إنجازات المستخدم"""
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id
    unlocked = get_user_achievements(user_id)

    message = f"🏆 *إنجازاتك ({len(unlocked)}/{len(ACHIEVEMENTS)}):*\n\n{'═' * 25}\n\n"

    for key, achievement in ACHIEVEMENTS.items():
        if key in unlocked:
            message += f"✅ {achievement['title']} — {achievement['desc']}\n"
        else:
            message += f"🔒 ??? — ???\n"

    keyboard = [[InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back_to_days")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
    return DAY_SELECTION


# ═══════════════════════════════════════════════════════════
#  الإعدادات
# ═══════════════════════════════════════════════════════════

async def show_settings(update: Update, context: CallbackContext):
    """عرض الإعدادات"""
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id
    db_user = get_or_create_user(user_id)

    reminder_status = "مفعّل 🔔" if db_user["reminder_enabled"] else "متوقف 🔕"

    message = (
        f"⚙️ *الإعدادات*\n\n"
        f"{'═' * 25}\n\n"
        f"🔔 *التذكير اليومي:* {reminder_status}\n"
    )

    reply_markup = settings_keyboard(db_user["reminder_enabled"])
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
    return DAY_SELECTION


async def toggle_reminder_handler(update: Update, context: CallbackContext):
    """تبديل حالة التذكير"""
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id
    db_user = get_or_create_user(user_id)

    new_state = not db_user["reminder_enabled"]
    toggle_reminder(user_id, new_state)

    status = "تم تفعيل التذكير اليومي 🔔" if new_state else "تم إيقاف التذكير اليومي 🔕"
    message = f"✅ *{status}*"

    keyboard = [[InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back_to_days")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
    return DAY_SELECTION


# ═══════════════════════════════════════════════════════════
#  الاختبار الشامل
# ═══════════════════════════════════════════════════════════

async def start_test(update: Update, context: CallbackContext):
    """بدء الاختبار الشامل"""
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id
    memorized_days = get_memorized_days(user_id)

    if not memorized_days:
        message = (
            "📝 *الاختبار الشامل*\n\n"
            "📭 لا توجد كلمات محفوظة لاختبارها!\n"
            "احفظ بعض الكلمات أولاً ثم عد للاختبار 🌟"
        )
        keyboard = [[InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back_to_days")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
        return DAY_SELECTION

    context.user_data["test_words"] = [WORDS[d]["word"] for d in memorized_days]
    context.user_data["test_score"] = 0
    context.user_data["test_total"] = 0
    context.user_data["last_question"] = None
    await ask_next_question(update, context)
    return TEST


async def ask_next_question(update: Update, context: CallbackContext):
    """طرح سؤال جديد في الاختبار"""
    words = context.user_data["test_words"]
    last_question = context.user_data.get("last_question")

    word_phrase = random.choice(words)
    attempts = 0
    while words and len(words) > 1 and last_question and last_question.get("phrase") == word_phrase and attempts < 10:
        word_phrase = random.choice(words)
        attempts += 1

    word_parts = word_phrase.split()
    if len(word_parts) < 2:
        question = word_phrase
        raw_answer = word_phrase
    else:
        blank_pos = random.randint(0, len(word_parts) - 1)
        raw_answer = word_parts[blank_pos]
        word_parts[blank_pos] = "ـــــــ"
        question = " ".join(word_parts)

    cleaned_answer = clean_answer(raw_answer)
    context.user_data["current_question"] = {"q": question, "a": cleaned_answer, "raw": raw_answer}
    context.user_data["last_question"] = {"phrase": word_phrase, "q": question}

    total = context.user_data.get("test_total", 0)
    score = context.user_data.get("test_score", 0)

    message = (
        f"📝 *الاختبار الشامل*\n\n"
        f"🎯 *النتيجة:* {score}/{total}\n\n"
        f"{'─' * 25}\n\n"
        f"*أكمل الفراغ:*\n\n"
        f"❝ {question} ❞\n\n"
        f"{'─' * 25}\n\n"
        f"✏️ اكتب الكلمة الناقصة..."
    )

    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(message, parse_mode="Markdown")
        except Exception:
            await update.callback_query.message.reply_text(message, parse_mode="Markdown")
    else:
        await update.message.reply_text(message, parse_mode="Markdown")


async def handle_test_answer(update: Update, context: CallbackContext):
    """معالجة إجابة الاختبار"""
    user_answer = update.message.text.strip()
    question = context.user_data.get("current_question")

    if not question:
        return await show_days(update, context)

    user_answer_clean = clean_answer(user_answer)
    correct_answer_clean = question["a"]

    context.user_data["test_total"] = context.user_data.get("test_total", 0) + 1
    total = context.user_data["test_total"]
    score = context.user_data.get("test_score", 0)

    if user_answer_clean == correct_answer_clean:
        context.user_data["test_score"] = score + 1
        score += 1
        result = (
            f"✅ *إجابة صحيحة! أحسنت!*\n\n"
            f"🎯 *النتيجة:* {score}/{total}\n"
            f"🌟 +5 نقاط"
        )
    else:
        result = (
            f"❌ *إجابة خاطئة*\n\n"
            f"✏️ *إجابتك:* {user_answer}\n"
            f"✅ *الإجابة الصحيحة:* {question['raw']}\n\n"
            f"🎯 *النتيجة:* {score}/{total}"
        )

    reply_markup = test_keyboard()
    await update.message.reply_text(result, reply_markup=reply_markup, parse_mode="Markdown")

    # حفظ النتيجة
    user_id = update.message.from_user.id
    save_test_result(user_id, total, score, score * 5)
    check_and_unlock_achievements(user_id)

    return TEST


async def next_question(update: Update, context: CallbackContext):
    """الانتقال للسؤال التالي"""
    await update.callback_query.answer()
    await ask_next_question(update, context)
    return TEST


# ═══════════════════════════════════════════════════════════
#  الرجوع والتنقل
# ═══════════════════════════════════════════════════════════

async def back_to_days(update: Update, context: CallbackContext):
    """الرجوع للقائمة الرئيسية"""
    await update.callback_query.answer()
    return await show_days(update, context)


async def handle_text(update: Update, context: CallbackContext):
    """معالجة النصوص العشوائية"""
    return await start(update, context)


# ═══════════════════════════════════════════════════════════
#  إعداد البوت وتشغيله
# ═══════════════════════════════════════════════════════════

def main():
    """الدالة الرئيسية لتشغيل البوت"""
    # تهيئة قاعدة البيانات
    init_db()
    logger.info("تم تهيئة قاعدة البيانات")

    # إنشاء التطبيق
    app = ApplicationBuilder().token(TOKEN).build()

    # إعداد معالج المحادثة
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            DAY_SELECTION: [
                CallbackQueryHandler(select_day, pattern=r"^day_\d+$"),
                CallbackQueryHandler(show_section, pattern=r"^section_\d+$"),
                CallbackQueryHandler(review, pattern=r"^review$"),
                CallbackQueryHandler(start_test, pattern=r"^test_all$"),
                CallbackQueryHandler(show_stats, pattern=r"^stats$"),
                CallbackQueryHandler(show_achievements, pattern=r"^achievements$"),
                CallbackQueryHandler(show_settings, pattern=r"^settings$"),
                CallbackQueryHandler(toggle_reminder_handler, pattern=r"^toggle_reminder$"),
                CallbackQueryHandler(back_to_days, pattern=r"^back_to_days$"),
            ],
            DAY_VIEW: [
                CallbackQueryHandler(show_word_detail, pattern=r"^word_\d+$"),
                CallbackQueryHandler(show_explanation, pattern=r"^explain_\d+$"),
                CallbackQueryHandler(show_dua, pattern=r"^dua_\d+$"),
                CallbackQueryHandler(show_hadith, pattern=r"^hadith_\d+$"),
                CallbackQueryHandler(show_tip, pattern=r"^tip_\d+$"),
                CallbackQueryHandler(show_challenge, pattern=r"^challenge_\d+$"),
                CallbackQueryHandler(complete_challenge, pattern=r"^complete_challenge_\d+$"),
                CallbackQueryHandler(memorize_word_handler, pattern=r"^memorize_\d+$"),
                CallbackQueryHandler(back_to_day, pattern=r"^dayback_\d+$"),
                CallbackQueryHandler(back_to_days, pattern=r"^back_to_days$"),
            ],
            TEST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_test_answer),
                CallbackQueryHandler(next_question, pattern=r"^next_question$"),
                CallbackQueryHandler(back_to_days, pattern=r"^back_to_days$"),
            ],
        },
        fallbacks=[
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text),
            CommandHandler("start", start),
        ],
    )

    app.add_handler(conv_handler)

    logger.info("🌙 بوت شهر رمضان يعمل الآن...")
    app.run_polling()


if __name__ == "__main__":
    main()
