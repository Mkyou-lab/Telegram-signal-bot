# Telegram Signal Bot (Cloud Deploy)

## Deploy to Render
1. Fork this repo or upload to your GitHub.
2. Go to Render → New → Blueprint → connect repo.
3. Add Environment Variables:
   - BOT_TOKEN = your bot token
   - ADMIN_IDS = your Telegram ID(s), comma separated
   - WEBHOOK_SECRET = (optional)
4. Deploy 🚀

## Deploy to Railway
1. Create a new project → Deploy from GitHub.
2. Add the same environment variables.
3. Deploy.

## Use
- `/start` → start bot
- `/subscribe` → receive signals
- `/unsubscribe` → stop receiving
- POST signals to `/signal` endpoint with JSON:
```json
{
  "pair": "AUD/USD OTC",
  "direction": "BUY",
  "expiry_minutes": 3,
  "note": "Example reason"
}