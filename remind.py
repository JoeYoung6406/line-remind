import os
import csv
import io
import json
import re
import requests
from datetime import datetime, timedelta

# ===== 設定 =====
CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_TOKEN", "")
GROUP_ID = os.environ.get("LINE_GROUP_ID", "")

# 輪值分配直接讀取 Google Sheet（試算表更新後不需改程式）
SHEET_ID = "1bbRLsAE4tEMaZG7D6QGKK9XZrig43ZrQeLOR_eFCQKQ"
SHEET_NAME = "輪值分配"
SHEET_CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
    f"/gviz/tq?tqx=out:csv&sheet={requests.utils.quote(SHEET_NAME)}"
)
SHEET_VIEW_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

DATE_HEADER = "日期"
# 輸出順序：標題名稱 -> 顯示文字
ROLES = ["帶點心", "破冰", "敬拜", "代禱"]

# 卡片配色（與 Hope Kids 服事卡同一套視覺）
INK = "#4a3b22"
TEAL = "#2bb3a3"
BG_SOFT = "#fffdf6"
BADGE_COLORS = ["#f2a900", "#ff7a59", "#2bb3a3"]


def _parse_md(value):
    """把試算表的日期欄位轉成 (月, 日)，無法解析則回傳 None。"""
    if not value:
        return None
    value = value.strip()

    # gviz 對日期型欄位可能回傳 Date(年,月,日)，其中月份是 0-based
    m = re.match(r"Date\((\d+),(\d+),(\d+)\)", value)
    if m:
        return int(m.group(2)) + 1, int(m.group(3))

    parts = re.split(r"[/-]", value)
    try:
        if len(parts) == 2:          # M/D
            return int(parts[0]), int(parts[1])
        if len(parts) == 3:          # Y/M/D
            return int(parts[1]), int(parts[2])
    except ValueError:
        return None
    return None


def fetch_schedule():
    """從 Google Sheet 抓輪值表，回傳 {(月, 日): {角色: 人名}}。"""
    resp = requests.get(SHEET_CSV_URL, timeout=20)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    rows = list(csv.reader(io.StringIO(resp.text)))

    # 找到含「日期」的標題列，並依欄名定位各欄索引（不寫死欄位位置）
    date_idx = None
    role_idx = {}
    header_row = -1
    for i, row in enumerate(rows):
        cells = [c.strip() for c in row]
        if DATE_HEADER in cells:
            date_idx = cells.index(DATE_HEADER)
            for role in ROLES:
                if role in cells:
                    role_idx[role] = cells.index(role)
            header_row = i
            break

    if date_idx is None:
        raise ValueError("在試算表中找不到『日期』標題列")

    schedule = {}
    for row in rows[header_row + 1:]:
        if len(row) <= date_idx:
            continue
        key = _parse_md(row[date_idx])
        if key is None:
            continue
        persons = {
            role: (row[idx].strip() if idx < len(row) else "")
            for role, idx in role_idx.items()
        }
        schedule[key] = persons
    return schedule


def role_row(label, name, color):
    return {
        "type": "box",
        "layout": "horizontal",
        "alignItems": "center",
        "spacing": "md",
        "contents": [
            {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": color,
                "cornerRadius": "6px",
                "paddingAll": "4px",
                "width": "72px",
                "contents": [{
                    "type": "text",
                    "text": label,
                    "size": "xs",
                    "weight": "bold",
                    "color": "#ffffff",
                    "align": "center",
                }],
            },
            {
                "type": "text",
                "text": name or "—",
                "size": "sm",
                "color": INK,
                "wrap": True,
                "flex": 1,
            },
        ],
    }


def build_flex(meeting_date, weekday, persons):
    body_rows = [
        role_row(role, persons.get(role, ""), BADGE_COLORS[i % len(BADGE_COLORS)])
        for i, role in enumerate(ROLES)
    ]

    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": TEAL,
            "paddingAll": "16px",
            "contents": [
                {"type": "text", "text": "小組聚會提醒", "size": "xs",
                 "weight": "bold", "color": "#ffffff"},
                {"type": "text", "text": "明天的聚會", "size": "xl",
                 "weight": "bold", "color": "#ffffff", "margin": "xs"},
                {"type": "text", "text": f"{meeting_date} {weekday}", "size": "sm",
                 "color": "#ffffff", "margin": "xs"},
            ],
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": BG_SOFT,
            "spacing": "sm",
            "paddingAll": "16px",
            "contents": body_rows,
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "color": TEAL,
                    "height": "sm",
                    "action": {"type": "uri", "label": "查看輪值表",
                               "uri": SHEET_VIEW_URL},
                },
            ],
        },
    }

    return {
        "type": "flex",
        "altText": f"明天的聚會 {meeting_date} 提醒",
        "contents": bubble,
    }


def send_line_message(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    data = {
        "to": GROUP_ID,
        "messages": [message]
    }
    response = requests.post(url, headers=headers, json=data)
    return response


def main():
    today = datetime.now()
    override = os.environ.get("REMIND_DATE")  # 測試用：指定 M/D 模擬「明天」
    if override:
        m, d = (int(x) for x in override.split("/"))
        target = datetime(today.year, m, d)
    else:
        target = today + timedelta(days=1)

    key = (target.month, target.day)
    schedule = fetch_schedule()

    if key not in schedule:
        print(f"明天 {key[0]}/{key[1]} 沒有聚會，不發送。")
        return

    persons = schedule[key]
    meeting_date = f"{key[0]}/{key[1]}"

    # 停聚處理：帶點心欄出現「暫停」或全部空白
    lead = persons.get("帶點心", "")
    if "暫停" in lead or not any(persons.values()):
        print(f"明天 {meeting_date} 暫停聚會，不發送。")
        return

    weekday = "（週" + "一二三四五六日"[target.weekday()] + "）"
    message = build_flex(meeting_date, weekday, persons)

    if os.environ.get("DRY_RUN"):
        print(json.dumps(message, ensure_ascii=False, indent=2))
        print(f"\n[DRY RUN] {meeting_date} {weekday} {persons}")
        return

    response = send_line_message(message)
    if response.status_code == 200:
        print(f"[成功] 已發送 {meeting_date} 聚會提醒")
    else:
        print(f"[失敗] {response.status_code}：{response.text}")


if __name__ == "__main__":
    main()
