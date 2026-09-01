from flask import Flask, render_template_string, request
import psycopg2
import os

app = Flask(__name__)

INDEX_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IP CHECKER</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            background-color: #0b0f19; 
            color: #9ca3af; 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            min-height: 100vh; 
        }
        .card { 
            background-color: #111827; 
            border: 1px solid #1f2937; 
            border-radius: 12px; 
            padding: 40px; 
            text-align: center; 
            box-shadow: 0 0 25px rgba(16, 185, 129, 0.15); 
            max-width: 450px;
            width: 100%;
        }
        .header-title {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            font-size: 1.2rem;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 25px;
            letter-spacing: 1px;
        }
        .dot {
            width: 10px;
            height: 10px;
            background-color: #10b981;
            border-radius: 50%;
            box-shadow: 0 0 10px #10b981;
        }
        h1 { color: #9ca3af; font-size: 1rem; font-weight: 500; margin-bottom: 10px; }
        .ip { 
            font-size: 2.2rem; 
            color: #10b981; 
            font-weight: 700; 
            margin: 15px 0 30px 0; 
            text-shadow: 0 0 12px rgba(16, 185, 129, 0.4);
            font-family: monospace;
        }
        .btn { 
            display: inline-block;
            background-color: #064e3b; 
            color: #34d399; 
            border: 1px solid #059669;
            padding: 10px 20px;
            border-radius: 8px;
            text-decoration: none; 
            font-weight: 600; 
            transition: all 0.2s ease;
        }
        .btn:hover { 
            background-color: #059669; 
            color: #ffffff;
            box-shadow: 0 0 15px rgba(16, 185, 129, 0.4);
        }
    </style>
</head>
<body>
    <div class="card">
        <div class="header-title">
            <span class="dot"></span> IP CHECKER
        </div>
        <h1>Ваш текущий IP-адрес:</h1>
        <div class="ip">{{ ip }}</div>
        <a href="/history" class="btn">История визитов →</a>
    </div>
</body>
</html>
"""

HISTORY_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IP CHECKER - Последние визиты</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            background-color: #0b0f19; 
            color: #9ca3af; 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            padding: 40px 20px; 
            display: flex; 
            justify-content: center; 
        }
        .container { width: 100%; max-width: 1000px; }
        .top-bar { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin-bottom: 30px; 
        }
        .logo { 
            display: flex; 
            align-items: center; 
            gap: 10px; 
            font-size: 1.1rem; 
            font-weight: 700; 
            color: #ffffff; 
            letter-spacing: 1px;
        }
        .dot { 
            width: 10px; 
            height: 10px; 
            background-color: #10b981; 
            border-radius: 50%; 
            box-shadow: 0 0 10px #10b981; 
        }
        .btn-home { 
            background-color: #064e3b; 
            color: #34d399; 
            border: 1px solid #059669; 
            padding: 8px 16px; 
            border-radius: 20px; 
            text-decoration: none; 
            font-size: 0.9rem; 
            font-weight: 600; 
            display: flex; 
            align-items: center; 
            gap: 6px;
            transition: all 0.2s ease;
        }
        .btn-home:hover { 
            background-color: #059669; 
            color: #ffffff; 
            box-shadow: 0 0 12px rgba(16, 185, 129, 0.4); 
        }
        h1 { color: #ffffff; font-size: 1.5rem; margin-bottom: 20px; font-weight: 600; }
        .table-container { 
            background-color: #111827; 
            border: 1px solid #1f2937; 
            border-radius: 8px; 
            overflow: hidden; 
        }
        table { width: 100%; border-collapse: collapse; }
        th { 
            background-color: #1f2937; 
            color: #10b981; 
            font-size: 0.8rem; 
            text-transform: uppercase; 
            letter-spacing: 0.5px; 
            padding: 14px 16px; 
            text-align: left; 
            font-weight: 700;
        }
        td { 
            padding: 16px; 
            border-bottom: 1px solid #1f2937; 
            font-size: 0.9rem; 
            color: #d1d5db; 
        }
        tr:last-child td { border-bottom: none; }
        tr:hover td { background-color: #172033; }
        .num-col { color: #6b7280; width: 50px; }
        .ip-col { color: #10b981; font-weight: 700; font-family: monospace; font-size: 0.95rem; }
        .ua-col { color: #9ca3af; font-size: 0.85rem; line-height: 1.4; max-width: 450px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="top-bar">
            <div class="logo">
                <span class="dot"></span> IP CHECKER
            </div>
            <a href="/" class="btn-home">🏡 Главная</a>
        </div>
        
        <h1>Последние визиты (до 20)</h1>
        
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>ВРЕМЯ (UTC)</th>
                        <th>IP-АДРЕС</th>
                        <th>USER-AGENT (БРАУЗЕР)</th>
                    </tr>
                </thead>
                <tbody>
                    {% for visit in visits %}
                    <tr>
                        <td class="num-col">{{ loop.index }}</td>
                        <td>{{ visit[1].strftime('%Y-%m-%d %H:%M:%S') }}</td>
                        <td class="ip-col">{{ visit[2] }}</td>
                        <td class="ua-col">{{ visit[3] }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
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
    
    # DISTINCT ON (ip_address) + ORDER BY ip_address, timestamp DESC для группировки уникальных IP
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
    app.run(host='0.0.0.0', port=5000)
