from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def get_my_ip():
    # Проверяем заголовки на случай, если стоим за прокси/Nginx, иначе берем прямой адрес
    if request.headers.get('X-Forwarded-For'):
        client_ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    else:
        client_ip = request.remote_addr
        
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>My IP Service</title>
        <style>
            body {{ font-family: Arial, sans-serif; background: #0f172a; color: #f8fafc; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
            .card {{ background: #1e293b; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); text-align: center; }}
            h1 {{ color: #38bdf8; font-size: 2.5rem; margin-bottom: 10px; }}
            p {{ color: #94a3b8; font-size: 1.1rem; }}
        </style>
    </head>
    <body>
        <div class="card">
            <p>Ваш внешний IP-адрес:</p>
            <h1>{client_ip}</h1>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
