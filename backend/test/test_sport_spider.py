import requests
import csv

class RaceSpider:
    def __init__(self, base_url, out_csv="race_list.csv"):
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

if __name__ == "__main__":
    spider = RaceSpider(
        "https://api.sport-china.cn/officialApi/getRaces",
        out_csv=r"G:\gh_repo\Joy-Run-Smart-Track\backend\temp\race_list.csv"
    )
    spider.run()
    print("已保存 race_list.csv")