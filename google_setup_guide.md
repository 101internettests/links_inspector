# Руководство по настройке Google Sheets API

Это подробное руководство поможет вам настроить Google Sheets API для работы с SEO парсером.

## Шаг 1: Создание проекта в Google Cloud Console

1. **Перейдите в Google Cloud Console:**
   - Откройте [https://console.cloud.google.com/](https://console.cloud.google.com/)
   - Войдите в свой Google аккаунт

2. **Создайте новый проект:**
   - Нажмите на выпадающее меню проектов в верхней части страницы
   - Нажмите "New Project"
   - Введите название проекта (например, "SEO Parser")
   - Нажмите "Create"

3. **Выберите созданный проект:**
   - Убедитесь, что ваш новый проект выбран в выпадающем меню

## Шаг 2: Включение Google Sheets API

1. **Перейдите в библиотеку API:**
   - В левом меню найдите "APIs & Services" > "Library"

2. **Найдите Google Sheets API:**
   - В поиске введите "Google Sheets API"
   - Нажмите на "Google Sheets API" в результатах

3. **Включите API:**
   - На странице API нажмите кнопку "Enable"
   - Дождитесь подтверждения включения

## Шаг 3: Создание учетных данных

1. **Перейдите к учетным данным:**
   - В левом меню найдите "APIs & Services" > "Credentials"

2. **Создайте новые учетные данные:**
   - Нажмите "Create Credentials"
   - Выберите "OAuth 2.0 Client IDs"

3. **Настройте OAuth согласие:**
   - Если это первый раз, вам нужно настроить OAuth согласие
   - Выберите "External" (внешний)
   - Заполните обязательные поля:
     - App name: "SEO Parser"
     - User support email: ваш email
     - Developer contact information: ваш email
   - Нажмите "Save and Continue"
   - На следующих экранах нажмите "Save and Continue" (можно пропустить добавление областей)
   - На последнем экране нажмите "Back to Dashboard"

4. **Создайте OAuth 2.0 Client ID:**
   - Вернитесь в "Credentials"
   - Нажмите "Create Credentials" > "OAuth 2.0 Client IDs"
   - Выберите тип приложения "Desktop application"
   - Введите название (например, "SEO Parser Desktop")
   - Нажмите "Create"

5. **Скачайте учетные данные:**
   - После создания появится окно с информацией о клиенте
   - Нажмите "Download JSON"
   - Сохраните файл как `credentials.json` в корне проекта

## Шаг 4: Настройка прав доступа к таблице

1. **Откройте вашу Google таблицу:**
   - Перейдите по ссылке: https://docs.google.com/spreadsheets/d/1NTyI48H4woktkCqnvjGsMOWZbnqs8oCMMNP3j_AJDkw/edit?gid=0#gid=0

2. **Найдите email из учетных данных:**
   - Откройте файл `credentials.json`
   - Найдите поле `client_email` (обычно выглядит как `something@project-id.iam.gserviceaccount.com`)

3. **Предоставьте права доступа:**
   - В таблице нажмите кнопку "Share" (Поделиться) в правом верхнем углу
   - В поле "Add people and groups" введите email из учетных данных
   - Выберите права "Editor"
   - Уберите галочку "Notify people" (если не хотите отправлять уведомление)
   - Нажмите "Share"

## Шаг 5: Проверка настройки

1. **Убедитесь, что файлы на месте:**
   ```
   seo_tests/
   ├── credentials.json    # Учетные данные Google API
   └── config.json         # Конфигурация (создается автоматически)
   ```

2. **Запустите тестовый анализ:**
   ```bash
   python main.py --no-sheets
   ```

3. **Если тест прошел успешно, запустите полный анализ:**
   ```bash
   python main.py
   ```

## Возможные проблемы и решения

### Проблема: "FileNotFoundError: credentials.json"

**Решение:**
- Убедитесь, что файл `credentials.json` находится в корне проекта
- Проверьте правильность названия файла (должно быть точно `credentials.json`)

### Проблема: "Access denied" при работе с таблицей

**Решение:**
- Проверьте, что email из учетных данных имеет права "Editor" на таблицу
- Убедитесь, что ID таблицы в `config.json` правильный

### Проблема: "Google Sheets API not enabled"

**Решение:**
- Вернитесь в Google Cloud Console
- Убедитесь, что Google Sheets API включен в вашем проекте
- Если нет, включите его в "APIs & Services" > "Library"

### Проблема: "Invalid credentials"

**Решение:**
- Удалите файл `token.pickle` (если он существует)
- Перезапустите скрипт
- Пройдите процесс авторизации заново

### Проблема: Браузер не открывается для авторизации

**Решение:**
- Убедитесь, что у вас есть доступ к интернету
- Проверьте, что порт 8080 не занят другими приложениями
- Попробуйте запустить скрипт с правами администратора

## Безопасность

⚠️ **Важные рекомендации по безопасности:**

1. **Не публикуйте учетные данные:**
   - Никогда не коммитьте `credentials.json` в Git
   - Добавьте `credentials.json` и `token.pickle` в `.gitignore`

2. **Ограничьте права доступа:**
   - Предоставляйте минимально необходимые права
   - Регулярно проверяйте список пользователей с доступом к таблице

3. **Мониторинг использования:**
   - Регулярно проверяйте логи использования API в Google Cloud Console
   - Установите квоты, если необходимо

## Дополнительные настройки

### Настройка квот API

1. Перейдите в Google Cloud Console > "APIs & Services" > "Quotas"
2. Найдите "Google Sheets API"
3. Настройте лимиты запросов при необходимости

### Настройка уведомлений

1. Перейдите в Google Cloud Console > "APIs & Services" > "Credentials"
2. Нажмите на ваш OAuth 2.0 Client ID
3. Настройте уведомления о превышении квот

## Поддержка

Если у вас возникли проблемы с настройкой:

1. Проверьте логи в файле `seo_parser.log`
2. Убедитесь, что все шаги выполнены правильно
3. Проверьте документацию Google Sheets API: https://developers.google.com/sheets/api 