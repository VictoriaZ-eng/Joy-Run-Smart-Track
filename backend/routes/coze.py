# 后端保护COZE TOKEN（AI功能相关代码）
from flask import Blueprint, jsonify
import os

coze_bp = Blueprint("coze", __name__)

# 从环境变量读取 token（推荐），如果没设置则用默认值
COZE_TOKEN = os.getenv("COZE_TOKEN", "sat_yWOYtRW3qyvsvGugcMTHjK4r8cPNWu4Nclp5dN8zBfutdGTsRdTRmeO3RmnY5G0K")

@coze_bp.route("/token", methods=["GET"])
def get_token():
    return jsonify({"token": COZE_TOKEN})
