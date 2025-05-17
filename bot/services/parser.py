import asyncio
import aiohttp
from bs4 import BeautifulSoup
from bot.services.database import load_sent_links, save_sent_links
from bot.utils.errors import send_error_message
from bot.config import GROUP_CHAT_ID, USER_CHAT_ID
from bot.services.database import load_data, load_sent_links, save_sent_links, add_sent_link

async def notify_about_thanks(bot, master_id, name, link, manager_login, sent_links):
    try:
        # Проверяем, есть ли уже такая ссылка
        if not any(l['url'] == link for l in sent_links['sent_links']):
            message = (f"Найдена благодарность у сотрудника с masterID: {master_id} ({name}). "
                     f"Ссылка на благодарность: {link}. "
                     f"Уведомляем: {manager_login}.")
            await bot.send_message(GROUP_CHAT_ID, message)
            
            # Добавляем новую запись
            from bot.services.database import add_sent_link  # Явный импорт
            await add_sent_link(link, master_id, manager_login, name)
    except Exception as e:
        await send_error_message(bot, f"Не удалось отправить уведомление: {str(e)}")

async def find_text_in_review(session, bot, review_url, employees, semaphore, sent_links):
    async with semaphore:
        full_url = "https://www.banki.ru" + review_url
        try:
            async with session.get(full_url) as response:
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')
                
                ignored_element = soup.find('div', class_="lf4cbd87d ld6d46e58 lb9ca4d21")
                if ignored_element:
                    ignored_element.decompose()

                main_content = soup.find('main', class_="layout-wrapper")
                if main_content:
                    main_text = main_content.get_text()
                    for manager in employees:
                        for employee in manager['employees']:
                            master_id = employee['masterID']
                            name = employee['name']
                            if str(master_id) in main_text:
                                await notify_about_thanks(bot, master_id, name, full_url, manager['telegram_login'], sent_links)
                                break

        except Exception as e:
            await send_error_message(bot, f"Ошибка парсинга {full_url}: {str(e)}")

async def parse_page(session, bot, url, employees, semaphore, sent_links):
    try:
        async with session.get(url) as response:
            text = await response.text()
            soup = BeautifulSoup(text, 'html.parser')
            reviews = soup.find_all('a', href=True)
            review_links = list(set(
                a['href'] for a in reviews 
                if '/services/responses/bank/response/' in a['href']
            ))
            tasks = [
                find_text_in_review(session, bot, review_url, employees, semaphore, sent_links) 
                for review_url in review_links
            ]
            await asyncio.gather(*tasks)
    except Exception as e:
        await send_error_message(bot, f"Ошибка парсинга страницы {url}: {str(e)}")

async def parse_pages(bot, employees, start_page=1, end_page=25):
    try:
        semaphore = asyncio.Semaphore(10)
        sent_links = load_sent_links()
        async with aiohttp.ClientSession() as session:
            tasks = [
                parse_page(
                    session, 
                    bot,
                    f"https://www.banki.ru/services/responses/bank/tcs/?page={page}&type=all",
                    employees,
                    semaphore,
                    sent_links
                ) 
                for page in range(start_page, end_page + 1)
            ]
            await asyncio.gather(*tasks)
    except Exception as e:
        await send_error_message(bot, f"Ошибка парсинга: {str(e)}")

async def schedule_parsing(bot):
    while True:
        try:
            data = await load_data()  
            await bot.send_message(USER_CHAT_ID, "🔍 Начинаем цикл поиска")
            await parse_pages(bot, data["managers"])
            await bot.send_message(USER_CHAT_ID, "✅ Цикл поиска завершен")
        except Exception as e:
            await send_error_message(bot, f"Ошибка в цикле парсинга: {str(e)}")
        await asyncio.sleep(3600)