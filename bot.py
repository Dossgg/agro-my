import asyncio
import aiohttp
import os
from telegram import Bot
from datetime import datetime

# =====================
# ENV (Railway)
# =====================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise Exception("❌ Нет BOT_TOKEN или CHAT_ID в переменных Railway")

CHAT_ID = int(CHAT_ID)

# =====================
# CONFIG
# =====================

BASE_URL = "https://agropraktika.eu/vacancies"
CHECK_INTERVAL = 60

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "ru-RU,ru;q=0.9"
}

bot = Bot(token=BOT_TOKEN)

previous_status = {}

# =====================
# LOG
# =====================

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

# =====================
# FETCH (anti 403 retry)
# =====================

async def fetch(session):
    url = BASE_URL

    for attempt in range(3):
        try:
            async with session.get(url, headers=HEADERS, timeout=20) as r:

                if r.status == 403:
                    log(f"403 получен, попытка {attempt+1}/3 → жду 120 сек")
                    await asyncio.sleep(120)
                    continue

                if r.status != 200:
                    log(f"HTTP ошибка: {r.status}")
                    return None

                return await r.text()

        except Exception as e:
            log(f"Ошибка запроса: {e}")
            await asyncio.sleep(10)

    return None

# =====================
# STATUS CHECK
# =====================

def is_closed(html):
    return "регистрация временно приостановлена" in html.lower()

# =====================
# LOOP
# =====================

async def loop():
    global previous_status

    async with aiohttp.ClientSession() as session:

        await bot.send_message(CHAT_ID, "🤖 Бот запущен")

        while True:
            try:
                html = await fetch(session)

                if not html:
                    await asyncio.sleep(CHECK_INTERVAL)
                    continue

                closed = is_closed(html)
                prev = previous_status.get("main")

                # ОТКРЫЛОСЬ
                if prev is True and closed is False:
                    log("🔥 РЕГИСТРАЦИЯ ОТКРЫЛАСЬ")

                    await bot.send_message(
                        CHAT_ID,
                        f"🚨 РЕГИСТРАЦИЯ ОТКРЫЛАСЬ!\n{BASE_URL}"
                    )

                previous_status["main"] = closed

                log("проверка завершена")

            except Exception as e:
                log(f"Критическая ошибка: {e}")

            await asyncio.sleep(CHECK_INTERVAL)

# =====================
# START
# =====================

async def main():
    await loop()

if __name__ == "__main__":
    asyncio.run(main())