# 本代码实现马拉松赛事信息爬虫
# 请在修改12-19行代码为自己数据库信息，第29行代码需要修改为自己的config.yaml路径.第183行代码改为自己temp文件夹路径
import os
import time
import yaml
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
import requests
import csv
import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'joy_run_db',
    'user': 'postgres',
    # 'password': 'postgres1'
    'password': 'zzq12'
}

race_bp = Blueprint('race', __name__)

# 读取配置
def load_config():
    """
    读取配置文件
    """
    # config_path = r"G:\gh_repo\Joy-Run-Smart-Track\backend\config.yaml"
    config_path = r"D:\中地校企联合实训\Yuepaozhihui\JoyRun_SmartTrack\backend\config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def insert_new_races_from_csv(csv_file):
    """
    从CSV文件中插入新的赛事数据到数据库
    :param csv_file: CSV文件路径
    """
    # 1. 读取csv
    with open(csv_file, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        csv_races = [row for row in reader]

    csv_race_ids = set(row['raceId'] for row in csv_races)

    # 2. 查询数据库已有raceId
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT raceId FROM race")
    db_race_ids = set(str(row[0]) for row in cur.fetchall())

    # 3. 找出新增raceId
    new_race_ids = csv_race_ids - db_race_ids
    if not new_race_ids:
        print("数据库无新增赛事，无需插入。")
        cur.close()
        conn.close()
        return

    # 4. 插入新增赛事
    insert_sql = """
        INSERT INTO race (
            raceId, raceName, province, city, area, shortAddress,
            startTime, showSignEndTime, coverImage, raceType
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    for row in csv_races:
        if row['raceId'] in new_race_ids:
            cur.execute(insert_sql, (
                int(row['raceId']),
                row['raceName'],
                row['province'] or None,
                row['city'] or None,
                row['area'] or None,
                row['shortAddress'] or None,
                row['startTime'] or None,
                row['showSignEndTime'] or None,
                row['coverImage'] or None,
                int(row['raceType']) if row['raceType'] else None
            ))
    conn.commit()
    print(f"已插入 {len(new_race_ids)} 条新赛事。")
    cur.close()
    conn.close()

class RaceSpider:
    def __init__(self, base_url, out_csv):
        self.base_url = base_url
        self.out_csv = out_csv
        self.data = []

    def fetch_page(self, page):
        """
        获取指定页码的赛事数据
        :param page: 页码
        :return: JSON格式的赛事数据
        """
        url = f"{self.base_url}?page={page}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def parse_races(self, races):
        """
        解析赛事数据
        :param races: 赛事数据列表
        """
        for race in races:
            self.data.append([
                race.get("raceId", ""),
                race.get("raceName", ""),
                race.get("province", ""),
                race.get("city", ""),
                race.get("area", ""),
                race.get("shortAddress", ""),
                race.get("startTime", ""),
                race.get("showSignEndTime", ""),
                race.get("coverImage", ""),
                race.get("raceType", "")
            ])

    def crawl_all(self):
        """
        爬取所有赛事数据
        """
        page = 1
        while True:
            res = self.fetch_page(page)
            if res.get("code") != 200 or not res.get("data"):
                break
            self.parse_races(res["data"])
            page += 1

    def save_csv(self):
        """
        保存爬取的数据到CSV文件
        """
        headers = [
            "raceId", "raceName", "province", "city", "area",
            "shortAddress", "startTime", "showSignEndTime", "coverImage", "raceType"
        ]
        with open(self.out_csv, "w", newline='', encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(self.data)

    def run(self):
        """
        执行爬虫流程
        """
        self.crawl_all()
        self.save_csv()

def should_spider(ts_file):
    """
    判断是否需要重新爬取数据
    :param ts_file: 时间戳文件路径
    :return: 如果超过5天则返回True，否则返回False
    """
    if not os.path.exists(ts_file):
        return True
    with open(ts_file, "r") as f:
        last_ts = float(f.read().strip())
    last_time = datetime.fromtimestamp(last_ts)
    if datetime.now() - last_time > timedelta(days=5):
        return True
    return False

def update_timestamp(ts_file):
    """
    更新时间戳文件
    :param ts_file: 时间戳文件路径
    """
    with open(ts_file, "w") as f:
        f.write(str(time.time()))

def auto_spider_race():
    """
    自动爬取赛事数据
    """
    config = load_config()
    ts_file = config.get("last_spider_time_stamp_file")
    # csv_file = r"G:\gh_repo\Joy-Run-Smart-Track\backend\temp\race_list.csv"
    csv_file = r"D:\中地校企联合实训\Yuepaozhihui\JoyRun_SmartTrack\backend\temp\race_list.csv"
    if should_spider(ts_file):
        spider = RaceSpider(
            "https://api.sport-china.cn/officialApi/getRaces",
            out_csv=csv_file
        )
        spider.run()
        update_timestamp(ts_file)
        print("爬取完成，数据已更新。")
        insert_new_races_from_csv(csv_file)
    else:
        insert_new_races_from_csv(csv_file)
        print("距离上次爬取未超过5天，无需爬取。")

@race_bp.route('/test', methods=['GET'])
def test_api():
    """测试API连接"""
    return jsonify({
        "code": 200,
        "message": "API连接正常",
        "timestamp": datetime.now().isoformat()
    })

@race_bp.route('/api/get_races', methods=['GET'])
def get_races():
    """
    获取赛事数据API
    支持的查询参数：
    - province: 省份筛选
    - raceType: 赛事类型筛选
    - range: 范围查询，格式如 "1-5" 或 "10-20"
    
    如果传入province/raceType，按举办时间(startTime)排序
    如果传入range，按raceId从大到小排序并返回指定范围
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # 获取查询参数
        province = request.args.get('province')
        race_type = request.args.get('raceType')
        range_param = request.args.get('range')
        
        # 构建基础查询SQL
        base_sql = """
            SELECT raceId, raceName, province, city, area, shortAddress, 
                   startTime, showSignEndTime, coverImage, raceType
            FROM race
        """
        
        # 情况1: 按range查询
        if range_param:
            try:
                # 解析range参数，如 "1-5" 或 "10-20"
                start_idx, end_idx = map(int, range_param.split('-'))
                
                # 按raceId从大到小排序，然后取指定范围
                sql = base_sql + " ORDER BY raceId DESC LIMIT %s OFFSET %s"
                limit = end_idx - start_idx + 1
                offset = start_idx - 1
                cur.execute(sql, (limit, offset))
                
            except ValueError:
                return jsonify({
                    "code": 400,
                    "message": "range参数格式错误，应为 '开始-结束' 格式，如 '1-5'"
                }), 400
        
        # 情况2: 按province和/或raceType查询
        else:
            conditions = []
            params = []
            
            if province:
                conditions.append("province = %s")
                params.append(province)
            
            if race_type:
                conditions.append("raceType = %s")
                params.append(int(race_type))
            
            # 构建WHERE子句
            where_clause = ""
            if conditions:
                where_clause = " WHERE " + " AND ".join(conditions)
            
            # 按举办时间排序（如果有startTime的话，否则按raceId排序）
            sql = base_sql + where_clause + " ORDER BY startTime ASC, raceId ASC"
            cur.execute(sql, params)
        
        # 获取查询结果
        results = cur.fetchall()
        
        # 转换为字典格式
        race_list = []
        for row in results:
            race_dict = {
                "raceId": row[0],
                "raceName": row[1],
                "province": row[2],
                "city": row[3],
                "area": row[4],
                "shortAddress": row[5],
                "startTime": row[6],
                "showSignEndTime": row[7],
                "coverImage": row[8],
                "raceType": row[9]
            }
            race_list.append(race_dict)
        
        cur.close()
        conn.close()
        
        # 如果数据库中没有数据，返回模拟数据进行测试
        if not race_list and range_param:
            race_list = generate_mock_races(range_param)
        
        return jsonify({
            "code": 200,
            "message": "查询成功",
            "data": race_list,
            "total": len(race_list)
        })
        
    except psycopg2.Error as e:
        print(f"数据库连接错误: {e}")
        # 数据库连接失败时，返回模拟数据
        if range_param:
            mock_data = generate_mock_races(range_param)
            return jsonify({
                "code": 200,
                "message": "使用模拟数据（数据库连接失败）",
                "data": mock_data,
                "total": len(mock_data)
            })
        return jsonify({
            "code": 500,
            "message": f"数据库错误: {str(e)}"
        }), 500
    except Exception as e:
        print(f"服务器错误: {e}")
        return jsonify({
            "code": 500,
            "message": f"服务器错误: {str(e)}"
        }), 500

def generate_mock_races(range_param):
    """生成模拟赛事数据用于测试"""
    try:
        start_idx, end_idx = map(int, range_param.split('-'))
        mock_races = []
        
        for i in range(start_idx, min(end_idx + 1, start_idx + 9)):  # 最多返回9条
            mock_races.append({
                "raceId": 1000 + i,
                "raceName": f"模拟马拉松赛事 {i}",
                "province": "浙江省" if i % 3 == 0 else "江苏省" if i % 3 == 1 else "上海市",
                "city": "杭州市" if i % 3 == 0 else "南京市" if i % 3 == 1 else "上海市",
                "area": f"测试区域{i}",
                "shortAddress": f"测试地址{i}号",
                "startTime": f"2025-{10 + (i % 3)}-{15 + (i % 15):02d}",
                "showSignEndTime": f"2025-{9 + (i % 3)}-{15 + (i % 15):02d}",
                "coverImage": "https://via.placeholder.com/300x200?text=Mock+Race+Image",
                "raceType": (i % 5) + 1
            })
        
        return mock_races
    except:
        return []