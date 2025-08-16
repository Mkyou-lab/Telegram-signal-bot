import os
import logging
from fastapi import FastAPI, Request, HTTPException
import uvicorn
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is required")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()
scheduler = AsyncIOScheduler()
subscribers = set()

# --- Telegram handlers ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Welcome! Use /subscribe to get signals.")

@dp.message(Command("subscribe"))
async def subscribe_cmd(message: types.Message):
    subscribers.add(message.chat.id)
    await message.answer("You are now subscribed to signals ✅")

@dp.message(Command("unsubscribe"))
async def unsubscribe_cmd(message: types.Message):
    subscribers.discard(message.chat.id)
    await message.answer("You are now unsubscribed ❌")

# --- FastAPI webhook ---
@app.post("/signal")
async def signal_endpoint(request: Request):
    if WEBHOOK_SECRET:
        secret = request.headers.get("X-Secret")
        if secret != WEBHOOK_SECRET:
            raise HTTPException(status_code=403, detail="Invalid secret")

    data = await request.json()
    pair = data.get("pair")
    direction = data.get("direction")
    expiry = data.get("expiry_minutes")
    note = data.get("note", "")

    if not pair or not direction or not expiry:
        raise HTTPException(status_code=400, detail="Missing fields")

    text = f"📊 Signal\nPair: {pair}\nDirection: {direction}\nExpiry: {expiry}m\nNote: {note}"
    for chat_id in subscribers:
        try:
            await bot.send_message(chat_id, text)
        except Exception as e:
            logging.error(f"Failed to send to {chat_id}: {e}")

    return {"status": "ok"}

# --- Startup ---
@app.on_event("startup")
async def on_startup():
    scheduler.start()
    import asyncio
    asyncio.create_task(dp.start_polling(bot))

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))