import os
from datetime import datetime
from flask import Flask, render_template_string, request
from flask_sqlalchemy import SQLAlchemy
import requests

app = Flask(__name__)

# Настройка подключения к PostgreSQL из переменных окружения
DB_HOST = os.getenv('DB_HOST', 'db')
DB_NAME = os.getenv('DB_NAME', 'ipcheck_db')
DB_USER = os.getenv('DB_USER', 'user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Модель таблицы в базе данных 🐘
class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Время первого визита этого посетителя
    first_seen = db.Column(db.DateTime, default=datetime.utcnow)
    # Время последнего визита — обновляется при повторном заходе
    last_seen = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ip_address = db.Column(db.String(50), nullable=False)
    user_agent = db.Column(db.String(500), nullable=False)
    # Счётчик визитов этого посетителя
    visit_count = db.Column(db.Integer, default=1)

    # Уникальность по паре (IP, User-Agent) — не даёт создавать дубликаты
    __table_args__ = (
        db.UniqueConstraint('ip_address', 'user_agent', name='uq_ip_useragent'),
    )

# Создаем таблицы при запуске
with app.app_context():
    db.create_all()

# Общие стили для обеих страниц
COMMON_STYLES = """
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: #0b0f0d;
        color: #e0e6e3;
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        padding: 20px;
    }
    .container {
        width: 100%;
        max-width: 800px;
        background: #121815;
        border: 1px solid #1f2e26;
        border-radius: 16px;
        padding: 30px;
        box-shadow: 0 10px 30px rgba(0, 255, 136, 0.05);
    }
    .header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 25px;
        padding-bottom: 15px;
        border-bottom: 1px solid #1f2e26;
    }
    .logo { font-size: 1.1em; font-weight: 700; color: #00ff88; letter-spacing: 1px; text-decoration: none; }
    .nav-link {
        color: #00ff88;
        text-decoration: none;
        font-size: 0.9em;
        font-weight: 600;
        border: 1px solid rgba(0, 255, 136, 0.3);
        padding: 5px 14px;
        border-radius: 20px;
        background-color: rgba(0, 255, 136, 0.1);
        transition: all 0.2s ease;
    }
    .nav-link:hover {
        background-color: rgba(0, 255, 136, 0.2);
    }
"""

INDEX_TEMPLATE = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IP Checker | Dashboard</title>
    <style>
        {COMMON_STYLES}
        .ip-card {{
            background: #17201b;
            border: 1px solid #23352b;
            border-radius: 12px;
            padding: 25px;
            text-align: center;
            margin-bottom: 25px;
        }}
        .ip-title {{ font-size: 0.9em; color: #8b9b92; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }}
        .ip-value {{
            font-size: 2.2em;
            font-weight: 800;
            color: #00ff88;
            text-shadow: 0 0 15px rgba(0, 255, 136, 0.3);
            font-family: monospace;
        }}
        .public-ip-tag {{ margin-top: 8px; font-size: 0.85em; color: #a0b3a8; }}
        .public-ip-tag b {{ color: #e0e6e3; font-family: monospace; }}
        .info-table {{ width: 100%; border-collapse: collapse; }}
        .info-table tr {{ border-bottom: 1px solid #1a2620; }}
        .info-table tr:last-child {{ border-bottom: none; }}
        .info-table td {{ padding: 14px 8px; font-size: 0.95em; }}
        .label-col {{ color: #8b9b92; width: 40%; font-weight: 500; }}
        .value-col {{ color: #e0e6e3; font-weight: 600; text-align: right; }}
        .icon {{ margin-right: 6px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <a href="/" class="logo">🟢 IP CHECKER</a>
            <a href="/history" class="nav-link">📜 История визитов</a>
        </div>

        <div class="ip-card">
            <div class="ip-title">Ваш локальный IP</div>
            <div class="ip-value">{{{{ local_ip }}}}</div>
            <div class="public-ip-tag">Внешний IP: <b>{{{{ public_ip }}}}</b></div>
        </div>

        <table class="info-table">
            <tr>
                <td class="label-col"><span class="icon">🌐</span> Страна</td>
                <td class="value-col">{{{{ geo.country or 'Не определено' }}}}</td>
            </tr>
            <tr>
                <td class="label-col"><span class="icon">🏙️</span> Регион / Город</td>
                <td class="value-col">
                    {{% if geo.regionName or geo.city %}}
                        {{{{ geo.regionName }}}}, {{{{ geo.city }}}}
                    {{% else %}}
                        Не определено
                    {{% endif %}}
                </td>
            </tr>
            <tr>
                <td class="label-col"><span class="icon">📡</span> Провайдер (ISP)</td>
                <td class="value-col">{{{{ geo.isp or 'Не определено' }}}}</td>
            </tr>
            <tr>
                <td class="label-col"><span class="icon">⚙️</span> Автономная система</td>
                <td class="value-col">{{{{ geo.as or 'Не определено' }}}}</td>
            </tr>
        </table>
    </div>
</body>
</html>
"""

HISTORY_TEMPLATE = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IP Checker | История визитов</title>
    <style>
        {COMMON_STYLES}
        .history-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        .history-table th {{
            background: #17201b;
            color: #00ff88;
            text-align: left;
            padding: 12px;
            font-size: 0.85em;
            text-transform: uppercase;
            border-bottom: 2px solid #23352b;
        }}
        .history-table td {{
            padding: 12px;
            font-size: 0.9em;
            border-bottom: 1px solid #1a2620;
        }}
        .ip-badge {{
            font-family: monospace;
            color: #00ff88;
            font-weight: 600;
        }}
        .time-col {{ color: #8b9b92; font-size: 0.85em; white-space: nowrap; }}
        .agent-col {{ color: #a0b3a8; font-size: 0.8em; word-break: break-all; max-width: 300px; }}
        .count-badge {{
            display: inline-block;
            min-width: 22px;
            padding: 2px 6px;
            border-radius: 10px;
            background: rgba(0, 255, 136, 0.15);
            color: #00ff88;
            font-size: 0.8em;
            font-weight: 700;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <a href="/" class="logo">🟢 IP CHECKER</a>
            <a href="/" class="nav-link">🏠 Главная</a>
        </div>

        <h2 style="margin-bottom: 15px; color: #e0e6e3; font-weight: 600;">Уникальные посетители (до 20)</h2>

        <table class="history-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th>Последний визит (UTC)</th>
                    <th>IP-адрес</th>
                    <th>Визитов</th>
                    <th>User-Agent (Браузер)</th>
                </tr>
            </thead>
            <tbody>
                {{% for visit in visits %}}
                <tr>
                    <td style="color: #555;">{{{{ visit.id }}}}</td>
                    <td class="time-col">{{{{ visit.last_seen.strftime('%Y-%m-%d %H:%M:%S') }}}}</td>
                    <td class="ip-badge">{{{{ visit.ip_address }}}}</td>
                    <td><span class="count-badge">{{{{ visit.visit_count }}}}</span></td>
                    <td class="agent-col">{{{{ visit.user_agent }}}}</td>
                </tr>
                {{% else %}}
                <tr>
                    <td colspan="5" style="text-align: center; color: #8b9b92; padding: 20px;">Записей пока нет</td>
                </tr>
                {{% endfor %}}
            </tbody>
        </table>
    </div>
</body>
</html>
"""

def is_local_ip(ip):
    return ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.16.') or ip == '127.0.0.1'

@app.route('/')
def index():
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown')

    # Сохраняем/обновляем визит без дублирования:
    # если такой (IP, User-Agent) уже есть — обновляем время и счётчик,
    # иначе создаём новую запись
    try:
        existing = Visit.query.filter_by(ip_address=user_ip, user_agent=user_agent).first()
        if existing:
            existing.last_seen = datetime.utcnow()
            existing.visit_count = (existing.visit_count or 1) + 1
        else:
            new_visit = Visit(ip_address=user_ip, user_agent=user_agent)
            db.session.add(new_visit)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка БД: {e}")

    geo_data = {}
    public_ip = user_ip

    try:
        if is_local_ip(user_ip):
            url = "http://ip-api.com/json/?fields=status,country,regionName,city,isp,as,query"
        else:
            url = f"http://ip-api.com/json/{user_ip}?fields=status,country,regionName,city,isp,as,query"

        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            geo_data = response.json()
            public_ip = geo_data.get('query', user_ip)
    except Exception:
        geo_data = {}

    return render_template_string(INDEX_TEMPLATE, local_ip=user_ip, public_ip=public_ip, geo=geo_data)

# 📊 Маршрут для просмотра истории визитов (уникальные посетители)
@app.route('/history')
def history():
    # Получаем 20 последних уникальных посетителей, отсортированных по времени последнего визита
    recent_visits = Visit.query.order_by(Visit.last_seen.desc()).limit(20).all()
    return render_template_string(HISTORY_TEMPLATE, visits=recent_visits)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
