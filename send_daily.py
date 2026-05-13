import os
import json
import requests
from datetime import datetime

_day = datetime.now().day
LINE_TOKEN = os.environ["LINE_TOKEN"] if _day % 2 == 1 else os.environ.get("LINE_TOKEN_B", os.environ["LINE_TOKEN"])
GROUP_ID = os.environ["LINE_GROUP_ID"]

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

def send_line_message(links):
    greeting = "各位家人平安，鼓勵你花些時間親近神唷~"

    _push([{
        "type": "image",
        "originalContentUrl": IMAGE_URL,
        "previewImageUrl": IMAGE_URL
    }])

    footer_contents = [
        {
            "type": "button",
            "style": "link",
            "height": "sm",
            "action": {"type": "uri", "label": title, "uri": href}
        }
        for title, href in links
    ]
    body_contents = [
        {
            "type": "text",
            "text": greeting,
            "wrap": True,
            "size": "md",
            "color": "#333333"
        }
    ] + footer_contents

    bubble = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": body_contents
        }
    }
    return _push([{"type": "flex", "altText": greeting, "contents": bubble}])

def main():
    with open(LINKS_PATH, encoding="utf-8") as f:
        links = json.load(f)

    print("發送到 LINE 群組...")
    response = send_line_message(links)
    if response.status_code == 200:
        print("[成功] 每日計畫已發送")
    else:
        print(f"[失敗] {response.status_code}：{response.text}")

if __name__ == "__main__":
    main()
