from flask import Flask, jsonify, render_template_string, request
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
        .card { background: #2a2a2a; max-width: 500px; margin: 0 auto; padding: 20px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
        h1 { color: #00adb5; }
        .info { text-align: left; margin-top: 20px; line-height: 1.6; }
        .label { color: #888; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <h1>Ваш IP: {{ ip }}</h1>
        <div class="info">
            <p><span class="label">Страна:</span> {{ geo.country }}</p>
            <p><span class="label">Регион / Город:</span> {{ geo.regionName }}, {{ geo.city }}</p>
            <p><span class="label">Провайдер (ISP):</span> {{ geo.isp }}</p>
            <p><span class="label">Автономная система (AS):</span> {{ geo.as }}</p>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    # Получаем IP пользователя (учитываем заголовок от прокси, если есть)
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    # Запрашиваем геолокацию для этого IP
    geo_data = {}
    try:
        response = requests.get(f"http://ip-api.com/json/{user_ip}?fields=status,country,regionName,city,isp,as", timeout=5)
        if response.status_code == 200:
            geo_data = response.json()
    except Exception:
        geo_data = {"country": "Не определено", "regionName": "", "city": "", "isp": "Ошибка запроса", "as": ""}

    return render_template_string(HTML_TEMPLATE, ip=user_ip, geo=geo_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
