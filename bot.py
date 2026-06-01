import asyncio
import aiohttp
from telegram import Bot

BOT_TOKEN = "YOUR_TOKEN"
CHAT_ID = 6318865778

BASE_URL = "https://agropraktika.eu/vacancies"
PAGES = 3
CHECK_INTERVAL = 60

bot = Bot(token=BOT_TOKEN)

previous_state = {}

async def is_closed(html: str) -> bool:
    return "Регистрация временно приостановлена" in html


async def get_page_state(session, page):
    url = f"{BASE_URL}?page={page}"

    try:
        async with session.get(url) as r:

            # 🔴 403 — НЕ ДЕЛАЕМ ВЫВОДОВ
            if r.status == 403:
                print(f"403 на странице {page} — пропуск")
                return None

            html = await r.text()
            return is_closed(html)

    except Exception as e:
        print(f"Ошибка страницы {page}: {e}")
        return None


async def get_state(session):
    state = {}

    for page in range(1, PAGES + 1):
        result = await get_page_state(session, page)

        # если 403 или ошибка — просто пропускаем страницу
        if result is None:
            continue

        state[page] = result

    return state


async def check():
    global previous_state

    async with aiohttp.ClientSession() as session:
        while True:
            current_state = await get_state(session)

            # если нет данных — просто ждём следующий цикл
            if not current_state:
                await asyncio.sleep(CHECK_INTERVAL)
                continue

            # первый запуск
            if not previous_state:
                previous_state = current_state
                await asyncio.sleep(CHECK_INTERVAL)
                continue

            for page in current_state:

                # 🔥 главное условие: было закрыто → стало открыто
                if (
                    page in previous_state
                    and previous_state[page] == True
                    and current_state[page] == False
                ):
                    await bot.send_message(
                        chat_id=CHAT_ID,
                        text=(
                            f"🚨 ВАКАНСИЯ ОТКРЫЛАСЬ!\n"
                            f"Страница: {page}\n"
                            f"{BASE_URL}?page={page}"
                        )
                    )

            # обновляем только валидные данные
            previous_state.update(current_state)

            await asyncio.sleep(CHECK_INTERVAL)


async def main():
    await bot.send_message(chat_id=CHAT_ID, text="✅ Бот запущен и отслеживает вакансии")
    await check()


if __name__ == "__main__":
    asyncio.run(main())