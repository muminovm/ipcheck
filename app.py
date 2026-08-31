from flask import Flask, render_template_string, request
import requests

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>IP Checker</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #1a1a1a; color: #fff; text-align: center; padding-top: 50px; }
        .card { background: #2a2a2a; max-width: 500px; margin: 0 auto; padding: 25px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
        h1 { color: #00adb5; margin-bottom: 5px; }
        .subtitle { color: #aaa; margin-top: 0; font-size: 0.9em; }
        .info { text-align: left; margin-top: 20px; line-height: 1.8; }
        .label { color: #888; font-weight: bold; }
        .badge { background: #00adb5; color: #fff; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; }
    </style>
</head>
<body>
    <div class="card">
        <h1>Ваш локальный IP: {{ local_ip }}</h1>
        <p class="subtitle">Внешний IP (Сеть): <b>{{ public_ip }}</b> <span class="badge">Public</span></p>
        
        <div class="info">
            <p><span class="label">Страна: 🌐</span> {{ geo.country }}</p>
            <p><span class="label">Регион / Город: 🏙️</span> {{ geo.regionName }}, {{ geo.city }}</p>
            <p><span class="label">Провайдер (ISP): 📡</span> {{ geo.isp }}</p>
            <p><span class="label">Автономная система (AS): ⚙️</span> {{ geo.as }}</p>
        </div>
    </div>
</body>
</html>
"""

def is_local_ip(ip):
    # Проверка на приватные диапазоны IP
    return ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.16.') or ip == '127.0.0.1'

@app.route('/')
def index():
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    geo_data = {}
    public_ip = user_ip

    try:
        # Если клиент зашел из локальной сети, делаем запрос без IP
        # Тогда ip-api.com вернет публичный IP самого сервера
        if is_local_ip(user_ip):
            url = "http://ip-api.com/json/?fields=status,country,regionName,city,isp,as,query"
        else:
            url = f"http://ip-api.com/json/{user_ip}?fields=status,country,regionName,city,isp,as,query"

        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            geo_data = response.json()
            public_ip = geo_data.get('query', user_ip)
    except Exception:
        geo_data = {"country": "Не определено", "regionName": "", "city": "", "isp": "Ошибка запроса", "as": ""}

    return render_template_string(HTML_TEMPLATE, local_ip=user_ip, public_ip=public_ip, geo=geo_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
