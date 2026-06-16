# -*- coding: utf-8 -*-
import os
import re
import time
import random
import cloudscraper
from pathlib import Path
from bs4 import BeautifulSoup

# ===== 初始化配置 =====
BASE_DIR = Path(__file__).resolve().parent
DISHES_DIR = BASE_DIR / "cook" / "dishes"
BAIKE_URL = "https://baike.baidu.com/item/{}"
DELAY = 1
TIMEOUT = 15
MAX_RETRIES = 3

_scraper = None


def get_scraper():
    global _scraper
    if _scraper is None:
        _scraper = cloudscraper.create_scraper(
            browser={
                "browser": "chrome",
                "platform": "darwin",
                "mobile": False,
            }
        )
    return _scraper


def extract_dish_names(dishes_dir):
    """递归遍历菜品目录，提取所有 .md 文件名（不含后缀）作为菜品名"""
    dish_files = []
    for root, dirs, files in os.walk(dishes_dir):
        for f in files:
            if f.endswith(".md") and not f.startswith("."):
                filepath = Path(root) / f
                dish_name = filepath.stem
                dish_files.append((dish_name, filepath))
    return dish_files


def clean_summary(summary_element):
    """清理摘要：移除引用标记（sup 标签）和引用链接"""
    for sup in summary_element.find_all("sup"):
        sup.decompose()
    for a in summary_element.find_all("a"):
        if a.get("href") and ("reference" in a.get("href", "") or a.get("class") and "sup" in str(a.get("class"))):
            a.decompose()

    text = summary_element.get_text(strip=True)
    text = re.sub(r"\[\d+(?:-\d+)?\]", "", text)
    text = re.sub(r"\s+", "", text)
    return text


def search_baike(dish_name):
    """搜索百度百科词条，返回词条摘要文本；失败返回 None"""
    url = BAIKE_URL.format(dish_name)
    scraper = get_scraper()

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = scraper.get(url, timeout=TIMEOUT)
            resp.encoding = "utf-8"

            if resp.status_code == 403:
                print(f"  [{dish_name}] HTTP 403（反爬拦截），尝试 {attempt}/{MAX_RETRIES}")
                if attempt < MAX_RETRIES:
                    time.sleep(DELAY * (attempt + 1))
                continue

            if resp.status_code != 200:
                print(f"  [{dish_name}] HTTP {resp.status_code}，尝试 {attempt}/{MAX_RETRIES}")
                if attempt < MAX_RETRIES:
                    time.sleep(DELAY * attempt)
                continue

            soup = BeautifulSoup(resp.text, "lxml")

            summary = soup.find("div", class_="J-summary")
            if summary is None:
                summary = soup.find("div", class_="lemma-summary")
            if summary is None:
                summary = soup.find("div", attrs={"data-tid": "lemma-summary"})

            if summary:
                text = clean_summary(summary)
                if text:
                    return text
                else:
                    print(f"  [{dish_name}] 摘要为空")
                    return None
            else:
                print(f"  [{dish_name}] 未找到词条摘要")
                return None

        except Exception as e:
            print(f"  [{dish_name}] 请求异常: {e}，尝试 {attempt}/{MAX_RETRIES}")
            if attempt < MAX_RETRIES:
                time.sleep(DELAY * attempt)

    return None


def update_md_file(filepath, dish_name, summary):
    """在 md 文件头部插入百科摘要，其余内容保持不变"""
    intro_header = f"# {dish_name}的介绍"
    intro_block = f"{intro_header}\n{summary}\n\n"

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if intro_header in content:
        print(f"  [{dish_name}] 文件已包含百科介绍，跳过")
        return

    new_content = intro_block + content

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"  [{dish_name}] 已更新百科介绍")


def main():
    print("=" * 50)
    print("百度百科菜品爬虫")
    print(f"菜品目录: {DISHES_DIR}")
    print("=" * 50)

    dish_files = extract_dish_names(DISHES_DIR)
    print(f"共发现 {len(dish_files)} 个菜品\n")

    success_count = 0
    skip_count = 0

    for i, (dish_name, filepath) in enumerate(dish_files, 1):
        print(f"[{i}/{len(dish_files)}] 处理: {dish_name}")

        summary = search_baike(dish_name)

        if summary:
            update_md_file(filepath, dish_name, summary)
            success_count += 1
        else:
            print(f"  [{dish_name}] 无法获取百科信息，跳过")
            skip_count += 1

        # 随机延迟，模拟人为访问
        delay = DELAY + random.uniform(0.5, 2.0)
        time.sleep(delay)

    print("\n" + "=" * 50)
    print(f"处理完成: 成功 {success_count} 个，跳过 {skip_count} 个")
    print("=" * 50)


if __name__ == "__main__":
    main()
