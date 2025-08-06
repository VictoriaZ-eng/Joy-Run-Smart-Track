import os
import time
import yaml
from datetime import datetime, timedelta
from flask import Blueprint, jsonify
import requests
import csv
import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'joy_run_db',
    'user': 'postgres',
    'password': 'postgres1'
}

race_bp = Blueprint('race', __name__)

# 读取配置
def load_config():
    config_path = r"G:\gh_repo\Joy-Run-Smart-Track\backend\config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def insert_new_races_from_csv(csv_file):
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
        url = f"{self.base_url}?page={page}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def parse_races(self, races):
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
        page = 1
        while True:
            res = self.fetch_page(page)
            if res.get("code") != 200 or not res.get("data"):
                break
            self.parse_races(res["data"])
            page += 1

    def save_csv(self):
        headers = [
            "raceId", "raceName", "province", "city", "area",
            "shortAddress", "startTime", "showSignEndTime", "coverImage", "raceType"
        ]
        with open(self.out_csv, "w", newline='', encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(self.data)

    def run(self):
        self.crawl_all()
        self.save_csv()

def should_spider(ts_file):
    if not os.path.exists(ts_file):
        return True
    with open(ts_file, "r") as f:
        last_ts = float(f.read().strip())
    last_time = datetime.fromtimestamp(last_ts)
    if datetime.now() - last_time > timedelta(days=5):
        return True
    return False

def update_timestamp(ts_file):
    with open(ts_file, "w") as f:
        f.write(str(time.time()))

def auto_spider_race():
    config = load_config()
    ts_file = config.get("last_spider_time_stamp_file")
    csv_file = r"G:\gh_repo\Joy-Run-Smart-Track\backend\temp\race_list.csv"
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

@race_bp.route('/api/spider_race', methods=['GET'])
def spider_race():
    config = load_config()
    ts_file = config.get("last_spider_time_stamp_file")
    csv_file = r"G:\gh_repo\Joy-Run-Smart-Track\backend\temp\race_list.csv"
    if should_spider(ts_file):
        spider = RaceSpider(
            "https://api.sport-china.cn/officialApi/getRaces",
            out_csv=csv_file
        )
        spider.run()
        update_timestamp(ts_file)
        return jsonify({"msg": "爬取完成", "csv": csv_file})
    else:
        return jsonify({"msg": "距离上次爬取未超过5天，无需爬取", "csv": csv_file})