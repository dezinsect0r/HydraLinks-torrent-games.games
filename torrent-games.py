import requests
from bs4 import BeautifulSoup
import re
import json
from multiprocessing.pool import ThreadPool
from time import sleep
from random import uniform
import bencodepy
import hashlib
from urllib.parse import urljoin

BASE_URL = "https://torrent-games.games"
HEADERS = {'User-Agent': 'Mozilla/5.0'}
MAX_PAGES = 2574
THREADS = 16
DELAY_RANGE = (0.2, 0.5)

TRACKERS = [
    "udp://tracker.opentrackr.org:1337/announce",
    "udp://open.demonii.com:1337",
    "http://tracker.openbittorrent.com:80/announce",
    "udp://opentracker.i2p.rocks:6969/announce",
    "udp://tracker.internetwarriors.net:1337/announce",
    "udp://tracker.leechers-paradise.org:6969/announce",
    "udp://coppersurfer.tk:6969/announce",
    "udp://tracker.zer0day.to:1337/announce"
]

def torrent_to_magnet(torrent_url, title):
    try:
        r = requests.get(torrent_url, headers=HEADERS, timeout=10)
        info = bencodepy.encode(bencodepy.decode(r.content)[b'info'])
        h = hashlib.sha1(info).hexdigest()
        trackers = ''.join([f"&tr={t.replace(':', '%3A').replace('/', '%2F')}" for t in TRACKERS])
        return f"magnet:?xt=urn:btih:{h}&dn={title.replace(' ', '.')}"+trackers
    except:
        return ""

def get_game_links_from_page(p):
    try:
        r = requests.get(f"{BASE_URL}/page/{p}/", headers=HEADERS, timeout=15)
        s = BeautifulSoup(r.text, 'html.parser')
        return list({
            a['href'] for a in s.select('a[href^="https://torrent-games.games/news/"]')
            if re.match(r'^https://torrent-games\.games/news/\d+-', a['href'])
        })
    except:
        return []

def parse_game_wrapper(args):
    i, total, url = args
    result = parse_game(url)
    print(f"[{i}/{total}] {'✓' if result else '✗'} {url}")
    return result

def parse_game(url):
    try:
        sleep(uniform(*DELAY_RANGE))
        r = requests.get(url, headers=HEADERS, timeout=15)
        s = BeautifulSoup(r.text, 'html.parser')
        title = s.select_one('h1').text.strip()

        t_tag = s.select_one('#page__dl a[href*="do=download"]')
        torrent = urljoin(BASE_URL, t_tag['href']) if t_tag else ""
        magnet = torrent_to_magnet(torrent, title) if torrent else ""

        size = "N/A"
        date = "N/A"
        for li in s.select("ul.page__list li"):
            label = li.select_one("span")
            if not label:
                continue
            label_text = label.text.strip().lower()
            content_text = li.get_text(separator=" ").replace(label.text, "").strip()
            if "размер" in label_text:
                m = re.search(r'([\d.,]+)', content_text)
                if m:
                    size = m.group(1).replace(",", ".") + "GB"
            elif "дата" in label_text:
                m = re.search(r'\d{2}\.\d{2}\.\d{4}', content_text)
                if m:
                    date = m.group(0).replace(".", "-")

        return {
            "title": title,
            "uris": [magnet],
            "uploadDate": date,
            "fileSize": size
        } if magnet else None
    except:
        return None

def main():
    links = []
    print("Собираем ссылки на все игры...")
    for p in range(1, MAX_PAGES + 1):
        page_links = get_game_links_from_page(p)
        print(f"Страница {p}/{MAX_PAGES}: найдено {len(page_links)} ссылок")
        links.extend(page_links)
        sleep(0.1)
    links = list(set(links))
    print(f"\nВсего уникальных ссылок: {len(links)}\n")

    indexed_links = [(i + 1, len(links), link) for i, link in enumerate(links)]
    print("Парсим страницы игр...")
    with ThreadPool(THREADS) as pool:
        results = pool.map(parse_game_wrapper, indexed_links)

    final = {
        "name": "Torrent-games",
        "downloads": [r for r in results if r]
    }

    print("\nСохраняем hydra_ready.json...")
    with open("torrent-games.json", "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)
    print("Готово.")

if __name__ == "__main__":
    main()
