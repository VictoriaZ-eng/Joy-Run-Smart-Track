from flask import Flask
from routes.weather import weather_bp, fetch_and_store_weather
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.register_blueprint(weather_bp, url_prefix='/weather')

if __name__ == '__main__':
    try:
        fetch_and_store_weather()
        print("天气数据更新成功")
    except Exception as e:
        print(f"天气数据更新失败: {e}")
    app.run(debug=True)