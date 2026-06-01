import asyncio
import aiohttp
from telegram import Bot

BOT_TOKEN = "8787982429:AAGpfzIibK7e58YtvAl6g5m1EG2sZtEdFYA"
CHAT_ID = 6318865778

BASE_URL = "https://agropraktika.eu/vacancies"
PAGES = 3
CHECK_INTERVAL = 60

bot = Bot("8787982429:AAGpfzIibK7e58YtvAl6g5m1EG2sZtEdFYA")

# запоминаем состояние страниц
previous_state = {}  # page -> True/False (closed/open)

async def is_registration_closed(html: str) -> bool:
    return "Регистрация временно приостановлена" in html


async def get_state(session):
    state = {}

    for page in range(1, PAGES + 1):
        url = f"{BASE_URL}?page={page}"
        async with session.get(url) as r:
            html = await r.text()
            state[page] = await is_registration_closed(html)

    return state


async def check():
    global previous_state

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                current_state = await get_state(session)

                if not previous_state:
                    previous_state = current_state
                    await asyncio.sleep(CHECK_INTERVAL)
                    continue

                for page in current_state:
                    # было закрыто → стало открыто
                    if previous_state[page] and not current_state[page]:

                        await bot.send_message(
                            chat_id=CHAT_ID,
                            text=f"🚨 РЕГИСТРАЦИЯ ОТКРЫЛАСЬ!\n"
                                 f"Страница: {page}\n"
                                 f"{BASE_URL}?page={page}"
                        )

                previous_state = current_state

            except Exception as e:
                await bot.send_message(chat_id=CHAT_ID, text=f"Ошибка: {e}")

            await asyncio.sleep(CHECK_INTERVAL)


async def main():
    await bot.send_message(chat_id=CHAT_ID, text="✅ Бот запущен")
    await check()


if __name__ == "__main__":
    asyncio.run(main())