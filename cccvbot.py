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

def tg_emoji(emoji_id: str | None, fallback: str) -> str:
    """Format an animated custom emoji for HTML parse mode, or return fallback."""
    if emoji_id and str(emoji_id).strip():
        return f'<tg-emoji emoji-id="{str(emoji_id).strip()}">{fallback}</tg-emoji>'
    return fallback


def make_reply_btn(text: str, emoji_id: str | None = None, fallback_icon: str = "") -> KeyboardButton:
    """Create a KeyboardButton with custom emoji icon if provided."""
    if emoji_id and str(emoji_id).strip():
        return KeyboardButton(text=text, api_kwargs={"icon_custom_emoji_id": str(emoji_id).strip()})
    label = f"{fallback_icon} {text}".strip() if fallback_icon else text
    return KeyboardButton(label)


def make_inline_btn(text: str, emoji_id: str | None = None, fallback_icon: str = "", **kwargs) -> InlineKeyboardButton:
    """Create an InlineKeyboardButton with custom emoji icon if provided."""
    if emoji_id and str(emoji_id).strip():
        api_kw = kwargs.pop("api_kwargs", {}) or {}
        api_kw["icon_custom_emoji_id"] = str(emoji_id).strip()
        return InlineKeyboardButton(text=text, api_kwargs=api_kw, **kwargs)
    label = f"{fallback_icon} {text}".strip() if fallback_icon else text
    return InlineKeyboardButton(label, **kwargs)

# ──────────────────────────────────────────────────────────────
# FAQ Data: Categories, Questions & Extended Answers (KH & EN)
# ──────────────────────────────────────────────────────────────
FAQ_CATEGORIES = [
    {
        "id": "arch_civil",
        "title_btn": "🏗️ ស្ថាបត្យកម្ម & សំណង់",
        "title_kh": "ជំនាញស្ថាបត្យកម្ម និងវិស្វកម្មសំណង់",
        "title_en": "Architecture & Civil Engineering",
        "header_kh": "១១. ជំនាញស្ថាបត្យកម្ម និងវិស្វកម្មសំណង់ (Architecture & Civil Engineering)",
        "positions": [
            "ស្ថាបត្យករ (Architect)",
            "វិស្វករសំណង់ស៊ីវិល (Civil Engineer)",
            "អ្នកគ្រប់គ្រងការដ្ឋាន (Site Manager)",
            "អ្នកត្រួតពិនិត្យគុណភាព (Quality Control Engineer)",
        ],
        "questions": [
            {
                "num": 1,
                "label": "គុណភាព & សុវត្ថិភាពការដ្ឋាន",
                "q_kh": "តើអ្នកធានាគុណភាព និងសុវត្ថិភាពនៅការដ្ឋានសំណង់ដូចម្តេច?",
                "q_en": "How do you ensure quality and safety on a construction site?",
                "a_kh": (
                    "<b>១. ការធានាគុណភាព (Quality Assurance):</b>\n"
                    "• <b>អនុលោមតាមប្លង់៖</b> អនុវត្តតាមប្លង់ស្ថាបត្យកម្ម និងវិស្វកម្មដែលបានអនុម័ត (Approved Drawings & Specs) យ៉ាងម៉ត់ចត់។\n"
                    "• <b>ត្រួតពិនិត្យសម្ភារ៖</b> ត្រួតពិនិត្យគុណភាពសម្ភារសំណង់ដែលនាំចូល និងធ្វើតេស្តបេតុង/ដែកមុនប្រើប្រាស់។\n"
                    "• <b>ត្រួតពិនិត្យតាមដំណាក់កាល៖</b> ធ្វើអធិការកិច្ចការងារជាប្រចាំតាមដំណាក់កាលនីមួយៗ (Inspection & Testing Plan)។\n\n"
                    "<b>២. ការធានាសុវត្ថិភាព (Safety Management):</b>\n"
                    "• <b>ឧបករណ៍ការពារ (PPE):</b> តម្រូវឱ្យបុគ្គលិក និងកម្មករទាំងអស់ពាក់មួក ស្បែកជើង និងខ្សែក្រវ៉ាត់សុវត្ថិភាពជាប្រចាំ។\n"
                    "• <b>ការបណ្តុះបណ្តាល៖</b> រៀបចំការប្រជុំសុវត្ថិភាពខ្លីៗ (Toolbox Talk) រៀងរាល់ព្រឹកមុនពេលចាប់ផ្តើមការងារ។\n"
                    "• <b>ទប់ស្កាត់ហានិភ័យ៖</b> រាយការណ៍ និងកែតម្រូវកំហុសឆ្គង ឬស្ថានភាពគ្រោះថ្នាក់ភ្លាមៗ (Zero Accident Policy)។\n\n"
                    "💡 <b>គន្លឹះសម្ភាសន៍:</b> លើកឡើងពីបទពិសោធន៍ផ្ទាល់ក្នុងការដោះស្រាយបញ្ហាបច្ចេកទេស និងការប្រកាន់ខ្ជាប់នូវបទដ្ឋានស្តង់ដារសំណង់។"
                ),
                "a_en": (
                    "<b>1. Quality Assurance:</b>\n"
                    "• <b>Compliance:</b> Adhere strictly to approved architectural and structural drawings, codes, and technical specifications.\n"
                    "• <b>Material Inspection:</b> Verify the quality of incoming construction materials and conduct standard testing (e.g., slump test, compressive strength).\n"
                    "• <b>Milestone Checks:</b> Implement rigorous inspections at every phase according to the Inspection & Test Plan (ITP).\n\n"
                    "<b>2. Safety Management:</b>\n"
                    "• <b>PPE Enforcement:</b> Mandate the use of appropriate Personal Protective Equipment (hard hats, boots, harnesses, vests) at all times.\n"
                    "• <b>Daily Briefings:</b> Conduct daily 'Toolbox Talks' to raise hazard awareness among the workforce.\n"
                    "• <b>Risk Prevention:</b> Identify, report, and rectify safety hazards immediately to achieve zero accidents.\n\n"
                    "💡 <b>Interview Tip:</b> Highlight your familiarity with building codes, quality control processes, and a safety-first mindset with practical examples."
                ),
            },
            {
                "num": 2,
                "label": "គម្រោងយឺតជាងកាលវិភាគ",
                "q_kh": "តើអ្នកធ្វើដូចម្តេច ប្រសិនបើគម្រោងយឺតជាងកាលវិភាគ?",
                "q_en": "What would you do if a project fell behind schedule?",
                "a_kh": (
                    "<b>ជំហានក្នុងការដោះស្រាយ៖</b>\n"
                    "1️⃣ <b>ស្វែងរកឫសគល់នៃបញ្ហា (Root Cause Analysis):</b> វិភាគថាតើការយឺតយ៉ាវបណ្តាលមកពីកង្វះកម្លាំងពលកម្ម សម្ភារមកយឺត អាកាសធាតុ ឬប្លង់មានការកែប្រែ។\n"
                    "2️⃣ <b>វាយតម្លៃកាលវិភាគឡើងវិញ (Schedule Assessment):</b> ប្រើវិធីសាស្ត្រ Critical Path Method (CPM) ដើម្បីកំណត់សកម្មភាពណាដែលប៉ះពាល់ដល់ថ្ងៃបញ្ចប់គម្រោងផ្ទាល់។\n"
                    "3️⃣ <b>ស្នើវិធានការដោះស្រាយ (Action Plan):</b>\n"
                    "   • បន្ថែមវេនការងារ (Overtime / Double Shifts) លើការងារអាទិភាព។\n"
                    "   • បង្កើនកម្លាំងពលកម្ម ឬម៉ាស៊ីនបន្ថែម (Fast-tracking / Crashing)។\n"
                    "4️⃣ <b>ទំនាក់ទំនងជាមួយភាគីពាក់ព័ន្ធ (Stakeholder Management):</b> ជួបពិភាក្សា និងធ្វើរបាយការណ៍ជូនម្ចាស់គម្រោង និងអ្នកម៉ៅការបន្តអំពីវិធានការស្តារកាលវិភាគឡើងវិញ។\n"
                    "5️⃣ <b>មិនបន្ថយគុណភាព និងសុវត្ថិភាព:</b> ការពន្លឿនការងារដាច់ខាតមិនត្រូវកាត់បន្ថយស្តង់ដារបច្ចេកទេស និងសុវត្ថិភាពឡើយ។\n\n"
                    "💡 <b>គន្លឹះសម្ភាសន៍:</b> បង្ហាញពីជំនាញដោះស្រាយវិបត្តិ (Crisis Management) និងសមត្ថភាពធ្វើការងារក្រោមសម្ពាធ។"
                ),
                "a_en": (
                    "<b>Action Steps to Recover:</b>\n"
                    "1️⃣ <b>Root Cause Analysis:</b> Immediately analyze why the delay occurred (material shortage, labor issues, adverse weather, or design revisions).\n"
                    "2️⃣ <b>Reassess Timeline:</b> Identify the critical path activities that directly impact the project completion date.\n"
                    "3️⃣ <b>Implement Recovery Strategies:</b>\n"
                    "   • <b>Fast-tracking:</b> Perform parallel activities where safe and feasible.\n"
                    "   • <b>Crashing:</b> Allocate additional workforce, equipment, or schedule overtime/double shifts.\n"
                    "4️⃣ <b>Stakeholder Communication:</b> Transparently brief clients, consultants, and subcontractors on the revised recovery schedule.\n"
                    "5️⃣ <b>Maintain Standards:</b> Ensure quality assurance and site safety are never sacrificed for the sake of speed.\n\n"
                    "💡 <b>Interview Tip:</b> Demonstrate leadership, strategic planning, and the ability to maintain composure under high-pressure deadlines."
                ),
            },
        ],
    },
    {
        "id": "languages",
        "title_btn": "🗣️ ភាសាអង់គ្លេស & ចិន",
        "title_kh": "ជំនាញភាសាអង់គ្លេស និងភាសាចិន",
        "title_en": "English & Chinese Teaching",
        "header_kh": "១២. ជំនាញភាសាអង់គ្លេស និងភាសាចិន (English & Chinese Teaching)",
        "positions": [
            "គ្រូបង្រៀនភាសាអង់គ្លេស (English Teacher)",
            "គ្រូបង្រៀនភាសាចិន (Chinese Teacher)",
            "អ្នកបកប្រែ (Translator)",
            "អ្នកបកប្រែផ្ទាល់មាត់ (Interpreter)",
        ],
        "questions": [
            {
                "num": 1,
                "label": "បង្រៀនសិស្សកម្រិតខុសគ្នា",
                "q_kh": "តើអ្នកបង្រៀនសិស្សដែលមានកម្រិតភាសាខុសៗគ្នាដូចម្តេច?",
                "q_en": "How would you teach students with different language levels?",
                "a_kh": (
                    "<b>វិធីសាស្ត្រក្នុងការគ្រប់គ្រងថ្នាក់រៀនចម្រុះកម្រិត (Mixed-ability classes):</b>\n"
                    "1️⃣ <b>វាយតម្លៃសមត្ថភាពដំបូង៖</b> ធ្វើតេស្តសាកល្បង ឬសង្កេតដើម្បីដឹងពីកម្រិតជាក់ស្តែងរបស់សិស្សម្នាក់ៗ។\n"
                    "2️⃣ <b>បែងចែកភារកិច្ចតាមកម្រិត (Differentiated Tasks):</b> ផ្តល់លំហាត់ ឬកិច្ចការដែលមានកម្រិតលំបាកខុសៗគ្នាលើប្រធានបទតែមួយ។\n"
                    "3️⃣ <b>ការរៀនជាដៃគូ (Peer Learning):</b> ចាត់តាំងសិស្សដែលពូកែឱ្យជួយពន្យល់សិស្សដែលខ្សោយ ដែលជួយទាំងសងខាងឱ្យយល់កាន់តែច្បាស់។\n"
                    "4️⃣ <b>ការប្រើប្រាស់ឧបករណ៍ជំនួយ (Scaffolding & Media):</b> ប្រើប្រាស់រូបភាព វីដេអូ កាយវិការ និងបច្ចេកវិទ្យាដើម្បីឱ្យសិស្សងាយយល់។\n"
                    "5️⃣ <b>ការលើកទឹកចិត្ត និង Feedback:</b> ផ្តល់ការសរសើរចំពោះការរីកចម្រើនផ្ទាល់ខ្លួនរបស់សិស្សម្នាក់ៗ ជាជាងការប្រៀបធៀបគ្នាក្នុងថ្នាក់។\n\n"
                    "💡 <b>គន្លឹះសម្ភាសន៍:</b> បង្ហាញពីវិធីសាស្ត្របង្រៀនដែលមានភាពច្នៃប្រឌិត និងការយកចិត្តទុកដាក់លើសិស្សគ្រប់កម្រិត។"
                ),
                "a_en": (
                    "<b>Strategies for Mixed-Ability Classrooms:</b>\n"
                    "1️⃣ <b>Initial Assessment:</b> Gauge students' proficiency levels through diagnostics, informal observation, and interactive activities.\n"
                    "2️⃣ <b>Differentiated Instruction:</b> Design tiered tasks where beginners work on core vocabulary/grammar while advanced learners tackle extended analytical exercises.\n"
                    "3️⃣ <b>Peer-Assisted Learning:</b> Pair stronger students with those who need support, reinforcing comprehension for both parties.\n"
                    "4️⃣ <b>Scaffolded Learning:</b> Use visual aids, realia, gestures, and interactive multimedia to bridge language comprehension gaps.\n"
                    "5️⃣ <b>Individualized Feedback:</b> Celebrate progress relative to each student's starting point to boost confidence and motivation.\n\n"
                    "💡 <b>Interview Tip:</b> Emphasize adaptability, empathy, and your repertoire of engaging pedagogical techniques."
                ),
            },
            {
                "num": 2,
                "label": "ភាពត្រឹមត្រូវនៃការបកប្រែ",
                "q_kh": "តើអ្នកធានាភាពត្រឹមត្រូវនៃការបកប្រែដូចម្តេច?",
                "q_en": "How do you ensure an accurate translation?",
                "a_kh": (
                    "<b>គោលការណ៍បកប្រែប្រកបដោយវិជ្ជាជីវៈ៖</b>\n"
                    "1️⃣ <b>ស្វែងយល់បរិបទឱ្យច្បាស់ (Context is King):</b> អានអត្ថបទទាំងមូលដើម្បីយល់ពីគោលបំណង អត្ថន័យបង្កប់ និងអ្នកអានគោលដៅ។\n"
                    "2️⃣ <b>ភាពត្រឹមត្រូវនៃពាក្យបច្ចេកទេស:</b> ស្រាវជ្រាវ និងផ្ទៀងផ្ទាត់ពាក្យបច្ចេកទេសក្នុងវិស័យពាក់ព័ន្ធ (ច្បាប់ វេជ្ជសាស្ត្រ ហិរញ្ញវត្ថុ...) ឱ្យមានភាពស៊ីសង្វាក់គ្នា។\n"
                    "3️⃣ <b>រក្សាសំនៀង និងរចនាបថ (Tone & Cultural Nuance):</b> មិនបកប្រែពាក្យមួយទល់នឹងពាក្យមួយ (Word-for-word) ប៉ុន្តែបកប្រែអត្ថន័យ និងបរិបទវប្បធម៌ឱ្យសមរម្យ។\n"
                    "4️⃣ <b>ដំណើរការត្រួតពិនិត្យ (Two-pass Proofreading):</b> ផ្ទៀងផ្ទាត់លើកទី ១ ជាមួយអត្ថបទដើម និងលើកទី ២ អានជាអត្ថបទសម្រេចដើម្បីពិនិត្យវេយ្យាករណ៍ និងលំហូរនៃភាសា។\n"
                    "5️⃣ <b>ក្រមសីលធម៌:</b> រក្សាការសម្ងាត់នៃឯកសារ និងមិនបន្ថែមបន្ថយអត្ថន័យផ្ទាល់ខ្លួន។\n\n"
                    "💡 <b>គន្លឹះសម្ភាសន៍:</b> បញ្ជាក់ពីការយកចិត្តទុកដាក់ខ្ពស់លើភាពជាក់លាក់ និងសមត្ថភាពបកប្រែទាំងភាសា និងវប្បធម៌។"
                ),
                "a_en": (
                    "<b>Professional Translation Standards:</b>\n"
                    "1️⃣ <b>Context Comprehension:</b> Read through the entire source text first to grasp tone, nuance, target audience, and communicative intent.\n"
                    "2️⃣ <b>Terminology Consistency:</b> Build and reference specialized glossaries to ensure accurate, consistent industry-specific terms (legal, technical, medical, etc.).\n"
                    "3️⃣ <b>Meaning over Literal Translation:</b> Focus on dynamic equivalence rather than word-for-word translation to sound natural while faithfully conveying the message.\n"
                    "4️⃣ <b>Two-Pass Quality Check:</b> First pass compares translation against the source text; second pass reviews the target text alone for fluency and natural flow.\n"
                    "5️⃣ <b>Professional Ethics:</b> Strictly maintain client confidentiality and impartial accuracy.\n\n"
                    "💡 <b>Interview Tip:</b> Highlight your linguistic accuracy, cultural sensitivity, and systematic proofreading habits."
                ),
            },
        ],
    },
    {
        "id": "literature_history",
        "title_btn": "📚 អក្សរសាស្ត្រ & ប្រវត្តិ",
        "title_kh": "ជំនាញអក្សរសាស្ត្រខ្មែរ និងប្រវត្តិសាស្ត្រ",
        "title_en": "Khmer Literature & History",
        "header_kh": "១៣. ជំនាញអក្សរសាស្ត្រខ្មែរ និងប្រវត្តិសាស្ត្រ (Khmer Literature & History)",
        "positions": [
            "គ្រូបង្រៀនអក្សរសាស្ត្រខ្មែរ (Khmer Literature Teacher)",
            "អ្នកស្រាវជ្រាវ (Researcher)",
            "អ្នកនិពន្ធ (Writer)",
            "មន្ត្រីវប្បធម៌ (Cultural Affairs Officer)",
        ],
        "questions": [
            {
                "num": 1,
                "label": "ភាពត្រឹមត្រូវនៃព័ត៌មានប្រវត្តិ",
                "q_kh": "តើអ្នកធានាភាពត្រឹមត្រូវនៃព័ត៌មានប្រវត្តិសាស្ត្រដូចម្តេច?",
                "q_en": "How do you ensure the accuracy of historical information?",
                "a_kh": (
                    "<b>វិធីសាស្ត្រស្រាវជ្រាវប្រវត្តិសាស្ត្របែបវិទ្យាសាស្ត្រ៖</b>\n"
                    "1️⃣ <b>ផ្តល់អាទិភាពលើប្រភពបឋម (Primary Sources):</b> សិក្សាសិលាចារឹក ឯកសារបណ្ណសារដ្ឋាន កំណត់ត្រាបុរាណ និងវត្ថុបុរាណវិទ្យា។\n"
                    "2️⃣ <b>ផ្ទៀងផ្ទាត់ពហុប្រភព (Cross-referencing):</b> ប្រៀបធៀបឯកសារជាច្រើនដែលមានប្រភពខុសៗគ្នា (ឯកសារជាតិ អន្តរជាតិ កំណត់ត្រាអ្នកដំណើរ...) ដើម្បីបញ្ជាក់ការពិត។\n"
                    "3️⃣ <b>បែងចែកការពិត និងមតិ៖</b> ញែកឱ្យដាច់រវាងអង្គហេតុប្រវត្តិសាស្ត្រដែលបានផ្ទៀងផ្ទាត់ (Facts) និងការបកស្រាយឬមតិផ្ទាល់ខ្លួន (Opinions/Narratives)។\n"
                    "4️⃣ <b>ពិនិត្យបរិបទសង្គមសម័យនោះ៖</b> វិភាគព្រឹត្តិការណ៍ដោយផ្អែកលើស្ថានភាពនយោបាយ សេដ្ឋកិច្ច និងជំនឿនាសម័យកាលនោះ មិនមែនទស្សនៈបច្ចុប្បន្នឡើយ។\n"
                    "5️⃣ <b>កត់ត្រាប្រភពយោងច្បាស់លាស់៖</b> ដាក់ឯកសារយោង និងគន្ថនិទ្ទេសឱ្យបានត្រឹមត្រូវគ្រប់ពេល។\n\n"
                    "💡 <b>គន្លឹះសម្ភាសន៍:</b> បញ្ជាក់ពីជំហរអព្យាក្រឹត្យ ភាពម៉ត់ចត់ និងការស្រឡាញ់ការស្រាវជ្រាវយ៉ាងស៊ីជម្រៅ។"
                ),
                "a_en": (
                    "<b>Methodology for Historical Accuracy:</b>\n"
                    "1️⃣ <b>Primary Sources First:</b> Rely primarily on original documents, stone inscriptions, archival materials, and archaeological evidence.\n"
                    "2️⃣ <b>Cross-Referencing:</b> Compare multiple independent sources (local accounts, foreign chronicles, archaeological findings) to corroborate events.\n"
                    "3️⃣ <b>Distinguish Fact from Bias:</b> Separate verified historical facts from ideological narratives, subjective accounts, or period-specific biases.\n"
                    "4️⃣ <b>Contextual Analysis:</b> Interpret historical events within the socio-political and cultural climate of the era in which they occurred.\n"
                    "5️⃣ <b>Meticulous Citation:</b> Provide clear, verifiable citations and references for all claims made.\n\n"
                    "💡 <b>Interview Tip:</b> Highlight your dedication to research ethics, critical thinking, and objective analysis."
                ),
            },
            {
                "num": 2,
                "label": "បង្រៀនអក្សរសាស្ត្រឱ្យទាក់ទាញ",
                "q_kh": "តើអ្នកធ្វើឱ្យមេរៀនអក្សរសាស្ត្រទាក់ទាញសិស្សដូចម្តេច?",
                "q_en": "How would you make a literature lesson engaging?",
                "a_kh": (
                    "<b>បច្ចេកទេសបង្រៀនអក្សរសាស្ត្របែបទំនើប និងទាក់ទាញ៖</b>\n"
                    "1️⃣ <b>សិល្បៈនៃការនិទានរឿង (Compelling Storytelling):</b> បង្ហាញតួអង្គ និងសាច់រឿងឱ្យមានជីវិត ធ្វើឱ្យសិស្សមានអារម្មណ៍ចូលតួ និងចង់តាមដាន។\n"
                    "2️⃣ <b>ការភ្ជាប់ទៅនឹងជីវិតជាក់ស្តែង៖</b> យកបញ្ហាក្នុងរឿង (សេចក្ដីស្រឡាញ់ គ្រួសារ សង្គម) មកជជែកប្រៀបធៀបនឹងជីវិតសង្គមសម័យបច្ចុប្បន្ន។\n"
                    "3️⃣ <b>សកម្មភាពល្ខោន និងការសម្ដែង (Role-play/Drama):</b> ឱ្យសិស្សរៀបចំឈុតឆាកខ្លីៗសម្ដែងជាតួអង្គក្នុងរឿង ដើម្បីយល់ពីជម្រៅចិត្តរបស់តួអង្គ។\n"
                    "4️⃣ <b>ការពិភាក្សាដេញដោល (Socratic Debate):</b> បើកវេទិកាឱ្យសិស្សបញ្ចេញមតិយោបល់ និងការពារទស្សនៈរបស់ខ្លួនលើទង្វើតួអង្គ។\n"
                    "5️⃣ <b>ប្រើប្រាស់ប្រព័ន្ធផ្សព្វផ្សាយ (Multimedia Integration):</b> ប្រើគំនូរជីវចល ខ្សែភាពយន្តសម្រង់ ឬចម្រៀងទាក់ទងនឹងស្នាដៃអក្សរសិល្ប៍នោះ។\n\n"
                    "💡 <b>គន្លឹះសម្ភាសន៍:</b> បង្ហាញពីវិធីសាស្រ្តដែលបង្វែរអក្សរសាស្ត្រពីមុខវិជ្ជាទន្ទេញចាំ ទៅជាមុខវិជ្ជាបណ្តុះការគិតស៊ីជម្រៅ។"
                ),
                "a_en": (
                    "<b>Techniques for Engaging Literature Instruction:</b>\n"
                    "1️⃣ <b>Dynamic Storytelling:</b> Bring characters and plotlines to life, cultivating emotional connection and curiosity among learners.\n"
                    "2️⃣ <b>Real-World Connections:</b> Relate central themes—such as morality, social justice, and personal conflict—to students' own lives and current society.\n"
                    "3️⃣ <b>Role-Playing & Dramatization:</b> Have students act out key scenes to develop a deeper understanding of character motivations and perspectives.\n"
                    "4️⃣ <b>Socratic Discussions & Debates:</b> Encourage critical thinking by asking open-ended questions and debating characters' decisions.\n"
                    "5️⃣ <b>Multimedia Tools:</b> Use video adaptations, audio dramatizations, and visual arts connected to the literary work.\n\n"
                    "💡 <b>Interview Tip:</b> Emphasize how you inspire critical reading rather than rote memorization, fostering lifelong appreciation for literature."
                ),
            },
        ],
    },
    {
        "id": "hr",
        "title_btn": "👥 ធនធានមនុស្ស (HR)",
        "title_kh": "ជំនាញធនធានមនុស្ស",
        "title_en": "Human Resources",
        "header_kh": "១៤. ជំនាញធនធានមនុស្ស (Human Resources)",
        "positions": [
            "មន្ត្រីធនធានមនុស្ស (HR Officer)",
            "មន្ត្រីជ្រើសរើសបុគ្គលិក (Recruitment Officer)",
            "មន្ត្រីបណ្តុះបណ្តាល (Training Officer)",
        ],
        "questions": [
            {
                "num": 1,
                "label": "ការពិនិត្យជ្រើសរើសបេក្ខជន",
                "q_kh": "តើអ្នកពិនិត្យជ្រើសរើសបេក្ខជនដាក់ពាក្យការងារដូចម្តេច?",
                "q_en": "How do you screen job applicants?",
                "a_kh": (
                    "<b>ដំណើរការជ្រើសរើសបេក្ខជនប្រកបដោយប្រសិទ្ធភាព៖</b>\n"
                    "1️⃣ <b>ពិនិត្យប្រវត្តិរូបសង្ខេប (CV/Resume Screening):</b>\n"
                    "   • ពិនិត្យភាពត្រូវគ្នារវាងបទពិសោធន៍ និងតម្រូវការមុខតំណែង (Job Description Match)\n"
                    "   • ពិនិត្យកម្រិតអប់រំ ជំនាញបច្ចេកទេស និងសមិទ្ធិផលជាក់ស្តែងដែលបង្ហាញជាលេខ/ទិន្នន័យ។\n"
                    "2️⃣ <b>ការសម្ភាសន៍បឋម (Phone/Short Video Screening):</b>\n"
                    "   • វាយតម្លៃជំនាញទំនាក់ទំនង និងកម្រិតភាសា\n"
                    "   • បញ្ជាក់ពីការរំពឹងទុកប្រាក់ខែ និងកាលបរិច្ឆេទអាចចូលបម្រើការងារបាន។\n"
                    "3️⃣ <b>ប្រើប្រាស់តារាងពិន្ទុស្តង់ដារ (Scoring Rubric):</b> ធានាការវាយតម្លៃប្រកបដោយតម្លាភាព គ្មានការលំអៀង និងផ្តល់ឱកាសស្មើគ្នា។\n"
                    "4️⃣ <b>ការផ្ទៀងផ្ទាត់ឯកសារយោង (Reference Check):</b> ទំនាក់ទំនងទៅកាន់កន្លែងធ្វើការមុន ដើម្បីបញ្ជាក់ពីអត្តចរិត និងប្រសិទ្ធភាពការងារ។\n"
                    "5️⃣ <b>ការសម្ងាត់៖</b> រក្សាព័ត៌មានផ្ទាល់ខ្លួនរបស់បេក្ខជនទាំងអស់ជាការសម្ងាត់។\n\n"
                    "💡 <b>គន្លឹះសម្ភាសន៍:</b> បញ្ជាក់ពីការយល់ដឹងលើទីផ្សារការងារ ការប្រើប្រាស់បច្ចេកវិទ្យាជ្រើសរើសបុគ្គលិក និងក្រមសីលធម៌ HR។"
                ),
                "a_en": (
                    "<b>Structured Applicant Screening Process:</b>\n"
                    "1️⃣ <b>Resume & Portfolio Review:</b>\n"
                    "   • Assess alignment between qualifications and the role's core requirements (Job Description).\n"
                    "   • Look for quantifiable achievements, career progression, and relevant technical competencies.\n"
                    "2️⃣ <b>Initial Phone/Video Screening:</b>\n"
                    "   • Evaluate communication skills, enthusiasm, and cultural alignment.\n"
                    "   • Verify salary expectations, availability, and reason for seeking a new role.\n"
                    "3️⃣ <b>Standardized Scoring Rubric:</b> Apply consistent evaluation criteria to ensure fairness and minimize unconscious bias.\n"
                    "4️⃣ <b>Professional Reference Checks:</b> Contact past employers to verify performance history, integrity, and work ethic.\n"
                    "5️⃣ <b>Confidentiality & Compliance:</b> Safeguard applicant data in compliance with labor laws and company privacy policies.\n\n"
                    "💡 <b>Interview Tip:</b> Emphasize objective evaluation, data-driven hiring practices, and the candidate experience."
                ),
            },
            {
                "num": 2,
                "label": "ដោះស្រាយបណ្តឹងបុគ្គលិក",
                "q_kh": "តើអ្នកធ្វើដូចម្តេច ប្រសិនបើបុគ្គលិកត្អូញត្អែរថាត្រូវបានប្រព្រឹត្តដោយមិនយុត្តិធម៌?",
                "q_en": "What would you do if an employee complained about unfair treatment?",
                "a_kh": (
                    "<b>នីតិវិធីដោះស្រាយបណ្តឹងតវ៉ារបស់បុគ្គលិក (Grievance Handling):</b>\n"
                    "1️⃣ <b>ស្តាប់ដោយការយល់ចិត្ត និងអព្យាក្រឹត្យ:</b> ផ្តល់កន្លែងសុវត្ថិភាពដើម្បីឱ្យបុគ្គលិករៀបរាប់ពីបញ្ហាដោយគ្មានការកាត់សេចក្តីជាមុន។\n"
                    "2️⃣ <b>កត់ត្រាព័ត៌មានលម្អិត:</b> កត់ត្រាកាលបរិច្ឆេទ ព្រឹត្តិការណ៍ បុគ្គលពាក់ព័ន្ធ និងប្រមូលភស្តុតាង (សារ អ៊ីមែល ឯកសារ)។\n"
                    "3️⃣ <b>ស្រាវជ្រាវ និងស៊ើបអង្កេតដោយសម្ងាត់:</b> ជួបសម្ភាសន៍ភាគីម្ខាងទៀត និងសាក្សី (បើមាន) ដោយរក្សាការសម្ងាត់ជាដាច់ខាត។\n"
                    "4️⃣ <b>ពិនិត្យគោលការណ៍ និងច្បាប់ការងារ:</b> ផ្ទៀងផ្ទាត់ជាមួយបទបញ្ជាផ្ទៃក្នុងរបស់ក្រុមហ៊ុន និងច្បាប់ស្តីពីការងារនៃព្រះរាជាណាចក្រកម្ពុជា។\n"
                    "5️⃣ <b>ចាត់វិធានការដោះស្រាយសមស្រប:</b> សម្របសម្រួលដោះស្រាយ ផ្ដល់ដំណោះស្រាយយុត្តិធម៌ និងដាក់ទណ្ឌកម្មវិន័យបើមានការបំពានច្បាប់។\n"
                    "6️⃣ <b>តាមដានស្ថានភាព (Follow-up):</b> ធានាថាមិនមានការសងសឹក (No Retaliation) និងបរិយាកាសការងារត្រូវបានកែលម្អ។\n\n"
                    "💡 <b>គន្លឹះសម្ភាសន៍:</b> បង្ហាញពីភាពចាស់ទុំក្នុងការដោះស្រាយវិបត្តិ ជំនាញទំនាក់ទំនងអន្តរបុគ្គល និងការការពារផលប្រយោជន៍ទាំងបុគ្គលិកនិងក្រុមហ៊ុន។"
                ),
                "a_en": (
                    "<b>Professional Grievance Resolution Procedure:</b>\n"
                    "1️⃣ <b>Active, Empathetic Listening:</b> Provide a safe, confidential space for the employee to express their concerns without prejudice.\n"
                    "2️⃣ <b>Documentation:</b> Carefully record specific incidents, dates, names, witnesses, and any supporting evidence.\n"
                    "3️⃣ <b>Impartial Investigation:</b> Interview the other involved party and any relevant witnesses discreetly to gather all perspectives.\n"
                    "4️⃣ <b>Policy & Legal Review:</b> Compare the facts against internal company policies, code of conduct, and local labor legislation.\n"
                    "5️⃣ <b>Constructive Resolution:</b> Propose a fair, actionable resolution, mediate when appropriate, and enforce corrective measures if violations occurred.\n"
                    "6️⃣ <b>Follow-up & Monitoring:</b> Monitor the workplace environment to ensure zero retaliation and verify that the issue has been genuinely resolved.\n\n"
                    "💡 <b>Interview Tip:</b> Highlight your emotional intelligence, confidentiality, conflict resolution skills, and fairness."
                ),
            },
        ],
    },
    {
        "id": "general_cv",
        "title_btn": "📄 គន្លឹះទូទៅអំពី CV",
        "title_kh": "គន្លឹះទូទៅអំពីការសរសេរ CV",
        "title_en": "General CV Writing Tips",
        "header_kh": "គន្លឹះទូទៅអំពីការសរសេរ CV (General CV Writing Tips)",
        "positions": [
            "សម្រាប់គ្រប់មុខតំណែង និងគ្រប់កម្រិតការងារ",
        ],
        "questions": [
            {
                "num": 1,
                "label": "ចំនួនទំព័រ CV សមស្រប",
                "q_kh": "តើ CV ល្អគួរមានប៉ុន្មានទំព័រ?",
                "q_en": "How many pages should a good CV be?",
                "a_kh": (
                    "📄 <b>ប្រវែងដែលល្អបំផុតសម្រាប់ CV៖</b>\n\n"
                    "• <b>១ ទំព័រ:</b> ល្អបំផុតសម្រាប់និស្សិតទើបបញ្ចប់ការសិក្សា ឬអ្នកដែលមានបទពិសោធន៍ការងារតិចជាង ៥ ឆ្នាំ។\n"
                    "• <b>២ ទំព័រ:</b> សមស្របសម្រាប់អ្នកដែលមានបទពិសោធន៍លើសពី ៥ ឆ្នាំ ឬតំណែងគ្រប់គ្រង/បច្ចេកទេសកម្រិតខ្ពស់។\n"
                    "• <b>៣ ទំព័រឡើង:</b> សម្រាប់តែវិស័យស្រាវជ្រាវ ការសិក្សាជាន់ខ្ពស់ (Academic CV) ឬមុខតំណែងវេជ្ជសាស្ត្រប៉ុណ្ណោះ។\n\n"
                    "💡 <b>គន្លឹះសំខាន់:</b> អ្នកជ្រើសរើសបុគ្គលិកចំណាយពេលត្រឹមតែ ៦-១០ វិនាទីប៉ុណ្ណោះក្នុងការមើល CV មួយ ដូច្នេះសូមសង្ខេបតែចំណុចសំខាន់ៗ និងពាក់ព័ន្ធបំផុត!"
                ),
                "a_en": (
                    "📄 <b>Ideal CV Length:</b>\n\n"
                    "• <b>1 Page:</b> Recommended for fresh graduates, entry-level, and professionals with under 5 years of experience.\n"
                    "• <b>2 Pages:</b> Appropriate for mid-to-senior professionals, managers, or those with extensive relevant experience.\n"
                    "• <b>3+ Pages:</b> Generally reserved for academic, research, or clinical/medical positions.\n\n"
                    "💡 <b>Pro Tip:</b> Recruiters typically spend 6-10 seconds reviewing a resume. Keep it concise, relevant, and impactful!"
                ),
            },
            {
                "num": 2,
                "label": "ព័ត៌មានដែលត្រូវមានក្នុង CV",
                "q_kh": "តើ CV ត្រូវមានផ្នែកសំខាន់ៗអ្វីខ្លះ?",
                "q_en": "What essential sections should be included in a CV?",
                "a_kh": (
                    "📝 <b>ផ្នែកសំខាន់ៗដែលមិនអាចខ្វះបានក្នុង CV៖</b>\n\n"
                    "1️⃣ <b>ព័ត៌មានផ្ទាល់ខ្លួន (Contact Information):</b> ឈ្មោះពេញ លេខទូរស័ព្ទ អ៊ីមែលដែលមានលក្ខណៈវិជ្ជាជីវៈ និងទីលំនៅបច្ចុប្បន្ន។\n"
                    "2️⃣ <b>សេចក្តីសង្ខេបអំពីខ្លួនឯង (Professional Summary):</b> សេចក្តីផ្តើមខ្លី ២-៣ ជួរបង្ហាញពីបទពិសោធន៍ និងគោលដៅការងារ។\n"
                    "3️⃣ <b>បទពិសោធន៍ការងារ (Work Experience):</b> រៀបរាប់ពីការងារថ្មីបំផុតទៅចាស់ បញ្ជាក់ពីតួនាទី ក្រុមហ៊ុន និងសមិទ្ធិផលសំខាន់ៗ។\n"
                    "4️⃣ <b>កម្រិតវប្បធម៌ និងការអប់រំ (Education):</b> សញ្ញាបត្រ ជំនាញ និងគ្រឹះស្ថានសិក្សា។\n"
                    "5️⃣ <b>ជំនាញ (Skills):</b> ទាំង Hard Skills (បច្ចេកទេស) និង Soft Skills (ទំនាក់ទំនង ភាពជាអ្នកដឹកនាំ)។\n"
                    "6️⃣ <b>ភាសា និងវគ្គបណ្តុះបណ្តាល (Languages & Certifications):</b> កម្រិតភាសាបរទេស និងវិញ្ញាបនបត្រពាក់ព័ន្ធ។"
                ),
                "a_en": (
                    "📝 <b>Essential Sections of a Competitive CV:</b>\n\n"
                    "1️⃣ <b>Contact Information:</b> Full name, professional email, phone number, location, and LinkedIn profile.\n"
                    "2️⃣ <b>Professional Summary:</b> A powerful 2-3 sentence overview of your key qualifications, experience, and value proposition.\n"
                    "3️⃣ <b>Work Experience:</b> Listed in reverse chronological order with action verbs and quantifiable achievements.\n"
                    "4️⃣ <b>Education:</b> Degree title, institution, graduation year, and academic honors (if applicable).\n"
                    "5️⃣ <b>Skills:</b> A balanced mix of technical (Hard) skills and interpersonal (Soft) skills.\n"
                    "6️⃣ <b>Languages & Certifications:</b> Language proficiencies and accredited professional certifications."
                ),
            },
            {
                "num": 3,
                "label": "អ្វីដែលមិនគួរដាក់ក្នុង CV",
                "q_kh": "តើអ្វីខ្លះដែលមិនគួរដាក់ក្នុង CV?",
                "q_en": "What should you avoid including in your CV?",
                "a_kh": (
                    "🚫 <b>ចំណុចដែលគួរចៀសវាងក្នុង CV៖</b>\n\n"
                    "❌ <b>រូបថតមិនសមរម្យ៖</b> រូប Selfie រូបទេសចរណ៍ ឬរូបកាត់តមិនស្អាត។\n"
                    "❌ <b>ព័ត៌មានផ្ទាល់ខ្លួនហួសហេតុ៖</b> ស្ថានភាពគ្រួសារ សាសនា និន្នាការនយោបាយ ឬលេខអត្តសញ្ញាណប័ណ្ណ។\n"
                    "❌ <b>អ៊ីមែលមិនផ្លូវការ៖</b> ជៀសវាងអ៊ីមែលដូចជា cute_boy@... គួរប្រើឈ្មោះពេញ។\n"
                    "❌ <b>ប្រាក់ខែចាស់ ឬប្រាក់ខែរំពឹងទុក៖</b> មិនត្រូវដាក់ក្នុង CV ទេ ទុកពិភាក្សានៅពេលសម្ភាសន៍។\n"
                    "❌ <b>មូលហេតុចាកចេញពីការងារចាស់៖</b> មិនចាំបាច់សរសេរក្នុង CV ឡើយ។\n"
                    "❌ <b>ព័ត៌មានមិនពិត៖</b> ការបំផ្លើសជំនាញ ឬបទពិសោធន៍អាចនាំឱ្យបាត់បង់ឱកាសភ្លាមៗ។"
                ),
                "a_en": (
                    "🚫 <b>Common Mistakes to Avoid on Your CV:</b>\n\n"
                    "❌ <b>Unprofessional Photos:</b> Casual selfies, cropped party pictures, or low-resolution images.\n"
                    "❌ <b>Irrelevant Personal Data:</b> Marital status, religion, political views, or national ID numbers.\n"
                    "❌ <b>Informal Email Addresses:</b> Use a clean, professional address (e.g., firstname.lastname@email.com).\n"
                    "❌ <b>Salary Details:</b> Never include past or desired salary unless explicitly requested.\n"
                    "❌ <b>Reasons for Leaving:</b> Keep this for interview discussions; it does not belong on a CV.\n"
                    "❌ <b>Dishonesty / Exaggeration:</b> Falsifying qualifications can permanently damage your professional reputation."
                ),
            },
            {
                "num": 4,
                "label": "របៀបផ្ញើ CV ប្រកបដោយវិជ្ជាជីវៈ",
                "q_kh": "តើគួរផ្ញើ CV តាមរបៀបណាដើម្បីទទួលបានការចាប់អារម្មណ៍?",
                "q_en": "How should you send your CV to make a great impression?",
                "a_kh": (
                    "📧 <b>របៀបផ្ញើ CV តាមអ៊ីមែលប្រកបដោយវិជ្ជាជីវៈ៖</b>\n\n"
                    "1️⃣ <b>ទម្រង់ឯកសារ (File Format):</b> ផ្ញើជា <b>PDF</b> ជានិច្ច ដើម្បីកុំឱ្យរត់ទម្រង់ និង Font លើកុំព្យូទ័ររបស់អ្នកដទៃ។\n"
                    "2️⃣ <b>ឈ្មោះឯកសារ (File Naming):</b> ដាក់ឈ្មោះឯកសារឱ្យមានរបៀបរៀបរយ ឧទាហរណ៍៖ <code>CV_Sokha_Chan_Accountant.pdf</code>។\n"
                    "3️⃣ <b>ចំណងជើងអ៊ីមែល (Subject Line):</b> ដាក់ឱ្យច្បាស់លាស់ ឧទាហរណ៍៖ <code>Application for [Job Title] - [Your Full Name]</code>។\n"
                    "4️⃣ <b>ខ្លឹមសារអ៊ីមែល (Email Body):</b> សរសេរសារខ្លីគួរសម ណែនាំខ្លួន មុខតំណែងដែលដាក់ពាក្យ និងភ្ជាប់ឯកសារ។ កុំទុកអ៊ីមែលទទេ!\n"
                    "5️⃣ <b>ពិនិត្យមុនផ្ញើ៖</b> ត្រូវប្រាកដថាបានភ្ជាប់ឯកសារ (Attachment) រួចរាល់មុនចុច Send។"
                ),
                "a_en": (
                    "📧 <b>Professional Email Submission Best Practices:</b>\n\n"
                    "1️⃣ <b>Always Use PDF:</b> Send your CV as a PDF to ensure formatting and fonts render identically on all devices.\n"
                    "2️⃣ <b>Professional File Name:</b> Name your file clearly, e.g., <code>Resume_Firstname_Lastname_Position.pdf</code>.\n"
                    "3️⃣ <b>Clear Subject Line:</b> Follow the employer's instructions or use: <code>Application: [Position Title] - [Full Name]</code>.\n"
                    "4️⃣ <b>Engaging Cover Note:</b> Always write a courteous note in the email body stating who you are, the role applied for, and attached documents.\n"
                    "5️⃣ <b>Double Check Attachments:</b> Ensure all necessary files are attached and error-free before hitting Send."
                ),
            },
        ],
    },
    {
        "id": "general_interview",
        "title_btn": "🎯 គន្លឹះសម្ភាសន៍ទូទៅ",
        "title_kh": "គន្លឹះទូទៅអំពីការសម្ភាសន៍ការងារ",
        "title_en": "General Job Interview Tips",
        "header_kh": "គន្លឹះទូទៅអំពីការសម្ភាសន៍ការងារ (General Job Interview Tips)",
        "positions": [
            "សម្រាប់គ្រប់មុខតំណែង និងគ្រប់កម្រិតការងារ",
        ],
        "questions": [
            {
                "num": 1,
                "label": "សារៈសំខាន់នៃ Cover Letter",
                "q_kh": "តើ Cover Letter សំខាន់ទេ? ហេតុអ្វី?",
                "q_en": "Is a Cover Letter important and why?",
                "a_kh": (
                    "✉️ <b>សារៈសំខាន់នៃ Cover Letter៖</b>\n\n"
                    "<b>សំខាន់ណាស់!</b> Cover Letter គឺជាស្ពានចម្លងដែលភ្ជាប់ CV របស់អ្នកទៅកាន់ចិត្តរបស់អ្នកជ្រើសរើស៖\n"
                    "• <b>បង្ហាញចំណាប់អារម្មណ៍ពិត៖</b> បង្ហាញពីមូលហេតុដែលអ្នកជ្រើសរើសក្រុមហ៊ុននេះ និងការយល់ដឹងពីបេសកកម្មរបស់គេ។\n"
                    "• <b>រំលេចភាពខ្លាំង៖</b> ពន្យល់បន្ថែមពីសមិទ្ធិផលធំៗដែលមិនអាចពន្យល់លម្អិតក្នុង CV។\n"
                    "• <b>បង្ហាញអាកប្បកិរិយា៖</b> បង្ហាញពីភាពក្លៀវក្លា និងសមត្ថភាពក្នុងការប្រាស្រ័យទាក់ទងជាលាយលក្ខណ៍អក្សរ។\n\n"
                    "💡 <b>គន្លឹះ:</b> សរសេរ Cover Letter ថ្មីសម្រាប់ក្រុមហ៊ុននីមួយៗ ដោយកំណត់គោលដៅឱ្យស្របតាមតម្រូវការការងារជាក់ស្តែង!"
                ),
                "a_en": (
                    "✉️ <b>Why a Cover Letter Matters:</b>\n\n"
                    "<b>Crucial!</b> A well-crafted cover letter complements your CV by adding personality and context:\n"
                    "• <b>Demonstrates Genuine Interest:</b> Explains why you want to work for this specific company and how your values align.\n"
                    "• <b>Highlights Achievements:</b> Allows you to elaborate on key milestones that a bulleted CV cannot fully capture.\n"
                    "• <b>Showcases Communication:</b> Acts as an immediate sample of your written communication and professional tone.\n\n"
                    "💡 <b>Tip:</b> Tailor every cover letter to the specific company and role—never send a generic template!"
                ),
            },
            {
                "num": 2,
                "label": "ការត្រៀមខ្លួនមុនសម្ភាស",
                "q_kh": "តើត្រូវរៀបចំខ្លួនយ៉ាងម៉េចខ្លះមុនពេលសម្ភាសន៍?",
                "q_en": "How should you prepare before a job interview?",
                "a_kh": (
                    "🎯 <b>៥ ជំហានរៀបចំខ្លួនមុនសម្ភាសន៍៖</b>\n\n"
                    "1️⃣ <b>ស្រាវជ្រាវពីក្រុមហ៊ុន៖</b> ស្វែងយល់ពីផលិតផល សេវាកម្ម វប្បធម៌ និងព័ត៌មានថ្មីៗរបស់ក្រុមហ៊ុន។\n"
                    "2️⃣ <b>ពិនិត្យការពិពណ៌នាការងារ (JD):</b> មើលឡើងវិញនូវរាល់តម្រូវការ ហើយត្រៀមឧទាហរណ៍ជាក់ស្តែងដែលបង្ហាញពីបទពិសោធន៍របស់អ្នក។\n"
                    "3️⃣ <b>សម្លៀកបំពាក់៖</b> ជ្រើសរើសសម្លៀកបំពាក់បែបវិជ្ជាជីវៈ ស្អាតបាត និងសមរម្យ។\n"
                    "4️⃣ <b>ឯកសារចាំបាច់៖</b> ព្រីន CV ចំនួន ២-៣ ច្បាប់ ប៊ិច និងសៀវភៅកត់ត្រាដាក់តាមខ្លួន។\n"
                    "5️⃣ <b>ពេលវេលា និងផ្លូវធ្វើដំណើរ៖</b> រៀបចំផែនការធ្វើដំណើរដើម្បីទៅដល់មុនម៉ោង ១០-១៥ នាទី។\n\n"
                    "💡 <b>គន្លឹះ:</b> ត្រៀមសំណួរល្អៗ ២-៣ សំណួរ ដើម្បីសួរគណៈកម្មការនៅចុងបញ្ចប់នៃការសម្ភាសន៍!"
                ),
                "a_en": (
                    "🎯 <b>5 Steps to Prepare for an Interview:</b>\n\n"
                    "1️⃣ <b>Research the Company:</b> Learn about their mission, recent news, products/services, and work culture.\n"
                    "2️⃣ <b>Review the Job Description:</b> Map your skills and achievements to each key responsibility in the role.\n"
                    "3️⃣ <b>Professional Attire:</b> Dress appropriately for the industry—err on the side of formal and neat.\n"
                    "4️⃣ <b>Bring Documents:</b> Carry printed copies of your CV, a notebook, and a pen.\n"
                    "5️⃣ <b>Punctuality:</b> Plan your route to arrive 10-15 minutes early (or test your camera/mic early for virtual interviews).\n\n"
                    "💡 <b>Tip:</b> Prepare 2-3 thoughtful questions to ask the interviewer at the end!"
                ),
            },
            {
                "num": 3,
                "label": "សំណួរសម្ភាសដែលជួបញឹកញាប់",
                "q_kh": "តើសំណួរសម្ភាសន៍ណាខ្លះដែលគេសួរញឹកញាប់បំផុត?",
                "q_en": "What are the most common interview questions and how to answer them?",
                "a_kh": (
                    "🗣️ <b>សំណួរពេញនិយម និងវិធីឆ្លើយ៖</b>\n\n"
                    "1️⃣ <b>សូមណែនាំខ្លួនអ្នក?</b>\n"
                    "   👉 ឆ្លើយសង្ខេបពីប្រវត្តិសិក្សា បទពិសោធន៍សំខាន់ៗ និងមូលហេតុដែលអ្នកស្រឡាញ់ការងារនេះ (២-៣ នាទី)។\n\n"
                    "2️⃣ <b>ហេតុអ្វីអ្នកចង់ធ្វើការនៅទីនេះ?</b>\n"
                    "   👉 បង្ហាញការយល់ដឹងពីក្រុមហ៊ុន និងរបៀបដែលគោលដៅរបស់អ្នកស៊ីគ្នានឹងចក្ខុវិស័យរបស់ក្រុមហ៊ុន។\n\n"
                    "3️⃣ <b>ចំណុចខ្លាំង និងចំណុចខ្សោយរបស់អ្នក?</b>\n"
                    "   👉 លើកចំណុចខ្លាំងដែលពាក់ព័ន្ធនឹងការងារ និងចំណុចខ្សោយពិតប្រាកដដែលអ្នកកំពុងអភិវឌ្ឍកែលម្អ។\n\n"
                    "4️⃣ <b>ប្រាប់ពីបញ្ហាដែលអ្នកធ្លាប់ដោះស្រាយ?</b>\n"
                    "   👉 ប្រើរូបមន្ត <b>STAR</b> (Situation = ស្ថានភាព, Task = ភារកិច្ច, Action = សកម្មភាព, Result = លទ្ធផល)។"
                ),
                "a_en": (
                    "🗣️ <b>Common Interview Questions & Strategy:</b>\n\n"
                    "1️⃣ <b>'Tell me about yourself'</b>\n"
                    "   👉 Give a concise 2-minute elevator pitch: present role, past experience highlights, and why this position is the logical next step.\n\n"
                    "2️⃣ <b>'Why do you want to work here?'</b>\n"
                    "   👉 Mention specific values or projects of the company that excite you, showing you did your homework.\n\n"
                    "3️⃣ <b>'What are your strengths and weaknesses?'</b>\n"
                    "   👉 Align strengths with job requirements. For weaknesses, state an honest area of growth and steps you take to improve it.\n\n"
                    "4️⃣ <b>'Tell me about a challenge you overcame'</b>\n"
                    "   👉 Use the <b>STAR method</b>: Situation, Task, Action, and Result."
                ),
            },
            {
                "num": 4,
                "label": "អ្វីដែលគួរធ្វើក្រោយសម្ភាស",
                "q_kh": "តើគួរធ្វើអ្វីខ្លះបន្ទាប់ពីការសម្ភាសន៍ចប់?",
                "q_en": "What should you do after an interview?",
                "a_kh": (
                    "📩 <b>សកម្មភាពគន្លឹះក្រោយសម្ភាសន៍៖</b>\n\n"
                    "1️⃣ <b>ផ្ញើ Thank You Email៖</b> ក្នុងរយៈពេល ២៤ ម៉ោង ផ្ញើអ៊ីមែលអរគុណដល់គណៈកម្មការសម្ភាសន៍ចំពោះពេលវេលា និងឱកាស។\n"
                    "2️⃣ <b>រំលេចចំណុចសំខាន់៖</b> ក្នុងអ៊ីមែល បញ្ជាក់ឡើងវិញនូវចំណាប់អារម្មណ៍ខ្ពស់ចំពោះការងារ និងលើកឡើងពីប្រធានបទគួរឱ្យចាប់អារម្មណ៍ដែលបានជជែក។\n"
                    "3️⃣ <b>រង់ចាំដោយអត់ធ្មត់៖</b> គោរពពេលវេលាដែលខាងក្រុមហ៊ុនបានកំណត់សម្រាប់លទ្ធផល។\n"
                    "4️⃣ <b>Follow-up សមរម្យ៖</b> ប្រសិនបើហួសកាលកំណត់ ១-២ សប្ដាហ៍ដោយគ្មានដំណឹង អាចផ្ញើសារសួរនាំដោយសុភាពរាបសារ។\n"
                    "5️⃣ <b>រៀនសូត្រពីការសម្ភាសន៍៖</b> កត់ត្រាសំណួរពិបាកៗទុក ដើម្បីត្រៀមខ្លួនឱ្យកាន់តែល្អប្រសើរសម្រាប់ពេលក្រោយ។"
                ),
                "a_en": (
                    "📩 <b>Key Post-Interview Steps:</b>\n\n"
                    "1️⃣ <b>Send a Thank-You Email:</b> Within 24 hours, write a brief, polite email thanking the interviewers for their time.\n"
                    "2️⃣ <b>Reiterate Value:</b> Reaffirm your excitement about the position and briefly reference something specific discussed.\n"
                    "3️⃣ <b>Be Patient:</b> Respect the timeline provided by the hiring team.\n"
                    "4️⃣ <b>Polite Follow-up:</b> If the timeline has passed by 1-2 weeks without updates, send a professional follow-up inquiry.\n"
                    "5️⃣ <b>Debrief & Learn:</b> Write down questions that challenged you and refine your answers for future opportunities."
                ),
            },
        ],
    },
]

def get_faq_home_text() -> str:
    """Main FAQ menu message."""
    return (
        f"{tg_emoji(EMOJI_FAQ, '❓')} <b>សំណួរ-ចម្លើយ (FAQ)</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💬 <b>Do you have any questions about career or CV?</b>\n"
        f"តើអ្នកមានចម្ងល់ ឬសំណួរអ្វីខ្លះអំពី <b>Career</b> ឬ <b>CV</b>?\n\n"
        f"📦 <b>សូមជ្រើសរើសផ្នែកខាងក្រោម / Select a Category:</b>"
    )

def build_faq_home_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard for category list (2-column layout)."""
    rows = []
    for i in range(0, len(FAQ_CATEGORIES), 2):
        row = []
        for c_idx in range(i, min(i + 2, len(FAQ_CATEGORIES))):
            row.append(InlineKeyboardButton(
                text=FAQ_CATEGORIES[c_idx]["title_btn"],
                callback_data=f"faq_c_{c_idx}"
            ))
        rows.append(row)
    rows.append([
        InlineKeyboardButton("🔄 ផ្ទុកឡើងវិញ", callback_data="faq_home")
    ])
    return InlineKeyboardMarkup(rows)

def get_faq_category_text(cat_idx: int) -> str:
    """Text for a selected category, listing positions and asking for question."""
    cat = FAQ_CATEGORIES[cat_idx]
    pos_lines = ""
    if cat["positions"]:
        pos_lines = "👔 <b>មុខតំណែង (Positions)៖</b>\n" + "\n".join([f"  • {p}" for p in cat["positions"]]) + "\n\n"
    return (
        f"👍 <b>{cat['header_kh']}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{pos_lines}"
        f"💬 <b>សូមជ្រើសរើសសំណួរ / Select a Question:</b>"
    )

def build_faq_category_keyboard(cat_idx: int) -> InlineKeyboardMarkup:
    """Build question selection keyboard for a category."""
    cat = FAQ_CATEGORIES[cat_idx]
    rows = []
    for q_idx, q in enumerate(cat["questions"]):
        rows.append([
            InlineKeyboardButton(
                text=f"💬 សំណួរ {q['num']} ៖ {q['label']}",
                callback_data=f"faq_q_{cat_idx}_{q_idx}_both"
            )
        ])
    rows.append([
        InlineKeyboardButton("🔙 ត្រឡប់ក្រោយ / Back", callback_data="faq_home")
    ])
    return InlineKeyboardMarkup(rows)

def get_faq_qa_text(cat_idx: int, q_idx: int, lang: str = "both") -> str:
    """Format single question & answer in KH, EN, or BOTH with thorough, detailed responses."""
    cat = FAQ_CATEGORIES[cat_idx]
    qa = cat["questions"][q_idx]

    if lang == "kh":
        return (
            f"<b>{cat['title_kh']}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💬 <b>សំណួរ {qa['num']}៖</b>\n"
            f"<b>{qa['q_kh']}</b>\n\n"
            f"ℹ️ <b>ចម្លើយ៖</b>\n"
            f"{qa['a_kh']}"
        )
    elif lang == "en":
        return (
            f"<b>{cat['title_en']}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💬 <b>Question {qa['num']}:</b>\n"
            f"<b>{qa['q_en']}</b>\n\n"
            f"ℹ️ <b>Answer:</b>\n"
            f"{qa['a_en']}"
        )
    else:  # both
        return (
            f"<b>{cat['title_kh']} / {cat['title_en']}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💬 <b>សំណួរ {qa['num']} / Question {qa['num']}:</b>\n"
            f"🇰🇭 {qa['q_kh']}\n"
            f"🇬🇧 <i>{qa['q_en']}</i>\n\n"
            f"ℹ️ <b>ចម្លើយជាភាសាខ្មែរ៖</b>\n"
            f"{qa['a_kh']}\n\n"
            f"ℹ️ <b>Answer in English:</b>\n"
            f"{qa['a_en']}"
        )

def build_faq_qa_keyboard(cat_idx: int, q_idx: int, current_lang: str) -> InlineKeyboardMarkup:
    """Build language switch buttons and back button for Q&A."""
    lang_row = []
    if current_lang != "kh":
        lang_row.append(InlineKeyboardButton("🇰🇭 ភាសាខ្មែរ", callback_data=f"faq_q_{cat_idx}_{q_idx}_kh"))
    if current_lang != "en":
        lang_row.append(InlineKeyboardButton("🇬🇧 English", callback_data=f"faq_q_{cat_idx}_{q_idx}_en"))
    if current_lang != "both":
        lang_row.append(InlineKeyboardButton("🌐 ទាំងពីរ (Both)", callback_data=f"faq_q_{cat_idx}_{q_idx}_both"))

    return InlineKeyboardMarkup([
        lang_row,
        [InlineKeyboardButton("🔙 បញ្ជីសំណួរ / Questions", callback_data=f"faq_c_{cat_idx}")]
    ])

# បង្កើត Reply Keyboard បង្ហាញនៅខាងក្រោមប្រអប់វាយអក្សរ (Under typing)
reply_keyboard = [
    [
        make_reply_btn("CV & Cover Letter", EMOJI_CV, "✉️"),
        make_reply_btn("គន្លឹះក្នុងការសម្ភាស", EMOJI_INTERVIEW, "📌"),
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
        make_reply_btn("Support Us", EMOJI_SUPPORT or EMOJI_DONATE, "📈"),
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
    "❓ FAQ": {
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
        text=get_faq_home_text(),
        reply_markup=build_faq_home_keyboard(),
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

    elif query.data == "faq_home":
        try:
            await query.edit_message_text(
                text=get_faq_home_text(),
                reply_markup=build_faq_home_keyboard(),
                parse_mode="HTML",
            )
        except BadRequest:
            pass

    elif query.data.startswith("faq_c_"):
        cat_idx = int(query.data.split("_")[2])
        if 0 <= cat_idx < len(FAQ_CATEGORIES):
            try:
                await query.edit_message_text(
                    text=get_faq_category_text(cat_idx),
                    reply_markup=build_faq_category_keyboard(cat_idx),
                    parse_mode="HTML",
                )
            except BadRequest:
                pass

    elif query.data.startswith("faq_q_"):
        parts = query.data.split("_")
        cat_idx = int(parts[2])
        q_idx = int(parts[3])
        lang = parts[4] if len(parts) > 4 else "both"
        if 0 <= cat_idx < len(FAQ_CATEGORIES):
            cat = FAQ_CATEGORIES[cat_idx]
            if 0 <= q_idx < len(cat["questions"]):
                try:
                    await query.edit_message_text(
                        text=get_faq_qa_text(cat_idx, q_idx, lang),
                        reply_markup=build_faq_qa_keyboard(cat_idx, q_idx, lang),
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
                text=get_faq_home_text(),
                reply_markup=build_faq_home_keyboard(),
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
