import os
import sys
import logging
import requests
import time
import re
from datetime import datetime
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from google_sheets_service_account import GoogleSheetsServiceAccount
from links.links_doc import urls_prod, urls_stage
from config import SPREADSHEET_ID
from telegram_bot import TelegramBot

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ====== НАСТРОЙКИ ======
# Укажи путь к своему сервис-аккаунту и ID таблицы
SERVICE_ACCOUNT_FILE = 'service-account-key.json'
# SPREADSHEET_ID = '1afbfvzPn-SMPkTqPI6nmHv32mcQ3MTG0zu0DPBhCYm8'
SHEET_NAME = 'ПОЛ'  # Имя листа для результатов


# ====== ФУНКЦИИ ======
def analyze_url(url: str) -> Dict[str, Any]:
    """Анализирует страницу: h1-h6, title, description (все и непустые без 'error')."""
    result = {
        'url': url,
        'status': 'error',
        'error': None,
        'headings': {},
        'seo': {},
    }
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Заголовки
        headings = {}
        for i in range(1, 7):
            tag = f'h{i}'
            elements = soup.find_all(tag)
            total = len(elements)
            non_empty = len([el for el in elements if el.get_text(strip=True)])
            headings[f'{tag}_total'] = total
            headings[f'{tag}_non_empty'] = non_empty
        headings['total_headings'] = sum(headings[f'h{i}_non_empty'] for i in range(1, 7))

        # Title
        title_elements = soup.find_all('title')
        title_total = len(title_elements)
        title_non_empty = 0
        for t in title_elements:
            text = (t.get_text() or '').strip()
            if text and not re.search(r'error', text, re.IGNORECASE):
                title_non_empty += 1

        # Description
        description_elements = soup.find_all('meta', attrs={'name': re.compile(r'^description$', re.IGNORECASE)})
        description_total = len(description_elements)
        description_non_empty = 0
        for m in description_elements:
            content = (m.get('content') or '').strip()
            if content and not re.search(r'error', content, re.IGNORECASE):
                description_non_empty += 1

        result['status'] = 'success'
        result['headings'] = headings
        result['seo'] = {
            'title_total': title_total,
            'title_non_empty': title_non_empty,
            'description_total': description_total,
            'description_non_empty': description_non_empty,
        }
    except Exception as e:
        result['error'] = str(e)
        logger.error(f"Ошибка анализа {url}: {e}")
    return result


def compare_headings(prod: Dict[str, Any], stage: Dict[str, Any]) -> Dict[str, Any]:
    """Сравнивает количество заголовков между прод и стейдж, а также title/description (непустые)."""
    comparison = {}
    for i in range(1, 7):
        tag = f'h{i}_non_empty'
        prod_val = prod['headings'].get(tag, 0)
        stage_val = stage['headings'].get(tag, 0)
        comparison[tag] = {'prod': prod_val, 'stage': stage_val, 'diff': stage_val - prod_val}
    comparison['total_headings'] = {
        'prod': prod['headings'].get('total_headings', 0),
        'stage': stage['headings'].get('total_headings', 0),
        'diff': stage['headings'].get('total_headings', 0) - prod['headings'].get('total_headings', 0)
    }
    # Title/Description diffs (по непустым)
    prod_title = prod.get('seo', {}).get('title_non_empty', 0)
    stage_title = stage.get('seo', {}).get('title_non_empty', 0)
    prod_desc = prod.get('seo', {}).get('description_non_empty', 0)
    stage_desc = stage.get('seo', {}).get('description_non_empty', 0)
    comparison['title_non_empty'] = {'prod': prod_title, 'stage': stage_title, 'diff': stage_title - prod_title}
    comparison['description_non_empty'] = {'prod': prod_desc, 'stage': stage_desc, 'diff': stage_desc - prod_desc}
    return comparison


def save_to_google_sheets(results: List[Dict[str, Any]]):
    """Сохраняет результаты в Google Sheets"""
    sheets = GoogleSheetsServiceAccount(SERVICE_ACCOUNT_FILE)
    # Формируем данные для записи
    header = [
        'Дата',
        'Prod URL', 'Stage URL',
        # Headings
        'Prod H1', 'Prod H2', 'Prod H3', 'Prod H4', 'Prod H5', 'Prod H6', 'Prod Total', 'Prod Total All',
        'Stage H1', 'Stage H2', 'Stage H3', 'Stage H4', 'Stage H5', 'Stage H6', 'Stage Total', 'Stage Total All',
        'H1 diff', 'H2 diff', 'H3 diff', 'H4 diff', 'H5 diff', 'H6 diff', 'Total diff',
        # Title
        'Prod Title', 'Prod Title All', 'Stage Title', 'Stage Title All', 'Title diff',
        # Description
        'Prod Description', 'Prod Description All', 'Stage Description', 'Stage Description All', 'Description diff',
        # Errors
        'Prod error', 'Stage error'
    ]
    rows = [header]
    for item in results:
        row = [
            item['date'],
            item['prod_url'],
            item['stage_url'],
            # Headings
            item['prod_h1'],
            item['prod_h2'],
            item['prod_h3'],
            item['prod_h4'],
            item['prod_h5'],
            item['prod_h6'],
            item['prod_total'],
            item['prod_total_all'],
            item['stage_h1'],
            item['stage_h2'],
            item['stage_h3'],
            item['stage_h4'],
            item['stage_h5'],
            item['stage_h6'],
            item['stage_total'],
            item['stage_total_all'],
            item['h1_diff'],
            item['h2_diff'],
            item['h3_diff'],
            item['h4_diff'],
            item['h5_diff'],
            item['h6_diff'],
            item['total_diff'],
            # Title
            item['prod_title'],
            item['prod_title_all'],
            item['stage_title'],
            item['stage_title_all'],
            item['title_diff'],
            # Description
            item['prod_description'],
            item['prod_description_all'],
            item['stage_description'],
            item['stage_description_all'],
            item['description_diff'],
            # Errors
            item['prod_error'],
            item['stage_error'],
        ]
        rows.append(row)
    range_name = f"{SHEET_NAME}!A1"
    sheets.update_sheet(SPREADSHEET_ID, range_name, rows)
    logger.info(f"Результаты записаны в Google Sheets (лист {SHEET_NAME})")


def send_telegram_report(results: List[Dict[str, Any]]):
    """Формирует и отправляет отчёт в Telegram"""
    bot = TelegramBot()
    if not bot.bot_token or not bot.chat_id:
        logger.warning('Не настроен Telegram бот (нет токена или chat_id)')
        return
    total = len(results)
    errors = [r for r in results if r['prod_error'] or r['stage_error']]
    diffs = [
        r for r in results
        if any(r[f'h{i}_diff'] != 0 for i in range(1, 7))
        or r['total_diff'] != 0
        or r.get('title_diff', 0) != 0
        or r.get('description_diff', 0) != 0
    ]
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    msg = f"<b>🌐 ПОЛ СЕО инспектор страниц</b>\n<i>{timestamp}</i>\n\n"
    msg += f"📄 Всего пар: <b>{total}</b>\n"
    msg += f"❌ Ошибок: <b>{len(errors)}</b>\n"
    msg += f"📊 Пар с разницей: <b>{len(diffs)}</b>\n"
    if errors:
        msg += f"\n<b>Ошибки:</b>"
        for r in errors[:10]:
            msg += f"\n- <a href='{r['prod_url']}'>Prod</a> / <a href='{r['stage_url']}'>Stage</a>"
            if r['prod_error']:
                msg += f"\n  Prod error: {r['prod_error']}"
            if r['stage_error']:
                msg += f"\n  Stage error: {r['stage_error']}"
        if len(errors) > 10:
            msg += f"\n...ещё {len(errors)-10} ошибок"
    if diffs:
        msg += f"\n\n<b>Различия:</b>"
        for r in diffs[:10]:
            msg += f"\n- <a href='{r['prod_url']}'>Prod</a> / <a href='{r['stage_url']}'>Stage</a>"
            # Заголовки
            for i in range(1, 7):
                diff = r[f'h{i}_diff']
                if diff != 0:
                    msg += f"\n  H{i} diff: {diff}"
            if r['total_diff'] != 0:
                msg += f"\n  Headings total diff: {r['total_diff']}"
            # Title/Description
            if r.get('title_diff', 0) != 0:
                msg += f"\n  Title diff: {r['title_diff']}"
            if r.get('description_diff', 0) != 0:
                msg += f"\n  Description diff: {r['description_diff']}"
        if len(diffs) > 10:
            msg += f"\n...ещё {len(diffs)-10} с разницей"
        
        # Сводка по типам различий
        h_diffs = sum(1 for r in diffs if any(r[f'h{i}_diff'] != 0 for i in range(1, 7)))
        title_diffs = sum(1 for r in diffs if r.get('title_diff', 0) != 0)
        desc_diffs = sum(1 for r in diffs if r.get('description_diff', 0) != 0)
        msg += f"\n\n<b>Сводка различий:</b>"
        msg += f"\n📊 Пар с разницей по заголовкам: {h_diffs}"
        msg += f"\n📝 Пар с разницей по Title: {title_diffs}"
        msg += f"\n📄 Пар с разницей по Description: {desc_diffs}"
    msg += "\n\n<i> 💥 Ссылка на отчет: https://docs.google.com/spreadsheets/d/1afbfvzPn-SMPkTqPI6nmHv32mcQ3MTG0zu0DPBhCYm8/edit?gid=0#gid=0 </i>"
    msg += "\n\n<i>🤖 Отправлено автоматически</i>"
    bot.send_message(msg)


def main():
    if len(urls_prod) != len(urls_stage):
        logger.error('Списки urls_prod и urls_stage должны быть одинаковой длины!')
        sys.exit(1)
    results = []
    for prod_url, stage_url in zip(urls_prod, urls_stage):
        logger.info(f"Проверяю пару:\n  PROD: {prod_url}\n  STAGE: {stage_url}")
        prod_result = analyze_url(prod_url)
        stage_result = analyze_url(stage_url)
        comparison = compare_headings(prod_result, stage_result)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        results.append({
            'date': now,
            'prod_url': prod_url,
            'stage_url': stage_url,
            # Headings
            'prod_h1': prod_result['headings'].get('h1_non_empty', 0),
            'prod_h2': prod_result['headings'].get('h2_non_empty', 0),
            'prod_h3': prod_result['headings'].get('h3_non_empty', 0),
            'prod_h4': prod_result['headings'].get('h4_non_empty', 0),
            'prod_h5': prod_result['headings'].get('h5_non_empty', 0),
            'prod_h6': prod_result['headings'].get('h6_non_empty', 0),
            'prod_total': prod_result['headings'].get('total_headings', 0),
            'prod_total_all': sum(prod_result['headings'].get(f'h{i}_total', 0) for i in range(1, 7)),
            'stage_h1': stage_result['headings'].get('h1_non_empty', 0),
            'stage_h2': stage_result['headings'].get('h2_non_empty', 0),
            'stage_h3': stage_result['headings'].get('h3_non_empty', 0),
            'stage_h4': stage_result['headings'].get('h4_non_empty', 0),
            'stage_h5': stage_result['headings'].get('h5_non_empty', 0),
            'stage_h6': stage_result['headings'].get('h6_non_empty', 0),
            'stage_total': stage_result['headings'].get('total_headings', 0),
            'stage_total_all': sum(stage_result['headings'].get(f'h{i}_total', 0) for i in range(1, 7)),
            'h1_diff': comparison['h1_non_empty']['diff'],
            'h2_diff': comparison['h2_non_empty']['diff'],
            'h3_diff': comparison['h3_non_empty']['diff'],
            'h4_diff': comparison['h4_non_empty']['diff'],
            'h5_diff': comparison['h5_non_empty']['diff'],
            'h6_diff': comparison['h6_non_empty']['diff'],
            'total_diff': comparison['total_headings']['diff'],
            # Title
            'prod_title': prod_result['seo'].get('title_non_empty', 0),
            'prod_title_all': prod_result['seo'].get('title_total', 0),
            'stage_title': stage_result['seo'].get('title_non_empty', 0),
            'stage_title_all': stage_result['seo'].get('title_total', 0),
            'title_diff': comparison['title_non_empty']['diff'],
            # Description
            'prod_description': prod_result['seo'].get('description_non_empty', 0),
            'prod_description_all': prod_result['seo'].get('description_total', 0),
            'stage_description': stage_result['seo'].get('description_non_empty', 0),
            'stage_description_all': stage_result['seo'].get('description_total', 0),
            'description_diff': comparison['description_non_empty']['diff'],
            # Errors
            'prod_error': prod_result['error'],
            'stage_error': stage_result['error'],
        })
        time.sleep(1)  # чтобы не спамить запросами
    save_to_google_sheets(results)
    send_telegram_report(results)
    print('Готово!')


if __name__ == '__main__':
    main() 