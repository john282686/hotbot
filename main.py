import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from huggingface_hub import HfApi, create_repo

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
HF_TOKEN = os.environ["HF_TOKEN"]
HF_USERNAME = os.environ["HF_USERNAME"]
OWNER_TELEGRAM_ID = int(os.environ.get("OWNER_TELEGRAM_ID", "0"))
PORT = int(os.environ.get("PORT", 8080))

api = HfApi(token=HF_TOKEN)

def is_owner(update):
    return update.effective_user.id == OWNER_TELEGRAM_ID

async def start(update, ctx):
    await update.message.reply_text(
        "🤖 Host Bot Controller\n\n"
        "/new <name> — create a hosting space\n"
        "/list — list your spaces\n"
        "/delete <name> — delete a space\n"
        "/id — get your Telegram ID"
    )

async def new_space(update, ctx):
    if not is_owner(update):
        return await update.message.reply_text("Not authorized.")
    if not ctx.args:
        return await update.message.reply_text("Usage: /new <name>")
    name = ctx.args[0].lower().replace("_", "-")
    full = f"{HF_USERNAME}/{name}"
    try:
        create_repo(repo_id=full, repo_type="space", space_sdk="docker", private=False, token=HF_TOKEN)
        await update.message.reply_text(f"Space created: {full}\nhttps://huggingface.co/spaces/{full}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def list_spaces(update, ctx):
    if not is_owner(update):
        return await update.message.reply_text("Not authorized.")
    try:
        spaces = api.list_spaces(author=HF_USERNAME)
        lines = ["Your Spaces:"]
        for s in spaces:
            stage = s.runtime.stage if s.runtime else 'unknown'
            lines.append(f"- {s.id} — {stage}")
        await update.message.reply_text("\n".join(lines))
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def delete_space(update, ctx):
    if not is_owner(update):
        return await update.message.reply_text("Not authorized.")
    if not ctx.args:
        return await update.message.reply_text("Usage: /delete <name>")
    full = f"{HF_USERNAME}/{ctx.args[0]}"
    try:
        api.delete_repo(repo_id=full, repo_type="space", token=HF_TOKEN)
        await update.message.reply_text(f"Deleted {full}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def get_id(update, ctx):
    await update.message.reply_text(f"Your ID: {update.effective_user.id}")

def main():
    log.info("Starting Host Bot...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("new", new_space))
    app.add_handler(CommandHandler("list", list_spaces))
    app.add_handler(CommandHandler("delete", delete_space))
    app.add_handler(CommandHandler("id", get_id))
    log.info("Bot running.")
    app.run_polling()

if __name__ == "__main__":
    main()
