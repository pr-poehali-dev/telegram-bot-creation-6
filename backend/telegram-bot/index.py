'''
Business: Telegram webhook handler for P2P crypto exchange bot
Args: event - dict with httpMethod, body (JSON from Telegram), queryStringParameters
      context - object with attributes: request_id, function_name
Returns: HTTP response dict with statusCode, headers, body
'''

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection
def get_db_connection():
    dsn = os.environ.get('DATABASE_URL')
    return psycopg2.connect(dsn, cursor_factory=RealDictCursor)

# User management
def get_or_create_user(telegram_user: Dict[str, Any]) -> Dict[str, Any]:
    conn = get_db_connection()
    cur = conn.cursor()
    
    telegram_id = telegram_user.get('id')
    username = telegram_user.get('username', '')
    first_name = telegram_user.get('first_name', '')
    last_name = telegram_user.get('last_name', '')
    
    cur.execute(
        "SELECT * FROM users WHERE telegram_id = %s",
        (telegram_id,)
    )
    user = cur.fetchone()
    
    if not user:
        cur.execute(
            """INSERT INTO users (telegram_id, username, first_name, last_name) 
               VALUES (%s, %s, %s, %s) RETURNING *""",
            (telegram_id, username, first_name, last_name)
        )
        user = cur.fetchone()
        conn.commit()
    
    cur.close()
    conn.close()
    return dict(user)

# Send message to Telegram
def send_telegram_message(chat_id: int, text: str, reply_markup: Optional[Dict] = None):
    import urllib.request
    
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    
    data = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    
    if reply_markup:
        data['reply_markup'] = reply_markup
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    urllib.request.urlopen(req)

# Main menu keyboard
def get_main_menu_keyboard():
    return {
        'keyboard': [
            [{'text': '📋 Объявления'}, {'text': '➕ Создать объявление'}],
            [{'text': '💼 Мои сделки'}, {'text': '👤 Профиль'}],
            [{'text': '💬 Поддержка'}]
        ],
        'resize_keyboard': True
    }

# Handle /start command
def handle_start(chat_id: int, user_data: Dict):
    get_or_create_user(user_data)
    welcome_text = f"""👋 Добро пожаловать в P2P обменник!

Здесь вы можете безопасно покупать и продавать криптовалюту напрямую с другими пользователями.

🔐 Все сделки защищены эскроу-системой
⭐ Рейтинг и отзывы продавцов
💬 Встроенный чат для каждой сделки

Выберите действие из меню ниже:"""
    
    send_telegram_message(chat_id, welcome_text, get_main_menu_keyboard())

# Handle advertisements list
def handle_advertisements_list(chat_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT a.*, u.username, u.rating, u.total_deals 
        FROM advertisements a
        JOIN users u ON a.seller_telegram_id = u.telegram_id
        WHERE a.status = 'active'
        ORDER BY a.created_at DESC
        LIMIT 10
    """)
    
    ads = cur.fetchall()
    cur.close()
    conn.close()
    
    if not ads:
        send_telegram_message(chat_id, "📋 Пока нет активных объявлений", get_main_menu_keyboard())
        return
    
    text = "📋 <b>Активные объявления:</b>\n\n"
    
    for ad in ads:
        text += f"💰 <b>{ad['currency_type']}</b>\n"
        text += f"Количество: {ad['amount']}\n"
        text += f"Цена: {ad['price_per_unit']} руб/ед\n"
        text += f"Продавец: @{ad['username']} ⭐{ad['rating']} ({ad['total_deals']} сделок)\n"
        if ad['description']:
            text += f"📝 {ad['description']}\n"
        text += f"ID: {ad['id']}\n\n"
    
    text += "\nДля покупки отправьте: /buy [ID объявления] [количество]"
    
    send_telegram_message(chat_id, text, get_main_menu_keyboard())

# Handle create advertisement
def handle_create_ad_start(chat_id: int):
    text = """➕ <b>Создание объявления</b>

Отправьте данные в формате:
/create_ad [валюта] [количество] [цена за единицу]

Пример:
/create_ad USDT 1000 95.50"""
    
    send_telegram_message(chat_id, text, get_main_menu_keyboard())

# Handle user profile
def handle_profile(chat_id: int, telegram_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,))
    user = cur.fetchone()
    
    if not user:
        send_telegram_message(chat_id, "❌ Профиль не найден", get_main_menu_keyboard())
        return
    
    text = f"""👤 <b>Ваш профиль</b>

Имя: {user['first_name']}
Username: @{user['username'] or 'не указан'}
⭐ Рейтинг: {user['rating']}/5.00
📊 Всего сделок: {user['total_deals']}
✅ Успешных: {user['successful_deals']}
📅 Регистрация: {user['created_at'].strftime('%d.%m.%Y')}"""
    
    cur.close()
    conn.close()
    
    send_telegram_message(chat_id, text, get_main_menu_keyboard())

# Handle my deals
def handle_my_deals(chat_id: int, telegram_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT d.*, a.currency_type 
        FROM deals d
        JOIN advertisements a ON d.advertisement_id = a.id
        WHERE d.buyer_telegram_id = %s OR d.seller_telegram_id = %s
        ORDER BY d.created_at DESC
        LIMIT 10
    """, (telegram_id, telegram_id))
    
    deals = cur.fetchall()
    cur.close()
    conn.close()
    
    if not deals:
        send_telegram_message(chat_id, "💼 У вас пока нет сделок", get_main_menu_keyboard())
        return
    
    text = "💼 <b>Ваши сделки:</b>\n\n"
    
    for deal in deals:
        role = "Покупатель" if deal['buyer_telegram_id'] == telegram_id else "Продавец"
        status_emoji = {
            'created': '🆕',
            'paid': '💳',
            'disputed': '⚠️',
            'completed': '✅',
            'cancelled': '❌'
        }
        
        text += f"{status_emoji.get(deal['status'], '❓')} <b>Сделка #{deal['id']}</b>\n"
        text += f"Роль: {role}\n"
        text += f"Валюта: {deal['currency_type']}\n"
        text += f"Сумма: {deal['amount']}\n"
        text += f"Статус: {deal['status']}\n"
        text += f"Эскроу: {deal['escrow_status']}\n\n"
    
    text += "\nДля просмотра сделки: /deal [ID]"
    
    send_telegram_message(chat_id, text, get_main_menu_keyboard())

# Handle support
def handle_support(chat_id: int):
    text = """💬 <b>Поддержка</b>

Для создания обращения отправьте:
/support [тема] [описание проблемы]

Пример:
/support Проблема со сделкой #123 Продавец не отвечает

Мы ответим в ближайшее время!"""
    
    send_telegram_message(chat_id, text, get_main_menu_keyboard())

# Main handler
def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method: str = event.get('httpMethod', 'POST')
    
    # Handle CORS OPTIONS
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '86400'
            },
            'body': ''
        }
    
    if method != 'POST':
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    # Parse Telegram update
    body_str = event.get('body', '{}')
    update = json.loads(body_str)
    
    # Extract message data
    message = update.get('message', {})
    chat_id = message.get('chat', {}).get('id')
    text = message.get('text', '')
    user = message.get('from', {})
    telegram_id = user.get('id')
    
    if not chat_id:
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'ok': True})
        }
    
    # Route commands
    if text == '/start':
        handle_start(chat_id, user)
    elif text == '📋 Объявления' or text == '/ads':
        handle_advertisements_list(chat_id)
    elif text == '➕ Создать объявление' or text == '/new_ad':
        handle_create_ad_start(chat_id)
    elif text == '👤 Профиль' or text == '/profile':
        handle_profile(chat_id, telegram_id)
    elif text == '💼 Мои сделки' or text == '/deals':
        handle_my_deals(chat_id, telegram_id)
    elif text == '💬 Поддержка' or text == '/help':
        handle_support(chat_id)
    else:
        send_telegram_message(
            chat_id, 
            "Используйте меню для навигации или команды /start",
            get_main_menu_keyboard()
        )
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({'ok': True})
    }
