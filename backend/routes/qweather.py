from flask import Blueprint, jsonify
import requests
from datetime import datetime

qweather_bp = Blueprint('qweather', __name__, url_prefix='/api/qweather')

# ========= 配置部分 =========
QWEATHER_API_KEY = "b58da49a9c65480ebc795b041ad05eef"

# ⚠️ 从控制台复制的 Host（不用写 https://，代码里会自动加）
API_HOST = "nt3qqqbu6k.re.qweatherapi.com"

# 确保 Host 带上协议头
if not API_HOST.startswith("http"):
    API_HOST = "https://" + API_HOST

# 默认地点（杭州市拱墅区）
DEFAULT_LOCATION = "101210113"


def fetch_air_quality(location_id):
    """封装请求逻辑"""
    air_url = f"{API_HOST}/v7/air/now?location={location_id}&key={QWEATHER_API_KEY}"
    print("请求地址：", air_url)  # 调试用

    air_res = requests.get(air_url, timeout=10).json()

    # 检查返回是否正常
    if "code" in air_res and air_res["code"] != "200":
        raise ValueError(f"API返回错误: {air_res}")

    if not air_res.get('now'):
        raise ValueError("API返回数据不完整")

    return {
        "air": air_res['now'],
        "location": location_id,
        "updateTime": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }


# ========= 路由 =========

# 默认路由：直接访问 /api/qweather/now
@qweather_bp.route('/now', methods=['GET'])
def get_air_quality_default():
    try:
        return jsonify(fetch_air_quality(DEFAULT_LOCATION))
    except Exception as e:
        return jsonify({
            "error": str(e),
            "air": {"aqi": "--", "category": "无数据"}
        }), 500


# 指定地点：访问 /api/qweather/now/<location_id>
@qweather_bp.route('/now/<location_id>', methods=['GET'])
def get_air_quality(location_id):
    try:
        return jsonify(fetch_air_quality(location_id))
    except Exception as e:
        return jsonify({
            "error": str(e),
            "air": {"aqi": "--", "category": "无数据"}
        }), 500
