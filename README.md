# BlagaTGBotv2

Бот для автоматизации управления ID и мониторинга отзывов.

### Основные функции
#### 🛠 Управление сотрудниками:
- Добавление/удаление ID
-Редактирование данных (имя, ID)
- Иерархия "Группа ID → ID"
#### 🔔 Автоматический парсинг:
- Ежечасная проверка новых отзывов
- Умный фильтр упоминаний ID
- Автоуведомления в групповой чат (TG)
#### ⚙️ Технологии:
- Python 3.10+
- Aiogram
- AioHTTP + BeautifulSoup 
- JSON-хранилище данных

### Установка

1. Клонировать репозиторий:
```
git clone https://github.com/Blaseend/BlagaTGBotv2.git
```

2. Установить зависимости:
```
pip install -r requirements.txt
```

3. Настроить конфигурацию:
```
# bot/config.py
API_TOKEN = 'ВАШ_TELEGRAM_BOT_TOKEN'
GROUP_CHAT_ID = 'ID_ГРУППОВОГО_ЧАТА'
USER_CHAT_ID = 'ID_АДМИНИСТРАТОРА'
```

4. Запуск бота:
```
python main.py
```

----------------------------

Проект распространяется под лицензией MIT.

```
Copyright 2025 Blaseend

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```
