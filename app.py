from flask import Flask, render_template, request
import psycopg2
import os

app = Flask(__name__)

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
    
    # Создаем таблицу, если её ещё нет
    cur.execute('''
        CREATE TABLE IF NOT EXISTS visit (
            id SERIAL PRIMARY KEY,
            ip_address VARCHAR(50),
            user_agent TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    
    # Записываем каждый визит в историю
    cur.execute(
        'INSERT INTO visit (ip_address, user_agent) VALUES (%s, %s)',
        (user_ip, user_agent)
    )
    
    conn.commit()
    cur.close()
    conn.close()

    return render_template('index.html', ip=user_ip)

@app.route('/history')
def history():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # DISTINCT ON (ip_address) строго требует ORDER BY ip_address в начале!
    cur.execute('''
        SELECT DISTINCT ON (ip_address) id, timestamp, ip_address, user_agent 
        FROM visit 
        ORDER BY ip_address, timestamp DESC 
        LIMIT 20;
    ''')
    
    visits = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('history.html', visits=visits)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
