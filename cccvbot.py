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

# បង្កើត Reply Keyboard បង្ហាញនៅខាងក្រោមប្រអប់វាយអក្សរ (Under typing)
reply_keyboard = [
    [
        KeyboardButton("✉️ CV & Cover Letter"),
        KeyboardButton("💁‍♀️ គន្លឹះក្នុងការសម្ភាស"),
    ],
    [
        KeyboardButton("💼 Career Tip"),
    ],
    [
        KeyboardButton("📢 CareerCenter Channel"),
        KeyboardButton("🛡️ CareerCenter Admin"),
    ],
    [
        KeyboardButton("💝 Support Us"),
    ],
]

menu = ReplyKeyboardMarkup(
    reply_keyboard,
    resize_keyboard=True,
    is_persistent=True,
    input_field_placeholder="ជ្រើសរើស Menu ឬវាយសារ...",
)

QR_IMAGE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qr_donate.png")

# កំណត់ព័ត៌មាន និង Link សម្រាប់ប៊ូតុងនីមួយៗ
BUTTON_ACTIONS = {
    "✉️ CV & Cover Letter": {
        "text": "📄 *CV & Cover Letter*\n\nសូមចុចប៊ូតុងខាងក្រោមដើម្បីចូលទៅកាន់ Channel៖",
        "btn_label": "🔗 ចូលទៅកាន់ CV & Cover Letter",
        "url": URL_CV_CHANNEL,
    },
    "💁‍♀️ គន្លឹះក្នុងការសម្ភាស": {
        "text": "💡 *គន្លឹះក្នុងការសម្ភាសន៍*\n\nសូមចុចប៊ូតុងខាងក្រោមដើម្បីមើលការណែនាំសម្ភាសន៍៖",
        "btn_label": "🔗 ចូលទៅកាន់ គន្លឹះក្នុងការសម្ភាស",
        "url": URL_INTERVIEW_TIP,
    },
    "💁‍♀️ Interview Tip": {
        "text": "💡 *Interview Tip*\n\nសូមចុចប៊ូតុងខាងក្រោមដើម្បីមើលការណែនាំសម្ភាសន៍៖",
        "btn_label": "🔗 ចូលទៅកាន់ Interview Tip",
        "url": URL_INTERVIEW_TIP,
    },
    "💼 Career Tip": {
        "text": "💼 *Career Tip*\n\nសូមចុចប៊ូតុងខាងក្រោមដើម្បីមើលគន្លឹះការងារ៖",
        "btn_label": "🔗 ចូលទៅកាន់ Career Tip",
        "url": URL_CAREER_TIP,
    },
    "📢 CareerCenter Channel": {
        "text": "📢 *Career Center Channel*\n\nសូមចុចប៊ូតុងខាងក្រោមដើម្បីមើលChannel៖",
        "btn_label": "🔗 ចូលទៅកាន់ Career Center Channel",
        "url": URL_CAREER_CHANNEL,
    },
    "🛡️ CareerCenter Admin": {
        "text": "🛡️ *CareerCenter Admin*\n\nសូមចុចប៊ូតុងខាងក្រោមដើម្បីមើលAdmin៖",
        "btn_label": "🔗 ចូលទៅកាន់ CareerCenter Admin",
        "url": URL_ADMIN,
    },
    "❤️ CC Facebook Page": {
        "text": "❤️ *CC Facebook Page*\n\nសូមចុចប៊ូតុងខាងក្រោមដើម្បីចូលទៅកាន់ Facebook Page៖",
        "btn_label": "🔗 ចូលទៅកាន់ Facebook Page",
        "url": URL_FACEBOOK,
    },
    "💝 Support Us": {
        "text": (
            "💝 *Support Us / គាំទ្រពួកយើង*\n\n"
            "សូមជ្រើសរើសជម្រើសខាងក្រោមដើម្បីគាំទ្រ Career Center៖"
        ),
        "inline_keyboard": [
            [
                InlineKeyboardButton(
                    "❤️ CareerCenter Facebook page",
                    url=URL_FACEBOOK,
                )
            ],
            [
                InlineKeyboardButton(
                    "🎵 CareerCenter Tiktok page",
                    url=URL_TIKTOK,
                )
            ],
            [
                InlineKeyboardButton(
                    "💸 Donate us",
                    callback_data="donate_us",
                )
            ],
        ],
    },
    "Support Us": {
        "text": (
            "💝 *Support Us / គាំទ្រពួកយើង*\n\n"
            "សូមជ្រើសរើសជម្រើសខាងក្រោមដើម្បីគាំទ្រ Career Center៖"
        ),
        "inline_keyboard": [
            [
                InlineKeyboardButton(
                    "❤️ CareerCenter Facebook page",
                    url=URL_FACEBOOK,
                )
            ],
            [
                InlineKeyboardButton(
                    "🎵 CareerCenter Tiktok page",
                    url=URL_TIKTOK,
                )
            ],
            [
                InlineKeyboardButton(
                    "💸 Donate us",
                    callback_data="donate_us",
                )
            ],
        ],
    },
    "💝 Donate to Support Us": {
        "photo": QR_IMAGE_PATH,
        "caption": (
            f"💝 *Donate to Support Us*\n\n"
            f"👤 *ឈ្មោះ៖* {DONATE_NAME}\n"
            f"💳 *Wallet KHR៖* `{DONATE_KHR}`\n\n"
            f"💳 *Wallet USD៖* `{DONATE_USD}`\n\n"
            f"សូមស្កេន KHQR ខាងលើដើម្បីឧបត្ថម្ភគាំទ្រ Career Center! សូមអរគុណច្រើន 🙏"
        ),
    },
    "Donate us": {
        "photo": QR_IMAGE_PATH,
        "caption": (
            f"💝 *Donate to Support Us*\n\n"
            f"👤 *ឈ្មោះ៖* {DONATE_NAME}\n"
            f"💳 *Wallet KHR៖* `{DONATE_KHR}`\n\n"
            f"💳 *Wallet USD៖* `{DONATE_USD}`\n\n"
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
            f"ជម្រាបសួរ {user_display} \n\nសូមស្វាគមន៍មកកាន់ Career Center CV Bot! 👋\n\n"
            f"សូមជ្រើសរើស Menu ខាងក្រោម 👇"
        )
    else:
        welcome_text = "សូមស្វាគមន៍! សូមជ្រើសរើស Menu ខាងក្រោម 👇"

    if update.message:
        track_message(context, update.effective_chat.id, update.message.message_id)
    sent = await update.message.reply_text(
        welcome_text,
        reply_markup=menu
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
                        f"💝 *Donate to Support Us*\n\n"
                        f"👤 *ឈ្មោះ៖* {DONATE_NAME}\n"
                        f"💳 *Wallet KHR៖* `{DONATE_KHR}`\n\n"
                        f"💳 *Wallet USD៖* `{DONATE_USD}`\n\n"
                        f"សូមស្កេន KHQR ខាងលើដើម្បីឧបត្ថម្ភគាំទ្រ Career Center! សូមអរគុណច្រើន 🙏"
                    ),
                    parse_mode="Markdown",
                )
                track_message(context, update.effective_chat.id, sent.message_id)
        else:
            sent = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=(
                    f"💝 *Donate to Support Us*\n\n"
                    f"👤 *ឈ្មោះ៖* {DONATE_NAME_ALT}\n"
                    f"💳 *Wallet KHR៖* `{DONATE_KHR_ALT}`"
                ),
                parse_mode="Markdown",
            )
            track_message(context, update.effective_chat.id, sent.message_id)


async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not update.message or not update.message.text:
        return

    track_message(context, update.effective_chat.id, update.message.message_id)
    user_text = update.message.text.strip()

    if user_text in BUTTON_ACTIONS:
        # លុបសារដែល User ចុចប៊ូតុងដើម្បីឱ្យ Chat មើលទៅស្អាត មិនរញ៉េរញ៉ៃ (Auto-delete)
        try:
            await update.message.delete()
        except Exception:
            pass

        action = BUTTON_ACTIONS[user_text]

        # ប្រសិនបើប៊ូតុងមាន sub-buttons (Inline keyboard)
        if "inline_keyboard" in action:
            sent = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=action.get("text", ""),
                reply_markup=InlineKeyboardMarkup(action["inline_keyboard"]),
                parse_mode="Markdown",
            )
            track_message(context, update.effective_chat.id, sent.message_id)
        # ប្រសិនបើប៊ូតុងជាប្រភេទរូបភាព (ឧទាហរណ៍៖ QR Code Donate)
        elif "photo" in action and os.path.exists(action["photo"]):
            with open(action["photo"], "rb") as photo_file:
                sent = await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=photo_file,
                    caption=action.get("caption", ""),
                    parse_mode="Markdown",
                )
                track_message(context, update.effective_chat.id, sent.message_id)
        else:
            inline_btn = None
            if "btn_label" in action and "url" in action:
                inline_btn = InlineKeyboardMarkup([
                    [InlineKeyboardButton(action["btn_label"], url=action["url"])]
                ])
            sent = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=action.get("text", ""),
                reply_markup=inline_btn,
                parse_mode="Markdown",
            )
            track_message(context, update.effective_chat.id, sent.message_id)
    else:
        sent = await update.message.reply_text(
            "សូមជ្រើសរើស Menu ខាងក្រោម 👇",
            reply_markup=menu
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
