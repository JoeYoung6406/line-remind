import os
import json
import requests
from datetime import datetime

_day = datetime.now().day
if _day % 2 == 1:
    LINE_TOKEN = os.environ.get("LINE_TOKEN", "")
else:
    LINE_TOKEN = os.environ.get("LINE_TOKEN_B") or os.environ.get("LINE_TOKEN", "")
GROUP_ID = os.environ.get("LINE_GROUP_ID", "")

IMAGE_URL = "https://raw.githubusercontent.com/JoeYoung6406/line-remind/main/plan.png"
LINKS_PATH = "links.json"

def _push(messages):
    return requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LINE_TOKEN}"
        },
        json={"to": GROUP_ID, "messages": messages}
    )

def plan_aspect_ratio():
    """讀 plan.png 的實際尺寸給 hero 圖用（LINE 限制高最多是寬的 3 倍）。"""
    try:
        with open("plan.png", "rb") as f:
            head = f.read(24)
        w = int.from_bytes(head[16:20], "big")
        h = int.from_bytes(head[20:24], "big")
        if w > 0 and h > 0:
            return f"{w}:{min(h, w * 3)}"
    except OSError:
        pass
    return "500:900"


def send_line_message(links):
    greeting = "各位家人平安，鼓勵你花些時間親近神唷~"
    # 加日期參數避免 LINE 快取到前一天的舊圖
    image_url = f"{IMAGE_URL}?v={datetime.now():%Y%m%d}"

    buttons = [
        {
            "type": "button",
            "style": "link",
            "height": "sm",
            "action": {"type": "uri", "label": title, "uri": href}
        }
        for title, href in links
    ]

    bubble = {
        "type": "bubble",
        "hero": {
            "type": "image",
            "url": image_url,
            "size": "full",
            "aspectRatio": plan_aspect_ratio(),
            "aspectMode": "fit",
            "action": {"type": "uri", "uri": image_url}
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "text",
                    "text": greeting,
                    "wrap": True,
                    "size": "md",
                    "color": "#333333"
                }
            ] + buttons
        }
    }
    message = {"type": "flex", "altText": greeting, "contents": bubble}

    if os.environ.get("DRY_RUN"):
        print(json.dumps(message, ensure_ascii=False, indent=2))
        return None

    return _push([message])

def main():
    with open(LINKS_PATH, encoding="utf-8") as f:
        links = json.load(f)

    print("發送到 LINE 群組...")
    response = send_line_message(links)
    if response is None:
        print("[DRY RUN] 只顯示訊息內容，未發送")
    elif response.status_code == 200:
        print("[成功] 每日計畫已發送")
    else:
        print(f"[失敗] {response.status_code}：{response.text}")

if __name__ == "__main__":
    main()
