# 后端启动代码
from flask import Flask
from routes.weather import weather_bp, fetch_and_store_weather
from routes.routeplanning import route_planning_bp
from routes.racesspider import race_bp, auto_spider_race
from flask_cors import CORS
from routes.qweather import qweather_bp
from routes.coze import coze_bp

app = Flask(__name__)
CORS(app)
app.register_blueprint(weather_bp, url_prefix='/weather')
app.register_blueprint(route_planning_bp)
app.register_blueprint(race_bp, url_prefix='/get_races')
app.register_blueprint(qweather_bp) 
app.register_blueprint(coze_bp, url_prefix='/coze') 

if __name__ == '__main__':
    try:
        fetch_and_store_weather()
        auto_spider_race()
        # print("天气数据更新成功")
    except Exception as e:
        print(f"{e}")
    app.run(debug=True)

# python backend/app.py