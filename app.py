from flask import Flask, render_template_string, request
import psycopg2
import os

app = Flask(__name__)

# HTML-шаблоны прямо в коде
INDEX_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>IP Checker</title>
    <style>
        body { background-color: #0d1117; color: #c9d1d9; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background-color: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 40px; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        h1 { color: #58a6ff; margin-bottom: 10px; }
        .ip { font-size: 2em; color: #3fb950; font-weight: bold; margin: 20px 0; }
        a { color: #58a6ff; text-decoration: none; font-weight: bold; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="card">
        <h1>Ваш IP-адрес:</h1>
        <div class="ip">{{ ip }}</div>
        <p><a href="/history">Посмотреть историю визитов →</a></p>
    </div>
</body>
</html>
"""

HISTORY_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>История визитов</title>
    <style>
        body { background-color: #0d1117; color: #c9d1d9; font-family: sans-serif; padding: 40px; display: flex; justify-content: center; }
        .container { width: 100%; max-width: 900px; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        h1 { color: #58a6ff; margin: 0; }
        a { color: #3fb950; text-decoration: none; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; background-color: #161b22; border-radius: 8px; overflow: hidden; border: 1px solid #30363d; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #30363d; }
        th { background-color: #21262d; color: #8b949e; font-size: 0.85em; text-transform: uppercase; }
        tr:hover { background-color: #1c2128; }
        .ip-col { color: #3fb950; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Последние визиты (уникальные IP)</h1>
            <a href="/">← Главная</a>
        </div>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Время (UTC)</th>
                    <th>IP-Адрес</th>
                    <th>User-Agent (Браузер)</th>
                </tr>
            </thead>
            <tbody>
                {% for visit in visits %}
                <tr>
                    <td>{{ loop.index }}</td>
                    <td>{{ visit[1].strftime('%Y-%m-%d %H:%M:%S') }}</td>
                    <td class="ip-col">{{ visit[2] }}</td>
                    <td>{{ visit[3] }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
"""

def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'db'),
        database=os.environ.get('DB_NAME', 'ipcheck_db'),
        user=os.environ.get('DB_USER', 'user'),
        password=os.environ.get('DB_PASSWORD', 'password')
    )
    return conn

@app.route('/')
def index():
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent')

    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS visit (
            id SERIAL PRIMARY KEY,
            ip_address VARCHAR(50),
            user_agent TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    
    cur.execute(
        'INSERT INTO visit (ip_address, user_agent) VALUES (%s, %s)',
        (user_ip, user_agent)
    )
    
    conn.commit()
    cur.close()
    conn.close()

    return render_template_string(INDEX_HTML, ip=user_ip)

@app.route('/history')
def history():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # DISTINCT ON (ip_address) + правильная сортировка ORDER BY ip_address
    cur.execute('''
        SELECT DISTINCT ON (ip_address) id, timestamp, ip_address, user_agent 
        FROM visit 
        ORDER BY ip_address, timestamp DESC 
        LIMIT 20;
    ''')
    
    visits = cur.fetchall()
    cur.close()
    conn.close()

    return render_template_string(HISTORY_HTML, visits=visits)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
