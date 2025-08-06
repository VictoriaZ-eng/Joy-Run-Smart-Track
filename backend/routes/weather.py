import requests
from datetime import datetime, timedelta
from flask import Blueprint
import psycopg2
from flask import Blueprint, jsonify

weather_bp = Blueprint('weather', __name__)

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'joy_run_db',
    'user': 'postgres',
    'password': 'postgres1'
}

def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    return conn

def fetch_api_key():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT api_key FROM gaode_api ORDER BY id DESC LIMIT 1;")
    api_key = cur.fetchone()[0]
    cur.close()
    conn.close()
    return api_key

def fetch_and_store_weather():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT created_at FROM weather ORDER BY created_at DESC LIMIT 1;")
    last_time = cur.fetchone()
    now = datetime.now()
    need_update = True
    if last_time:
        last_time = last_time[0]
        if now - last_time < timedelta(minutes=30):
            print("天气时最新的，未超过30分钟，不更新")
            need_update = False
    if need_update:
        api_key = fetch_api_key()
        city_code = '330105'  # 杭州市拱墅区
        weather_url = f'https://restapi.amap.com/v3/weather/weatherInfo?city={city_code}&key={api_key}&extensions=all'
        weather_response = requests.get(weather_url)
        weather_data = weather_response.json()
        if weather_data.get('status') == '1':
            forecast = weather_data['forecasts'][0]
            for cast in forecast['casts']:
                cur.execute("""
                    INSERT INTO weather (city, adcode, province, reporttime, date, week, dayweather, nightweather, daytemp, nighttemp, daywind, nightwind, daypower, nightpower, daytemp_float, nighttemp_float)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    forecast['city'], forecast['adcode'], forecast['province'], forecast['reporttime'],
                    cast['date'], cast['week'], cast['dayweather'], cast['nightweather'],
                    int(cast['daytemp']), int(cast['nighttemp']), cast['daywind'], cast['nightwind'],
                    cast['daypower'], cast['nightpower'], float(cast['daytemp_float']), float(cast['nighttemp_float'])
                ))
            conn.commit()
            print("天气成功更新")
    cur.close()
    conn.close()

@weather_bp.route('/api/get_weather', methods=['GET'])
def get_weather():
    print("Fetching weather data...")
    conn = get_db_connection()
    cur = conn.cursor()
    # 获取最新四天的天气
    cur.execute("""
        SELECT *
        FROM (
            SELECT *
            FROM weather
            ORDER BY created_at DESC
            LIMIT 4
        ) AS latest_weather
        ORDER BY date ASC
    """)
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    forecasts = [dict(zip(columns, row)) for row in rows]
    cur.close()
    conn.close()
    return jsonify({'forecasts': forecasts})