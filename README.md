# 🏃‍♀️悦跑智绘——个性化慢跑路线规划系统🏃

随着城市居民健康意识的提升，慢跑已成为最受欢迎的健身方式之一。然而，现有慢跑路径推荐系统普遍存在功能单一、智能化程度不足的问题，难以满足用户对个性化、趣味性和科学性的综合需求。“悦跑智绘——个性化慢跑路径优化系统”正是针对这一市场空白而设计，致力于为跑者提供更智能、更富创意的运动体验

## 主要项目结构
```sh
JoyRun_SmartTrack/
├── src/          # 前端源代码
│   ├── assets/           # 存放icon图标及图片资源
│   ├──components/   # 前端组件
│   ├── data/        # 推荐路线图表数据
│   ├──  GIS-data/   # 推荐路线json数据
│   ├──  router/   # 路由配置
│   ├──  util/      # 网络请求配置核心文件
│   ├──  views/   #功能实现代码
│   ├──  App.vue   #首页代码
│   ├──  main.js    #入口文件
├── .env.development   # 生产环境配置
├──.env.production   # 开发环境配置
├── index.html   # 样式文件
├── pacakage.json   # 前端库包文件
├── vite.config.js   # Vite 项目的核心配置文件
└── backend/           # 后端代码
├── app.py         # Flask主程序
├── config.yaml         # 路径配置文件
├── setup_env.bat         # 安装python环境
├── res        # 算法原始文件及路网表格
├── routes         # 后端功能代码
├── schema        # 创建数据库相关代码
├── temp         # 存储生成路径临时文件
└── requirements.txt   # Python依赖列表
```
## 🛠️安装部署说明

### 系统硬件需求

💻 系统要求
硬件环境：

✅ 操作系统：Windows 11 专业版

✅ 处理器：Intel Core i7 第3代或更高

✅ 内存：32GB RAM（最低16GB）

✅ 存储：70GB+ 可用空间

软件环境：

🟢 Node.js v20.19.0+

🟢 Python 3.11.4+

🟢 PostgreSQL 17.5+ with PostGIS 3.5+

### 🚀 快速开始

### 1️⃣ 前端部署
```sh
# 进入项目目录
cd JoyRun_SmartTrack

# 安装依赖
npm install

# 构建生产版本
npm run build

# 启动开发服务器
npm run dev
```
💡 提示：环境配置已预设，生产环境使用相对路径 /api。开发调试时可修改 .env.development 中的VITE_APP_API_URL。

### 2️⃣ 后端部署
```sh
# 进入后端目录
cd backend

# 方式一：使用自动安装脚本
./setup_env.sh

# 方式二：手动创建环境
conda create -n joyrun python=3.11.4
conda activate joyrun
pip install -r requirements.txt
```
### 3️⃣ 数据库配置
```sh
-- 创建数据库
CREATE DATABASE joy_run_db;

-- 初始化天气数据表
\i create_weather.sql
```
### 4️⃣ 配置文件设置
在 config.yaml 中配置：
```sh
 route_planning_temp_folder: "..."
  last_spider_time_stamp_file: "..."
```
## 👥 项目团队
### 如果您有任何问题或建议，或者遇到了漏洞，请联系我们
- (https://github.com/VictoriaZ-eng) - 前端构建
- (https://github.com/Asher-Lars) - AI智能体构建
- (https://github.com/zeshuiliucheng) - 学术基础支撑
- (https://github.com/YiHanChangBanQingChun) - 后端及核心功能开发

📞 联系我们
单位：广州大学地理科学与遥感学院
邮箱：📧 1610881171@qq.com

