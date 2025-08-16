import os
import logging
from fastapi import FastAPI, Request, HTTPException
import uvicorn
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = os.getenv("ADMIN_IDS", "").split(",")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not set!")

# FastAPI app
app = FastAPI()

# Telegram app
tg_app = Application.builder().token(BOT_TOKEN).build()

subscribers = set()

# Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Use /subscribe to receive signals.")

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subscribers.add(update.message.chat_id)
    await update.message.reply_text("✅ You are now subscribed to signals.")

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subscribers.discard(update.message.chat_id)
    await update.message.reply_text("❌ You unsubscribed from signals.")

tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(CommandHandler("subscribe", subscribe))
tg_app.add_handler(CommandHandler("unsubscribe", unsubscribe))

# API endpoint for external signals
@app.post("/signal")
async def send_signal(request: Request):
    if WEBHOOK_SECRET:
        secret = request.headers.get("X-Secret")
        if secret != WEBHOOK_SECRET:
            raise HTTPException(status_code=403, detail="Forbidden")

    data = await request.json()
    pair = data.get("pair")
    direction = data.get("direction")
    expiry = data.get("expiry_minutes")
    note = data.get("note", "")

    message = f"📊 Signal Alert\nPair: {pair}\nDirection: {direction}\nExpiry: {expiry}m\nNote: {note}"

    for chat_id in subscribers:
        try:
            await tg_app.bot.send_message(chat_id=chat_id, text=message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    return {"status": "ok", "sent_to": len(subscribers)}

# Run
if __name__ == "__main__":
    import asyncio

    async def run():
        await tg_app.initialize()
        await tg_app.start()
        config = uvicorn.Config(app, host="0.0.0.0", port=8000)
        server = uvicorn.Server(config)
        await server.serve()
        await tg_app.stop()

    asyncio.run(run())