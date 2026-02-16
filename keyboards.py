from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard(memorized_days, total_days=30):
    """لوحة المفاتيح الرئيسية مع أيام الشهر"""
    keyboard = []

    # ─── أزرار التصنيفات ───
    keyboard.append([
        InlineKeyboardButton("🤍 الرحمة (1-10)", callback_data="section_0"),
        InlineKeyboardButton("💚 المغفرة (11-20)", callback_data="section_10"),
        InlineKeyboardButton("💛 العتق (21-30)", callback_data="section_20"),
    ])

    # ─── أزرار الأيام (3 في كل صف) ───
    for i in range(0, total_days, 3):
        row = []
        for j in range(3):
            day_idx = i + j
            if day_idx >= total_days:
                break
            is_memorized = day_idx in memorized_days
            emoji = "✅" if is_memorized else "📜"
            row.append(
                InlineKeyboardButton(
                    f"{emoji} اليوم {day_idx + 1}",
                    callback_data=f"day_{day_idx}"
                )
            )
        keyboard.append(row)

    # ─── أزرار الإجراءات ───
    keyboard.append([
        InlineKeyboardButton("📖 المراجعة", callback_data="review"),
        InlineKeyboardButton("📝 اختبار شامل", callback_data="test_all"),
    ])
    keyboard.append([
        InlineKeyboardButton("📊 إحصائياتي", callback_data="stats"),
        InlineKeyboardButton("🏆 إنجازاتي", callback_data="achievements"),
    ])
    keyboard.append([
        InlineKeyboardButton("⚙️ الإعدادات", callback_data="settings"),
    ])

    return InlineKeyboardMarkup(keyboard)


def section_keyboard(start_day, memorized_days):
    """لوحة مفاتيح قسم معين (10 أيام)"""
    keyboard = []
    end_day = min(start_day + 10, 30)

    for i in range(start_day, end_day, 3):
        row = []
        for j in range(3):
            day_idx = i + j
            if day_idx >= end_day:
                break
            is_memorized = day_idx in memorized_days
            emoji = "✅" if is_memorized else "📜"
            row.append(
                InlineKeyboardButton(
                    f"{emoji} اليوم {day_idx + 1}",
                    callback_data=f"day_{day_idx}"
                )
            )
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_to_days")])
    return InlineKeyboardMarkup(keyboard)


def day_content_keyboard(day_index, is_memorized, challenge_completed=False):
    """لوحة مفاتيح محتوى اليوم"""
    keyboard = []

    # أزرار المحتوى
    keyboard.append([
        InlineKeyboardButton("🔮 الكلمة النورانية", callback_data=f"word_{day_index}"),
        InlineKeyboardButton("💡 الشرح", callback_data=f"explain_{day_index}"),
    ])
    keyboard.append([
        InlineKeyboardButton("🤲 دعاء اليوم", callback_data=f"dua_{day_index}"),
        InlineKeyboardButton("📿 حديث اليوم", callback_data=f"hadith_{day_index}"),
    ])
    keyboard.append([
        InlineKeyboardButton("💡 فائدة فقهية", callback_data=f"tip_{day_index}"),
        InlineKeyboardButton(
            f"{'✅' if challenge_completed else '💪'} تحدي اليوم",
            callback_data=f"challenge_{day_index}"
        ),
    ])

    # زر الحفظ
    if not is_memorized:
        keyboard.append([
            InlineKeyboardButton("✅ تم حفظ الكلمة", callback_data=f"memorize_{day_index}")
        ])

    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_to_days")])
    return InlineKeyboardMarkup(keyboard)


def word_detail_keyboard(day_index):
    """لوحة مفاتيح تفاصيل الكلمة"""
    keyboard = [
        [InlineKeyboardButton("💡 اقرأ الشرح", callback_data=f"explain_{day_index}")],
        [InlineKeyboardButton("🔙 رجوع لليوم", callback_data=f"dayback_{day_index}")],
        [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back_to_days")],
    ]
    return InlineKeyboardMarkup(keyboard)


def back_keyboard(day_index=None):
    """لوحة مفاتيح الرجوع"""
    keyboard = []
    if day_index is not None:
        keyboard.append([InlineKeyboardButton("🔙 رجوع لليوم", callback_data=f"dayback_{day_index}")])
    keyboard.append([InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back_to_days")])
    return InlineKeyboardMarkup(keyboard)


def test_keyboard():
    """لوحة مفاتيح الاختبار"""
    keyboard = [
        [InlineKeyboardButton("➡️ سؤال آخر", callback_data="next_question")],
        [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back_to_days")],
    ]
    return InlineKeyboardMarkup(keyboard)


def challenge_keyboard(day_index, completed=False):
    """لوحة مفاتيح التحدي"""
    keyboard = []
    if not completed:
        keyboard.append([
            InlineKeyboardButton("✅ أتممت التحدي!", callback_data=f"complete_challenge_{day_index}")
        ])
    keyboard.append([InlineKeyboardButton("🔙 رجوع لليوم", callback_data=f"dayback_{day_index}")])
    keyboard.append([InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back_to_days")])
    return InlineKeyboardMarkup(keyboard)


def settings_keyboard(reminder_enabled):
    """لوحة مفاتيح الإعدادات"""
    reminder_text = "🔔 إيقاف التذكير" if reminder_enabled else "🔕 تفعيل التذكير"
    keyboard = [
        [InlineKeyboardButton(reminder_text, callback_data="toggle_reminder")],
        [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back_to_days")],
    ]
    return InlineKeyboardMarkup(keyboard)


def mcq_keyboard(options, day_index):
    """لوحة مفاتيح اختيار من متعدد"""
    keyboard = []
    for i, option in enumerate(options):
        keyboard.append([
            InlineKeyboardButton(
                f"{'🅰' if i == 0 else '🅱' if i == 1 else '🅲' if i == 2 else '🅳'} {option}",
                callback_data=f"mcq_{day_index}_{i}"
            )
        ])
    keyboard.append([InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back_to_days")])
    return InlineKeyboardMarkup(keyboard)
