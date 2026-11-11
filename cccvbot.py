import asyncio
import json
import logging
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from telegram import (
    BotCommand,
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.error import BadRequest
from telegram.request import HTTPXRequest
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Configure logging (silence verbose HTTP request/response logs from httpx)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Environment Configuration
TOKEN = os.getenv("BOT_TOKEN")

# Channel and Social Links
URL_CV_CHANNEL = os.getenv("URL_CV_CHANNEL", "https://t.me/USEACCTCV")
URL_INTERVIEW_TIP = os.getenv("URL_INTERVIEW_TIP", "https://t.me/USEACCITP")
URL_CAREER_TIP = os.getenv("URL_CAREER_TIP", "https://t.me/USEACCCT")
URL_CAREER_CHANNEL = os.getenv("URL_CAREER_CHANNEL", "https://t.me/useacareercenter")
URL_ADMIN = os.getenv("URL_ADMIN", "https://t.me/USEACCAD")
URL_FACEBOOK = os.getenv("URL_FACEBOOK", "https://www.facebook.com/useacareercenter")
URL_TIKTOK = os.getenv("URL_TIKTOK", "https://www.tiktok.com/@useacareercenter")

# Donation Details
DONATE_NAME = os.getenv("DONATE_NAME", "BOUSIVLY KHEV")
DONATE_KHR = os.getenv("DONATE_KHR", "005 920 170")
DONATE_USD = os.getenv("DONATE_USD", "005 920 166")
DONATE_NAME_ALT = os.getenv("DONATE_NAME_ALT", "SOR CHEATAMRIN")
DONATE_KHR_ALT = os.getenv("DONATE_KHR_ALT", "077 893 954")

# Telegram Premium Animated Custom Emoji IDs
EMOJI_CV = os.getenv("EMOJI_CV") or "5836754611305713785"
EMOJI_INTERVIEW = os.getenv("EMOJI_INTERVIEW") or "5213260226194583825"
EMOJI_CAREER = os.getenv("EMOJI_CAREER") or "5839260716132995098"
EMOJI_CHANNEL = os.getenv("EMOJI_CHANNEL") or "5836698068061261980"
EMOJI_ADMIN = os.getenv("EMOJI_ADMIN") or "5981233226629256657"
EMOJI_SUPPORT = os.getenv("EMOJI_SUPPORT") or "5244837092042750681"
EMOJI_FACEBOOK = os.getenv("EMOJI_FACEBOOK") or "5314696663552513826"
EMOJI_TIKTOK = os.getenv("EMOJI_TIKTOK") or "5474131686440584294"
EMOJI_DONATE = os.getenv("EMOJI_DONATE") or "5197434882321567830"
EMOJI_DOC = os.getenv("EMOJI_DOC") or "5431420628978641216"
EMOJI_BULB = os.getenv("EMOJI_BULB") or "5422439311196834318"
EMOJI_LINK = os.getenv("EMOJI_LINK") or "5271604874419647061"
EMOJI_WAVE = os.getenv("EMOJI_WAVE") or "5334863012475986105"
EMOJI_DOWN = os.getenv("EMOJI_DOWN") or "5411322793373477644"
EMOJI_FAQ = os.getenv("EMOJI_FAQ") or "5436113877181941026"

# ──────────────────────────────────────────────────────────────
# FAQ: សំណួរ និង ចម្លើយ អំពី Career និង CV
# ──────────────────────────────────────────────────────────────
FAQ_ITEMS = [
    {
        "title": "📄 ចំនួនទំព័រ CV",
        "q": "តើ CV ល្អគួរមានប៉ុន្មានទំព័រ?",
        "a": (
            "📄 <b>តើ CV ល្អគួរមានប៉ុន្មានទំព័រ?</b>\n\n"
            "• សម្រាប់និស្សិតថ្មី ឬអ្នកមានបទពិសោធន៍តិចជាង ៥ ឆ្នាំ: CV គួរមាន <b>១ ទំព័រ</b> ប៉ុណ្ណោះ។\n"
            "• បើមានបទពិសោធន៍ច្រើនជាង ៥ ឆ្នាំ: អាចមាន <b>២ ទំព័រ</b> ក៏បាន។\n\n"
            "💡 <b>គន្លឹះ:</b> ផ្ដោតលើព័ត៌មានសំខាន់ៗ និងពាក់ព័ន្ធនឹងមុខតំណែងដែលអ្នកដាក់ស្នើ។"
        ),
    },
    {
        "title": "📝 ព័ត៌មានក្នុង CV",
        "q": "តើ CV ត្រូវមានអ្វីខ្លះ?",
        "a": (
            "📝 <b>តើ CV ត្រូវមានអ្វីខ្លះ?</b>\n\n"
            "CV ល្អគួរមាន៖\n"
            "1️⃣ <b>ព័ត៌មានផ្ទាល់ខ្លួន:</b> ឈ្មោះ ទូរស័ព្ទ Email ទីលំនៅ\n"
            "2️⃣ <b>សង្ខេបអំពីខ្លួនឯង:</b> Professional Summary\n"
            "3️⃣ <b>បទពិសោធន៍ការងារ:</b> រៀបរាប់ពីថ្មីទៅចាស់\n"
            "4️⃣ <b>ការអប់រំ:</b> កម្រិតវប្បធម៌ ឬសញ្ញាបត្រ\n"
            "5️⃣ <b>ជំនាញ (Skills):</b> ជំនាញរឹង និងជំនាញទន់\n"
            "6️⃣ <b>សមិទ្ធិផល ឬ ភាសា:</b> ភាសាបរទេស វគ្គខ្លីៗ\n\n"
            "💡 <b>គន្លឹះ:</b> កែសម្រួល CV ឱ្យសមស្របនឹងមុខតំណែងនីមួយៗ។"
        ),
    },
    {
        "title": "✉️ Cover Letter",
        "q": "តើ Cover Letter សំខាន់ទេ?",
        "a": (
            "✉️ <b>តើ Cover Letter សំខាន់ទេ?</b>\n\n"
            "<b>សំខាន់ណាស់!</b> Cover Letter ជួយឱ្យអ្នកជ្រើសរើសស្គាល់អ្នកកាន់តែច្បាស់ "
            "អំពីចំណាប់អារម្មណ៍ និងហេតុផលដែលអ្នកចង់ធ្វើការងារនោះ។\n\n"
            "• បង្ហាញពីចំណុចពិសេសដែល CV មិនអាចបង្ហាញ\n"
            "• បង្ហាញពីការតាំងចិត្ត និងចំណេះដឹងអំពីក្រុមហ៊ុន\n\n"
            "💡 <b>គន្លឹះ:</b> សរសេរ Cover Letter ខុសៗគ្នាសម្រាប់ក្រុមហ៊ុននីមួយៗ កុំប្រើមួយដដែលៗ។"
        ),
    },
    {
        "title": "🎯 ការត្រៀមសម្ភាស",
        "q": "តើត្រូវរៀបចំខ្លួនយ៉ាងម៉េចមុនសម្ភាស?",
        "a": (
            "🎯 <b>តើត្រូវរៀបចំខ្លួនយ៉ាងម៉េចមុនសម្ភាស?</b>\n\n"
            "1️⃣ <b>ស្រាវជ្រាវ:</b> ស្វែងយល់ពីក្រុមហ៊ុន និងមុខតំណែង\n"
            "2️⃣ <b>ត្រៀមចម្លើយ:</b> សម្រាប់សំណួរទូទៅ និងសំណួរបច្ចេកទេស\n"
            "3️⃣ <b>សម្លៀកបំពាក់:</b> ស្លៀកពាក់ឱ្យសមរម្យ មានរបៀបរៀបរយ\n"
            "4️⃣ <b>ឯកសារ:</b> យក CV និងឯកសារពាក់ព័ន្ធមួយច្បាប់បន្ថែម\n"
            "5️⃣ <b>ពេលវេលា:</b> ទៅដល់មុន ១០-១៥ នាទី\n\n"
            "💡 <b>គន្លឹះ:</b> អនុវត្តសម្ភាសន៍សាកល្បងជាមួយមិត្តភ័ក្តិ ដើម្បីបង្កើនទំនុកចិត្ត។"
        ),
    },
    {
        "title": "🗣️ សំណួរសម្ភាស",
        "q": "សំណួរសម្ភាសដែលគេសួរញឹកញាប់?",
        "a": (
            "🗣️ <b>សំណួរសម្ភាសដែលគេសួរញឹកញាប់</b>\n\n"
            "1️⃣ ប្រាប់ខ្ញុំអំពីខ្លួនអ្នក?\n"
            "2️⃣ ហេតុអ្វីបានជាអ្នកចង់ធ្វើការនៅទីនេះ?\n"
            "3️⃣ តើចំណុចខ្លាំង និងចំណុចខ្សោយរបស់អ្នកគឺជាអ្វី?\n"
            "4️⃣ ប្រាប់ខ្ញុំអំពីបញ្ហាដែលអ្នកធ្លាប់ដោះស្រាយ?\n"
            "5️⃣ តើអ្នករំពឹងប្រាក់ខែប៉ុន្មាន?\n\n"
            "💡 <b>គន្លឹះ:</b> រៀបចំចម្លើយដោយប្រើវិធី <b>STAR</b> (Situation, Task, Action, Result)។"
        ),
    },
    {
        "title": "🚫 កំហុសក្នុង CV",
        "q": "តើអ្វីខ្លះដែលមិនគួរដាក់ក្នុង CV?",
        "a": (
            "🚫 <b>តើអ្វីខ្លះដែលមិនគួរដាក់ក្នុង CV?</b>\n\n"
            "❌ រូបថតមិនសមរម្យ (រូប Selfie ឬរូបលេងសើច)\n"
            "❌ ព័ត៌មានផ្ទាល់ខ្លួនដែលមិនចាំបាច់ (ស្ថានភាពគ្រួសារ សាសនា...)\n"
            "❌ ប្រវត្តិការងារដែលមិនទាក់ទងនឹងការងារថ្មី\n"
            "❌ ប្រាក់ខែចាស់ ឬប្រាក់ខែរំពឹងទុក\n"
            "❌ មូលហេតុចាកចេញពីការងារចាស់\n"
            "❌ ព័ត៌មានមិនពិត\n\n"
            "💡 <b>គន្លឹះ:</b> ដាក់តែព័ត៌មានដែលបន្ថែមតម្លៃដល់អ្នក។"
        ),
    },
    {
        "title": "📧 របៀបផ្ញើ CV",
        "q": "តើគួរផ្ញើ CV តាមរបៀបណា?",
        "a": (
            "📧 <b>តើគួរផ្ញើ CV តាមរបៀបណា?</b>\n\n"
            "✅ ផ្ញើតាម <b>Email</b> ជាឯកសារ <b>PDF</b> ជានិច្ច\n"
            "✅ ដាក់ Subject Email ឱ្យច្បាស់:\n"
            "   <i>ឧ. ពាក្យស្នើសុំការងារ - [ឈ្មោះ] - [មុខតំណែង]</i>\n"
            "✅ សរសេរ Cover Message ខ្លីៗ និងគួរសមក្នុង Email Body\n"
            "✅ ពិនិត្យឯកសារភ្ជាប់មុនពេលចុច Send\n\n"
            "💡 <b>គន្លឹះ:</b> កុំផ្ញើជា Word Document ព្រោះទម្រង់អាចខូចនៅលើឧបករណ៍ផ្សេង។"
        ),
    },
    {
        "title": "📩 ក្រោយសម្ភាសន៍",
        "q": "តើគួរធ្វើអ្វីបន្ទាប់ពីសម្ភាស?",
        "a": (
            "📩 <b>តើគួរធ្វើអ្វីបន្ទាប់ពីសម្ភាស?</b>\n\n"
            "1️⃣ ផ្ញើ <b>Thank You Email</b> ក្នុងរយៈពេល ២៤ ម៉ោង\n"
            "2️⃣ សម្ដែងការដឹងគុណចំពោះឱកាសដែលបានសម្ភាស\n"
            "3️⃣ រំលឹកឡើងវិញពីចំណាប់អារម្មណ៍របស់អ្នក\n"
            "4️⃣ រង់ចាំចម្លើយតាមពេលវេលាកំណត់\n\n"
            "💡 <b>គន្លឹះ:</b> បើមិនមានការឆ្លើយតបក្នុងរយៈពេល ១-២ សប្ដាហ៍ អាច Follow up ដោយសុភាពបាន។"
        ),
    },
]

FAQ_PER_PAGE = 4  # 4 questions per page (2x2 grid)


def get_faq_text(page: int = 0) -> str:
    total = len(FAQ_ITEMS)
    total_pages = max(1, (total + FAQ_PER_PAGE - 1) // FAQ_PER_PAGE)
    return (
        f"{tg_emoji(EMOJI_FAQ, '❓')} <b>សំណួរ និង ចម្លើយ (FAQ)</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💬 តើអ្នកមានចម្ងល់ ឬសំណួរអ្វីខ្លះអំពី <b>Career</b> ឬ <b>CV</b>?\n"
        f"សូមចុចលើប៊ូតុងសំណួរខាងក្រោម ដើម្បីមើលចម្លើយ៖\n\n"
        f"📊 <b>ទំព័រ {page + 1} / {total_pages}</b>"
    )


def build_faq_keyboard(page: int = 0) -> InlineKeyboardMarkup:
    """Build a paginated FAQ inline keyboard with a 2-column grid."""
    total = len(FAQ_ITEMS)
    total_pages = max(1, (total + FAQ_PER_PAGE - 1) // FAQ_PER_PAGE)
    page = max(0, min(page, total_pages - 1))

    start_idx = page * FAQ_PER_PAGE
    end_idx = min(start_idx + FAQ_PER_PAGE, total)
    page_items = FAQ_ITEMS[start_idx:end_idx]

    rows = []
    # 2-column buttons for questions
    for i in range(0, len(page_items), 2):
        row = []
        for j, item in enumerate(page_items[i:i + 2]):
            actual_idx = start_idx + i + j
            row.append(InlineKeyboardButton(
                text=item["title"],
                callback_data=f"faq_a_{actual_idx}",
            ))
        rows.append(row)

    # Navigation row: [< មុន] [1 / 2] [> បន្ទាប់]
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("‹ មុន", callback_data=f"faq_p_{page - 1}"))
    else:
        nav_row.append(InlineKeyboardButton(" ", callback_data="faq_noop"))

    nav_row.append(InlineKeyboardButton(f"{page + 1} / {total_pages}", callback_data="faq_noop"))

    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("› បន្ទាប់", callback_data=f"faq_p_{page + 1}"))
    else:
        nav_row.append(InlineKeyboardButton(" ", callback_data="faq_noop"))
    rows.append(nav_row)

    # Refresh row
    rows.append([
        InlineKeyboardButton("🔄 ផ្ទុកឡើងវិញ", callback_data=f"faq_p_{page}")
    ])

    return InlineKeyboardMarkup(rows)


def build_faq_answer_keyboard(idx: int) -> InlineKeyboardMarkup:
    """Build keyboard for single answer view with a Back button."""
    page = idx // FAQ_PER_PAGE
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 ត្រឡប់ក្រោយ", callback_data=f"faq_p_{page}")]
    ])


def tg_emoji(emoji_id: str | None, fallback: str) -> str:
    """Format an animated custom emoji for HTML parse mode, or return fallback."""
    if emoji_id and str(emoji_id).strip():
        return f'<tg-emoji emoji-id="{str(emoji_id).strip()}">{fallback}</tg-emoji>'
    return fallback


def make_reply_btn(text: str, emoji_id: str | None = None, fallback_icon: str = "") -> KeyboardButton:
    """Create a KeyboardButton with custom emoji icon if provided."""
    if emoji_id and str(emoji_id).strip():
        return KeyboardButton(text=text, icon_custom_emoji_id=str(emoji_id).strip())
    label = f"{fallback_icon} {text}".strip() if fallback_icon else text
    return KeyboardButton(label)


def make_inline_btn(text: str, emoji_id: str | None = None, fallback_icon: str = "", **kwargs) -> InlineKeyboardButton:
    """Create an InlineKeyboardButton with custom emoji icon if provided."""
    if emoji_id and str(emoji_id).strip():
        return InlineKeyboardButton(text=text, icon_custom_emoji_id=str(emoji_id).strip(), **kwargs)
    label = f"{fallback_icon} {text}".strip() if fallback_icon else text
    return InlineKeyboardButton(label, **kwargs)


# បង្កើត Reply Keyboard បង្ហាញនៅខាងក្រោមប្រអប់វាយអក្សរ (Under typing)
reply_keyboard = [
    [
        make_reply_btn("CV & Cover Letter", EMOJI_CV, "✉️"),
        make_reply_btn("គន្លឹះក្នុងការសម្ភាស", EMOJI_INTERVIEW, "💁‍♀️"),
    ],
    [
        make_reply_btn("Career Tip", EMOJI_CAREER, "💼"),
        make_reply_btn("FAQ", EMOJI_FAQ, "❓"),
    ],
    [
        make_reply_btn("CareerCenter Channel", EMOJI_CHANNEL, "📢"),
        make_reply_btn("CareerCenter Admin", EMOJI_ADMIN, "🛡️"),
    ],
    [
        make_reply_btn("Support Us", EMOJI_SUPPORT or EMOJI_DONATE, "💝"),
    ],
]

menu = ReplyKeyboardMarkup(
    reply_keyboard,
    resize_keyboard=True,
    is_persistent=True,
    input_field_placeholder="ជ្រើសរើស Menu ឬវាយសារ...",
)

QR_IMAGE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qr_donate.png")

support_inline_keyboard = [
    [
        make_inline_btn(
            "CareerCenter Facebook page",
            emoji_id=EMOJI_FACEBOOK,
            fallback_icon="❤️",
            url=URL_FACEBOOK,
        )
    ],
    [
        make_inline_btn(
            "CareerCenter Tiktok page",
            emoji_id=EMOJI_TIKTOK,
            fallback_icon="🎵",
            url=URL_TIKTOK,
        )
    ],
    [
        make_inline_btn(
            "Donate us",
            emoji_id=EMOJI_DONATE,
            fallback_icon="💸",
            callback_data="donate_us",
        )
    ],
]

# កំណត់ព័ត៌មាន និង Link សម្រាប់ប៊ូតុងនីមួយៗ
BUTTON_ACTIONS = {
    "CV & Cover Letter": {
        "text": f"{tg_emoji(EMOJI_DOC, '📄')} <b>CV & Cover Letter</b>\n\nសូមចុចប៊ូតុងខាងក្រោមដើម្បីចូលទៅកាន់ Channel៖",
        "btn_label": "ចូលទៅកាន់ CV & Cover Letter",
        "btn_emoji": EMOJI_LINK,
        "btn_fallback": "🔗",
        "url": URL_CV_CHANNEL,
    },
    "គន្លឹះក្នុងការសម្ភាស": {
        "text": f"{tg_emoji(EMOJI_BULB, '💡')} <b>គន្លឹះក្នុងការសម្ភាសន៍</b>\n\nសូមចុចប៊ូតុងខាងក្រោមដើម្បីមើលការណែនាំសម្ភាសន៍៖",
        "btn_label": "ចូលទៅកាន់ គន្លឹះក្នុងការសម្ភាស",
        "btn_emoji": EMOJI_LINK,
        "btn_fallback": "🔗",
        "url": URL_INTERVIEW_TIP,
    },
    "Interview Tip": {
        "text": f"{tg_emoji(EMOJI_BULB, '💡')} <b>Interview Tip</b>\n\nសូមចុចប៊ូតុងខាងក្រោមដើម្បីមើលការណែនាំសម្ភាសន៍៖",
        "btn_label": "ចូលទៅកាន់ Interview Tip",
        "btn_emoji": EMOJI_LINK,
        "btn_fallback": "🔗",
        "url": URL_INTERVIEW_TIP,
    },
    "Career Tip": {
        "text": f"{tg_emoji(EMOJI_CAREER, '💼')} <b>Career Tip</b>\n\nសូមចុចប៊ូតុងខាងក្រោមដើម្បីមើលគន្លឹះការងារ៖",
        "btn_label": "ចូលទៅកាន់ Career Tip",
        "btn_emoji": EMOJI_LINK,
        "btn_fallback": "🔗",
        "url": URL_CAREER_TIP,
    },
    "CareerCenter Channel": {
        "text": f"{tg_emoji(EMOJI_CHANNEL, '📢')} <b>Career Center Channel</b>\n\nសូមចុចប៊ូតុងខាងក្រោមដើម្បីមើលChannel៖",
        "btn_label": "ចូលទៅកាន់ Career Center Channel",
        "btn_emoji": EMOJI_LINK,
        "btn_fallback": "🔗",
        "url": URL_CAREER_CHANNEL,
    },
    "CareerCenter Admin": {
        "text": f"{tg_emoji(EMOJI_ADMIN, '🛡️')} <b>CareerCenter Admin</b>\n\nសូមចុចប៊ូតុងខាងក្រោមដើម្បីមើលAdmin៖",
        "btn_label": "ចូលទៅកាន់ CareerCenter Admin",
        "btn_emoji": EMOJI_LINK,
        "btn_fallback": "🔗",
        "url": URL_ADMIN,
    },
    "CC Facebook Page": {
        "text": f"{tg_emoji(EMOJI_FACEBOOK, '❤️')} <b>CC Facebook Page</b>\n\nសូមចុចប៊ូតុងខាងក្រោមដើម្បីចូលទៅកាន់ Facebook Page៖",
        "btn_label": "ចូលទៅកាន់ Facebook Page",
        "btn_emoji": EMOJI_LINK,
        "btn_fallback": "🔗",
        "url": URL_FACEBOOK,
    },
    "FAQ": {
        "is_faq": True,
    },
    "សំណួរ-ចម្លើយ (FAQ)": {
        "is_faq": True,
    },
    "Support Us": {
        "text": (
            f"{tg_emoji(EMOJI_SUPPORT or EMOJI_DONATE, '💝')} <b>Support Us / គាំទ្រពួកយើង</b>\n\n"
            f"សូមជ្រើសរើសជម្រើសខាងក្រោមដើម្បីគាំទ្រ Career Center៖"
        ),
        "inline_keyboard": support_inline_keyboard,
    },
    "Donate to Support Us": {
        "photo": QR_IMAGE_PATH,
        "caption": (
            f"{tg_emoji(EMOJI_DONATE, '💝')} <b>Donate to Support Us</b>\n\n"
            f"👤 <b>ឈ្មោះ៖</b> {DONATE_NAME}\n"
            f"💳 <b>Wallet KHR៖</b> <code>{DONATE_KHR}</code>\n\n"
            f"💳 <b>Wallet USD៖</b> <code>{DONATE_USD}</code>\n\n"
            f"សូមស្កេន KHQR ខាងលើដើម្បីឧបត្ថម្ភគាំទ្រ Career Center! សូមអរគុណច្រើន 🙏"
        ),
    },
    "Donate us": {
        "photo": QR_IMAGE_PATH,
        "caption": (
            f"{tg_emoji(EMOJI_DONATE, '💝')} <b>Donate to Support Us</b>\n\n"
            f"👤 <b>ឈ្មោះ៖</b> {DONATE_NAME}\n"
            f"💳 <b>Wallet KHR៖</b> <code>{DONATE_KHR}</code>\n\n"
            f"💳 <b>Wallet USD៖</b> <code>{DONATE_USD}</code>\n\n"
            f"សូមស្កេន KHQR ខាងលើដើម្បីឧបត្ថម្ភគាំទ្រ Career Center! សូមអរគុណច្រើន 🙏"
        ),
    },
}

TRACKED_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tracked_messages.json")


def load_tracked_ids(chat_id: int) -> set[int]:
    """Load previously saved message IDs for this chat."""
    if not os.path.exists(TRACKED_FILE):
        return set()
    try:
        with open(TRACKED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data.get(str(chat_id), []))
    except Exception:
        return set()


def track_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int | None, message_id: int | None) -> None:
    """Track message IDs in memory and disk so they can be cleared later."""
    if not message_id or not chat_id:
        return

    # In-memory tracking
    if "bot_message_ids" not in context.chat_data:
        context.chat_data["bot_message_ids"] = set()
    context.chat_data["bot_message_ids"].add(message_id)

    # Persistent file tracking
    try:
        data = {}
        if os.path.exists(TRACKED_FILE):
            with open(TRACKED_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        key = str(chat_id)
        current = set(data.get(key, []))
        current.add(message_id)
        data[key] = list(current)
        with open(TRACKED_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass


def clear_tracked_storage(chat_id: int) -> None:
    """Clear saved message IDs for this chat."""
    try:
        if os.path.exists(TRACKED_FILE):
            with open(TRACKED_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            data.pop(str(chat_id), None)
            with open(TRACKED_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f)
    except Exception:
        pass


async def clear_chat(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Clear chat history all at once without sending any follow-up message."""
    chat = update.effective_chat
    if not chat:
        return

    chat_id = chat.id
    current_msg_id = update.effective_message.message_id if update.effective_message else None

    # Collect tracked message IDs from memory and persistent file
    candidate_ids = set(context.chat_data.get("bot_message_ids", set()))
    candidate_ids.update(load_tracked_ids(chat_id))

    if current_msg_id:
        candidate_ids.add(current_msg_id)
        # Check a reasonable window of recent message IDs
        candidate_ids.update(range(max(1, current_msg_id - 30), current_msg_id + 1))

    # Reset tracking
    context.chat_data["bot_message_ids"] = set()
    clear_tracked_storage(chat_id)

    if not candidate_ids:
        return

    sorted_ids = sorted(candidate_ids, reverse=True)

    # Delete in bulk chunks of up to 100 at a time
    for i in range(0, len(sorted_ids), 100):
        chunk = sorted_ids[i:i + 100]
        try:
            await context.bot.delete_messages(chat_id=chat_id, message_ids=chunk)
        except Exception:
            for mid in chunk:
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=mid)
                except Exception:
                    pass


def find_button_action(text: str) -> dict | None:
    if not text:
        return None
    if text in BUTTON_ACTIONS:
        return BUTTON_ACTIONS[text]
    # Strip any leading fallback emojis and spaces
    clean = text.lstrip("✉️💁‍♀️💼📢🛡️❤️💝💸💡📄🔗🎵❓📌📈 ").strip()
    return BUTTON_ACTIONS.get(clean)


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user = update.effective_user
    if user:
        name = user.full_name or ""
        username_part = f"({user.username})" if user.username else ""
        user_display = f"{name}".strip() if username_part else (name or "មិត្តភក្តិ")
        welcome_text = (
            f"ជម្រាបសួរ {user_display} \n\n"
            f"សូមស្វាគមន៍មកកាន់ Career Center CV Bot! {tg_emoji(EMOJI_WAVE, '👋')}\n\n"
            f"សូមជ្រើសរើស Menu ខាងក្រោម {tg_emoji(EMOJI_DOWN, '👇')}"
        )
    else:
        welcome_text = f"សូមស្វាគមន៍! សូមជ្រើសរើស Menu ខាងក្រោម {tg_emoji(EMOJI_DOWN, '👇')}"

    if update.message:
        track_message(context, update.effective_chat.id, update.message.message_id)
    sent = await update.message.reply_text(
        welcome_text,
        reply_markup=menu,
        parse_mode="HTML",
    )
    track_message(context, update.effective_chat.id, sent.message_id)


async def faq_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Show the FAQ menu."""
    if update.message:
        track_message(context, update.effective_chat.id, update.message.message_id)
    sent = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=get_faq_text(0),
        reply_markup=build_faq_keyboard(0),
        parse_mode="HTML",
    )
    track_message(context, update.effective_chat.id, sent.message_id)


async def handle_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "donate_us":
        if os.path.exists(QR_IMAGE_PATH):
            with open(QR_IMAGE_PATH, "rb") as photo_file:
                sent = await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=photo_file,
                    caption=(
                        f"{tg_emoji(EMOJI_DONATE, '💝')} <b>Donate to Support Us</b>\n\n"
                        f"👤 <b>ឈ្មោះ៖</b> {DONATE_NAME}\n"
                        f"💳 <b>Wallet KHR៖</b> <code>{DONATE_KHR}</code>\n\n"
                        f"💳 <b>Wallet USD៖</b> <code>{DONATE_USD}</code>\n\n"
                        f"សូមស្កេន KHQR ខាងលើដើម្បីឧបត្ថម្ភគាំទ្រ Career Center! សូមអរគុណច្រើន 🙏"
                    ),
                    parse_mode="HTML",
                )
                track_message(context, update.effective_chat.id, sent.message_id)
        else:
            sent = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=(
                    f"{tg_emoji(EMOJI_DONATE, '💝')} <b>Donate to Support Us</b>\n\n"
                    f"👤 <b>ឈ្មោះ៖</b> {DONATE_NAME_ALT}\n"
                    f"💳 <b>Wallet KHR៖</b> <code>{DONATE_KHR_ALT}</code>"
                ),
                parse_mode="HTML",
            )
            track_message(context, update.effective_chat.id, sent.message_id)

    elif query.data.startswith("faq_p_"):
        page = int(query.data.split("_")[2])
        try:
            await query.edit_message_text(
                text=get_faq_text(page),
                reply_markup=build_faq_keyboard(page),
                parse_mode="HTML",
            )
        except BadRequest:
            pass

    elif query.data.startswith("faq_a_"):
        idx = int(query.data.split("_")[2])
        if 0 <= idx < len(FAQ_ITEMS):
            item = FAQ_ITEMS[idx]
            try:
                await query.edit_message_text(
                    text=item["a"],
                    reply_markup=build_faq_answer_keyboard(idx),
                    parse_mode="HTML",
                )
            except BadRequest:
                pass

    elif query.data == "faq_noop":
        pass


async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not update.message:
        return

    # 🔍 Animated Custom Emoji Inspector:
    # If the user sends any animated custom emoji to the bot, reply with its ID
    if update.message.entities:
        for ent in update.message.entities:
            if ent.type == "custom_emoji" and ent.custom_emoji_id:
                await update.message.reply_html(
                    f"✨ <b>Detected Animated Emoji ID:</b>\n"
                    f"<code>{ent.custom_emoji_id}</code>\n\n"
                    f"👉 Copy this number into your <code>.env</code> file!"
                )
                return

    if not update.message.text:
        return

    track_message(context, update.effective_chat.id, update.message.message_id)
    user_text = update.message.text.strip()
    action = find_button_action(user_text)

    if action:
        # លុបសារដែល User ចុចប៊ូតុងដើម្បីឱ្យ Chat មើលទៅស្អាត មិនរញ៉េរញ៉ៃ (Auto-delete)
        try:
            await update.message.delete()
        except Exception:
            pass

        # បើសិនជាប៊ូតុង FAQ
        if action.get("is_faq"):
            sent = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=get_faq_text(0),
                reply_markup=build_faq_keyboard(0),
                parse_mode="HTML",
            )
            track_message(context, update.effective_chat.id, sent.message_id)
        # ប្រសិនបើប៊ូតុងមាន sub-buttons (Inline keyboard)
        elif "inline_keyboard" in action:
            sent = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=action.get("text", ""),
                reply_markup=InlineKeyboardMarkup(action["inline_keyboard"]),
                parse_mode="HTML",
            )
            track_message(context, update.effective_chat.id, sent.message_id)
        # ប្រសិនបើប៊ូតុងជាប្រភេទរូបភាព (ឧទាហរណ៍៖ QR Code Donate)
        elif "photo" in action and os.path.exists(action["photo"]):
            with open(action["photo"], "rb") as photo_file:
                sent = await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=photo_file,
                    caption=action.get("caption", ""),
                    parse_mode="HTML",
                )
                track_message(context, update.effective_chat.id, sent.message_id)
        else:
            inline_btn = None
            if "btn_label" in action and "url" in action:
                btn_emoji = action.get("btn_emoji")
                btn_fallback = action.get("btn_fallback", "🔗")
                btn_obj = make_inline_btn(
                    action["btn_label"],
                    emoji_id=btn_emoji,
                    fallback_icon=btn_fallback,
                    url=action["url"],
                )
                inline_btn = InlineKeyboardMarkup([[btn_obj]])
            sent = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=action.get("text", ""),
                reply_markup=inline_btn,
                parse_mode="HTML",
            )
            track_message(context, update.effective_chat.id, sent.message_id)
    else:
        sent = await update.message.reply_text(
            f"សូមជ្រើសរើស Menu ខាងក្រោម {tg_emoji(EMOJI_DOWN, '👇')}",
            reply_markup=menu,
            parse_mode="HTML",
        )
        track_message(context, update.effective_chat.id, sent.message_id)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle network glitches or temporary disconnects without crashing."""
    logger.warning("Network or update warning: %s", context.error)


async def post_init(application: Application) -> None:
    """Register bot commands visible in Telegram's command menu (BotFather commands)."""
    try:
        commands = [
            BotCommand("start", "Start the bot / ចាប់ផ្ដើម"),
            BotCommand("faq", "Frequently Asked Questions / សំណួរ-ចម្លើយ"),
            BotCommand("clear", "Clear chatbot message history / សម្អាតសារ"),
        ]
        await application.bot.set_my_commands(commands)
        logger.info("Bot commands registered successfully.")
    except Exception as e:
        logger.warning("Could not set bot commands: %s", e)


class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler responding to Render health checks."""

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Bot is alive and running!")

    def log_message(self, format, *args):
        # Silence access logs so console output stays clean
        pass


def start_health_check_server() -> None:
    """
    Render Web Services require listening on $PORT (usually 10000).
    If $PORT is defined, run a lightweight HTTP server in a daemon thread.
    """
    port_env = os.getenv("PORT")
    if not port_env:
        return

    try:
        port = int(port_env)
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        logger.info("Health check HTTP server started on port %s for Render.", port)
    except Exception as e:
        logger.warning("Could not start health check HTTP server: %s", e)


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN is not set. Please set BOT_TOKEN in your .env file or environment variables.")

    # Start health check server if running on Render / cloud provider with $PORT
    start_health_check_server()

    request = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=30.0,
    )

    app = (
        Application.builder()
        .token(TOKEN)
        .request(request)
        .post_init(post_init)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("faq", faq_cmd))
    app.add_handler(CommandHandler("clear", clear_chat))
    app.add_handler(CommandHandler("clearchat", clear_chat))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    app.add_error_handler(error_handler)

    print("Bot is starting...", flush=True)
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        print("\nBot stopped cleanly.")