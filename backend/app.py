from flask import Flask, jsonify
import psycopg2

app = Flask(__name__)

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'joy_run_db',
    'user': 'postgres',
    'password': 'postgres1'
}

def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    print("数据库连接成功！")  # 新增日志
    return conn

@app.route('/test_db')
def test_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT version();')
        db_version = cur.fetchone()
        cur.close()
        conn.close()
        return jsonify({'db_version': db_version[0]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    try:
        get_db_connection()
    except Exception as e:
        print(f"数据库连接失败: {e}")
    app.run(debug=True)