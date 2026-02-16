import sqlite3
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", "ramadan_bot.db")


def get_connection():
    """إنشاء اتصال بقاعدة البيانات"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """إنشاء جداول قاعدة البيانات"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            join_date TEXT DEFAULT (datetime('now')),
            total_points INTEGER DEFAULT 0,
            streak_days INTEGER DEFAULT 0,
            last_active TEXT,
            reminder_enabled INTEGER DEFAULT 1,
            reminder_time TEXT DEFAULT '08:00'
        );

        CREATE TABLE IF NOT EXISTS memorized_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            day_index INTEGER,
            memorized_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            UNIQUE(user_id, day_index)
        );

        CREATE TABLE IF NOT EXISTS test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            total_questions INTEGER,
            correct_answers INTEGER,
            score INTEGER,
            test_date TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS daily_challenges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            day_index INTEGER,
            completed INTEGER DEFAULT 0,
            completed_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            UNIQUE(user_id, day_index)
        );

        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            achievement_key TEXT,
            unlocked_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            UNIQUE(user_id, achievement_key)
        );
    """)

    conn.commit()
    conn.close()
    logger.info("تم إنشاء قاعدة البيانات بنجاح")


# ─── دوال المستخدمين ───

def get_or_create_user(user_id, username=None, first_name=None):
    """جلب أو إنشاء مستخدم جديد"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute(
            "INSERT INTO users (user_id, username, first_name, last_active) VALUES (?, ?, ?, ?)",
            (user_id, username, first_name, datetime.now().isoformat())
        )
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()

    conn.close()
    return dict(user)


def update_user_activity(user_id):
    """تحديث آخر نشاط للمستخدم"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET last_active = ? WHERE user_id = ?",
        (datetime.now().isoformat(), user_id)
    )
    conn.commit()
    conn.close()


def add_points(user_id, points):
    """إضافة نقاط للمستخدم"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET total_points = total_points + ? WHERE user_id = ?",
        (points, user_id)
    )
    conn.commit()
    conn.close()


def get_user_points(user_id):
    """جلب نقاط المستخدم"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT total_points FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row["total_points"] if row else 0


# ─── دوال الحفظ ───

def memorize_word(user_id, day_index):
    """تسجيل حفظ كلمة"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR IGNORE INTO memorized_words (user_id, day_index) VALUES (?, ?)",
            (user_id, day_index)
        )
        if cursor.rowcount > 0:
            cursor.execute(
                "UPDATE users SET total_points = total_points + 10 WHERE user_id = ?",
                (user_id,)
            )
        conn.commit()
        return cursor.rowcount > 0  # True إذا تم الحفظ لأول مرة
    except Exception as e:
        logger.error(f"خطأ في حفظ الكلمة: {e}")
        return False
    finally:
        conn.close()


def get_memorized_days(user_id):
    """جلب قائمة الأيام المحفوظة"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT day_index FROM memorized_words WHERE user_id = ? ORDER BY day_index",
        (user_id,)
    )
    days = [row["day_index"] for row in cursor.fetchall()]
    conn.close()
    return days


def get_memorized_count(user_id):
    """جلب عدد الكلمات المحفوظة"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) as count FROM memorized_words WHERE user_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return row["count"] if row else 0


# ─── دوال الاختبارات ───

def save_test_result(user_id, total_questions, correct_answers, score):
    """حفظ نتيجة اختبار"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO test_results (user_id, total_questions, correct_answers, score) VALUES (?, ?, ?, ?)",
        (user_id, total_questions, correct_answers, score)
    )
    cursor.execute(
        "UPDATE users SET total_points = total_points + ? WHERE user_id = ?",
        (score, user_id)
    )
    conn.commit()
    conn.close()


def get_user_stats(user_id):
    """جلب إحصائيات المستخدم الشاملة"""
    conn = get_connection()
    cursor = conn.cursor()

    # عدد الكلمات المحفوظة
    cursor.execute(
        "SELECT COUNT(*) as count FROM memorized_words WHERE user_id = ?",
        (user_id,)
    )
    memorized_count = cursor.fetchone()["count"]

    # عدد الاختبارات
    cursor.execute(
        "SELECT COUNT(*) as count, COALESCE(AVG(score), 0) as avg_score FROM test_results WHERE user_id = ?",
        (user_id,)
    )
    test_row = cursor.fetchone()
    tests_count = test_row["count"]
    avg_score = round(test_row["avg_score"], 1)

    # النقاط
    cursor.execute(
        "SELECT total_points FROM users WHERE user_id = ?",
        (user_id,)
    )
    points = cursor.fetchone()["total_points"]

    # التحديات المكتملة
    cursor.execute(
        "SELECT COUNT(*) as count FROM daily_challenges WHERE user_id = ? AND completed = 1",
        (user_id,)
    )
    challenges_done = cursor.fetchone()["count"]

    # الإنجازات
    cursor.execute(
        "SELECT COUNT(*) as count FROM achievements WHERE user_id = ?",
        (user_id,)
    )
    achievements_count = cursor.fetchone()["count"]

    conn.close()

    return {
        "memorized_count": memorized_count,
        "tests_count": tests_count,
        "avg_score": avg_score,
        "total_points": points,
        "challenges_done": challenges_done,
        "achievements_count": achievements_count,
    }


# ─── دوال التحديات ───

def complete_challenge(user_id, day_index):
    """إكمال تحدي يومي"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO daily_challenges (user_id, day_index, completed, completed_at) VALUES (?, ?, 1, ?)",
            (user_id, day_index, datetime.now().isoformat())
        )
        cursor.execute(
            "UPDATE users SET total_points = total_points + 5 WHERE user_id = ?",
            (user_id,)
        )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"خطأ في إكمال التحدي: {e}")
        return False
    finally:
        conn.close()


def is_challenge_completed(user_id, day_index):
    """التحقق من إكمال تحدي"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT completed FROM daily_challenges WHERE user_id = ? AND day_index = ?",
        (user_id, day_index)
    )
    row = cursor.fetchone()
    conn.close()
    return row and row["completed"] == 1


# ─── دوال الإنجازات ───

ACHIEVEMENTS = {
    "first_word": {"title": "🌱 البداية", "desc": "حفظت أول كلمة", "condition": lambda stats: stats["memorized_count"] >= 1},
    "five_words": {"title": "⭐ نجم ساطع", "desc": "حفظت 5 كلمات", "condition": lambda stats: stats["memorized_count"] >= 5},
    "ten_words": {"title": "🌟 متألق", "desc": "حفظت 10 كلمات", "condition": lambda stats: stats["memorized_count"] >= 10},
    "half_way": {"title": "🏅 نصف الطريق", "desc": "حفظت 15 كلمة", "condition": lambda stats: stats["memorized_count"] >= 15},
    "twenty_words": {"title": "💎 ماهر", "desc": "حفظت 20 كلمة", "condition": lambda stats: stats["memorized_count"] >= 20},
    "all_words": {"title": "🏆 حافظ الكنوز", "desc": "حفظت جميع الكلمات الـ 30", "condition": lambda stats: stats["memorized_count"] >= 30},
    "first_test": {"title": "📝 المختبِر", "desc": "أكملت أول اختبار", "condition": lambda stats: stats["tests_count"] >= 1},
    "five_tests": {"title": "🎯 المثابر", "desc": "أكملت 5 اختبارات", "condition": lambda stats: stats["tests_count"] >= 5},
    "first_challenge": {"title": "💪 المتحدي", "desc": "أكملت أول تحدي", "condition": lambda stats: stats["challenges_done"] >= 1},
    "ten_challenges": {"title": "🔥 الملتزم", "desc": "أكملت 10 تحديات", "condition": lambda stats: stats["challenges_done"] >= 10},
    "points_100": {"title": "💰 جامع الحسنات", "desc": "جمعت 100 نقطة", "condition": lambda stats: stats["total_points"] >= 100},
    "points_500": {"title": "👑 سلطان النقاط", "desc": "جمعت 500 نقطة", "condition": lambda stats: stats["total_points"] >= 500},
}


def check_and_unlock_achievements(user_id):
    """التحقق من الإنجازات وفتح الجديدة"""
    stats = get_user_stats(user_id)
    conn = get_connection()
    cursor = conn.cursor()
    new_achievements = []

    for key, achievement in ACHIEVEMENTS.items():
        # تحقق من أن الإنجاز لم يُفتح بعد
        cursor.execute(
            "SELECT id FROM achievements WHERE user_id = ? AND achievement_key = ?",
            (user_id, key)
        )
        if cursor.fetchone():
            continue

        # تحقق من الشرط
        if achievement["condition"](stats):
            cursor.execute(
                "INSERT INTO achievements (user_id, achievement_key) VALUES (?, ?)",
                (user_id, key)
            )
            new_achievements.append(achievement)

    conn.commit()
    conn.close()
    return new_achievements


def get_user_achievements(user_id):
    """جلب إنجازات المستخدم"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT achievement_key FROM achievements WHERE user_id = ?",
        (user_id,)
    )
    unlocked = [row["achievement_key"] for row in cursor.fetchall()]
    conn.close()
    return unlocked


def get_all_users_with_reminders():
    """جلب جميع المستخدمين الذين فعّلوا التذكير"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE reminder_enabled = 1")
    users = [row["user_id"] for row in cursor.fetchall()]
    conn.close()
    return users


def toggle_reminder(user_id, enabled):
    """تفعيل/إيقاف التذكير"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET reminder_enabled = ? WHERE user_id = ?",
        (1 if enabled else 0, user_id)
    )
    conn.commit()
    conn.close()
