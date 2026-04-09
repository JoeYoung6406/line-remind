import os
import requests
from playwright.sync_api import sync_playwright

LINE_TOKEN = os.environ["LINE_TOKEN"]
GROUP_ID = os.environ["LINE_GROUP_ID"]
PLAN_URL = "https://brp-bot.dev-dee.workers.dev/api/v1/plan?format=html"

def take_screenshot():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 800, "height": 1200})
        page.goto(PLAN_URL, wait_until="networkidle")
        screenshot = page.screenshot(full_page=True)
        browser.close()
    return screenshot

def upload_image(image_bytes):
    # 先嘗試 litterbox（catbox 的暫存版，72小時有效）
    try:
        response = requests.post(
            "https://litterbox.catbox.moe/resources/internals/api.php",
            data={"reqtype": "fileupload", "time": "72h"},
            files={"fileToUpload": ("plan.png", image_bytes, "image/png")},
            timeout=30
        )
        url = response.text.strip()
        if url.startswith("https://"):
            print(f"litterbox 上傳成功：{url}")
            return url
        print(f"litterbox 回應：{url}")
    except Exception as e:
        print(f"litterbox 失敗：{e}")

    # 備用：0x0.st
    response = requests.post(
        "https://0x0.st",
        files={"file": ("plan.png", image_bytes, "image/png")},
        timeout=30
    )
    response.raise_for_status()
    url = response.text.strip()
    print(f"0x0.st 上傳成功：{url}")
    return url

def send_line_image(image_url):
    response = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LINE_TOKEN}"
        },
        json={
            "to": GROUP_ID,
            "messages": [{
                "type": "image",
                "originalContentUrl": image_url,
                "previewImageUrl": image_url
            }]
        }
    )
    return response

def main():
    print("截取網頁中...")
    screenshot = take_screenshot()

    print("上傳圖片中...")
    image_url = upload_image(screenshot)
    print(f"圖片網址：{image_url}")

    print("發送到 LINE 群組...")
    response = send_line_image(image_url)
    if response.status_code == 200:
        print("[成功] 每日計畫已發送")
    else:
        print(f"[失敗] {response.status_code}：{response.text}")

if __name__ == "__main__":
    main()
