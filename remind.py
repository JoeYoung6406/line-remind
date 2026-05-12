import os
import requests
from datetime import datetime, timedelta

# ===== 設定 =====
CHANNEL_ACCESS_TOKEN = os.environ["LINE_TOKEN"]
GROUP_ID = os.environ["LINE_GROUP_ID"]

# 聚會排程：日期 -> [帶點心, 破冰, 敬拜, 代禱]
SCHEDULE = {
    "05/13": ["Janet", "Peter", "Shin", "頌揚"],
    "05/20": ["Joe", "巧巧", "Tiffany", "Janet"],
    "05/27": ["Peter", "Shin", "頌揚", "Joe"],
    "06/03": ["巧巧", "Tiffany", "Janet", "Peter"],
    "06/10": ["Shin", "頌揚", "Joe", "巧巧"],
    "06/17": ["Tiffany", "Janet", "Peter", "Shin"],
    "06/24": ["頌揚", "Joe", "巧巧", "Tiffany"],
    "07/01": ["Janet", "Peter", "Shin", "頌揚"],
    "07/08": ["Joe", "巧巧", "Tiffany", "Janet"],
    "07/15": ["Peter", "Shin", "頌揚", "Joe"],
    "07/22": ["巧巧", "Tiffany", "Janet", "Peter"],
    "07/29": ["Shin", "頌揚", "Joe", "巧巧"],
    "08/05": ["Tiffany", "Janet", "Peter", "Shin"],
    "08/12": ["頌揚", "Joe", "巧巧", "Tiffany"],
    "08/19": ["Janet", "Peter", "Shin", "頌揚"],
    "08/26": ["Joe", "巧巧", "Tiffany", "Janet"],
}

def send_line_message(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    data = {
        "to": GROUP_ID,
        "messages": [{"type": "text", "text": message}]
    }
    response = requests.post(url, headers=headers, json=data)
    return response

def main():
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    tomorrow_key = tomorrow.strftime("%m/%d")

    if tomorrow_key in SCHEDULE:
        persons = SCHEDULE[tomorrow_key]
        meeting_date = f"{tomorrow.month}/{tomorrow.day}"
        message = (
            f"明天的聚會 {meeting_date}\n"
            f"帶點心：{persons[0]}\n"
            f"破冰：{persons[1]}\n"
            f"敬拜：{persons[2]}\n"
            f"代禱：{persons[3]}"
        )
        response = send_line_message(message)
        if response.status_code == 200:
            print(f"[成功] 已發送 {meeting_date} 聚會提醒")
        else:
            print(f"[失敗] {response.status_code}：{response.text}")
    else:
        print(f"明天 {tomorrow_key} 沒有聚會，不發送。")

if __name__ == "__main__":
    main()
