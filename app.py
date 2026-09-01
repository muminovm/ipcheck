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

# Модель таблицы в базе данных
class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(50), nullable=False)
    user_agent = db.Column(db.String(500), nullable=False)

# Создаем таблицы в базе данных при запуске
with app.app_context():
    db.create_all()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IP Checker | Dashboard</title>
    <style>
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
            max-width: 650px;
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
        .logo { font-size: 1.1em; font-weight: 700; color: #00ff88; letter-spacing: 1px; }
        .status-badge {
            background-color: rgba(0, 255, 136, 0.1);
            color: #00ff88;
            border: 1px solid rgba(0, 255, 136, 0.3);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
        }
        .ip-card {
            background: #17201b;
            border: 1px solid #23352b;
            border-radius: 12px;
            padding: 25px;
            text-align: center;
            margin-bottom: 25px;
        }
        .ip-title { font-size: 0.9em; color: #8b9b92; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
        .ip-value {
            font-size: 2.2em;
            font-weight: 800;
            color: #00ff88;
            text-shadow: 0 0 15px rgba(0, 255, 136, 0.3);
            font-family: monospace;
        }
        .public-ip-tag { margin-top: 8px; font-size: 0.85em; color: #a0b3a8; }
        .public-ip-tag b { color: #e0e6e3; font-family: monospace; }
        .info-table { width: 100%; border-collapse: collapse; }
        .info-table tr { border-bottom: 1px solid #1a2620; }
        .info-table tr:last-child { border-bottom: none; }
        .info-table td { padding: 14px 8px; font-size: 0.95em; }
        .label-col { color: #8b9b92; width: 40%; font-weight: 500; }
        .value-col { color: #e0e6e3; font-weight: 600; text-align: right; }
        .icon { margin-right: 6px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🟢 IP CHECKER</div>
            <div class="status-badge">● ONLINE</div>
        </div>

        <div class="ip-card">
            <div class="ip-title">Ваш локальный IP</div>
            <div class="ip-value">{{ local_ip }}</div>
            <div class="public-ip-tag">Внешний IP: <b>{{ public_ip }}</b></div>
        </div>

        <table class="info-table">
            <tr>
                <td class="label-col"><span class="icon">🌐</span> Страна</td>
                <td class="value-col">{{ geo.country or 'Не определено' }}</td>
            </tr>
            <tr>
                <td class="label-col"><span class="icon">🏙️</span> Регион / Город</td>
                <td class="value-col">
                    {% if geo.regionName or geo.city %}
                        {{ geo.regionName }}, {{ geo.city }}
                    {% else %}
                        Не определено
                    {% endif %}
                </td>
            </tr>
            <tr>
                <td class="label-col"><span class="icon">📡</span> Провайдер (ISP)</td>
                <td class="value-col">{{ geo.isp or 'Не определено' }}</td>
            </tr>
            <tr>
                <td class="label-col"><span class="icon">⚙️</span> Автономная система</td>
                <td class="value-col">{{ geo.as or 'Не определено' }}</td>
            </tr>
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
    
    # Сохраняем информацию о визите в БД PostgreSQL 🐘
    try:
        new_visit = Visit(ip_address=user_ip, user_agent=user_agent)
        db.session.add(new_visit)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка записи в БД: {e}")

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

    return render_template_string(HTML_TEMPLATE, local_ip=user_ip, public_ip=public_ip, geo=geo_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
