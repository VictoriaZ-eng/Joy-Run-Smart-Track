from flask import Flask
from routes.weather import weather_bp, fetch_and_store_weather
from routes.routeplanning import routeplanning_bp
from routes.racesspider import race_bp, spider_race, auto_spider_race
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.register_blueprint(weather_bp, url_prefix='/weather')
app.register_blueprint(routeplanning_bp, url_prefix='/routeplanning')
app.register_blueprint(race_bp, url_prefix='/racespider')

if __name__ == '__main__':
    try:
        fetch_and_store_weather()
        auto_spider_race()
        # print("天气数据更新成功")
    except Exception as e:
        print(f"{e}")
    app.run(debug=True)

# python backend/app.py