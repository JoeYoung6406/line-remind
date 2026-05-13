import os
import json
from datetime import datetime
from playwright.sync_api import sync_playwright

PLAN_URL = "https://brp-bot.dev-dee.workers.dev/api/v1/plan?format=html"
SCREENSHOT_PATH = "plan.png"
LINKS_PATH = "links.json"

def take_screenshot_and_links():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": 500, "height": 900},
            device_scale_factor=2
        )
        page.goto(PLAN_URL, wait_until="networkidle")
        screenshot = page.locator("body").screenshot()
        links = []
        anchors = page.locator("a[href*='youversion'], a[href*='bible.com']").all()
        for anchor in anchors:
            href = anchor.get_attribute("href")
            title = anchor.evaluate(
                "el => el.previousElementSibling ? el.previousElementSibling.innerText : el.parentElement.innerText"
            ).strip()
            if href and title:
                links.append((title, href))
        browser.close()
    return screenshot, links

def main():
    print("截取網頁中...")
    screenshot, links = take_screenshot_and_links()
    print(f"找到 {len(links)} 個連結：{links}")

    with open(SCREENSHOT_PATH, "wb") as f:
        f.write(screenshot)
    print(f"截圖已儲存：{SCREENSHOT_PATH}")

    with open(LINKS_PATH, "w", encoding="utf-8") as f:
        json.dump(links, f, ensure_ascii=False)
    print(f"連結已儲存：{LINKS_PATH}")

if __name__ == "__main__":
    main()
