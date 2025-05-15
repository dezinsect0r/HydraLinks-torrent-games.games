import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime
from multiprocessing.pool import ThreadPool
from time import sleep
from random import uniform
import bencodepy
import hashlib
from urllib.parse import urljoin

BASE_URL = "https://torrent-games.games"
HEADERS = {'User-Agent': 'Mozilla/5.0'}
MAX_PAGES = 2574
THREADS = 32
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

def parse_game(url):
    try:
        sleep(uniform(*DELAY_RANGE))
        r = requests.get(url, headers=HEADERS, timeout=15)
        s = BeautifulSoup(r.text, 'html.parser')
        title = s.select_one('h1').text.strip()
        t_tag = s.select_one('#page__dl a[href*="do=download"]')
        torrent = urljoin(BASE_URL, t_tag['href']) if t_tag else ""
        magnet = torrent_to_magnet(torrent, title) if torrent else ""
        date_li = s.find('li', string=re.compile("Дата"))
        date = datetime.strptime(re.search(r'\d{2}\.\d{2}\.\d{4}', date_li.text).group(), "%d.%m.%Y").isoformat() + "Z" if date_li else "N/A"
        size_li = s.find('li', string=re.compile("Размер"))
        size = re.search(r'[\d.]+\s?[Гг][Бб]', size_li.text).group(0) if size_li else "N/A"
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
    for p in range(1, MAX_PAGES + 1):
        links.extend(get_game_links_from_page(p))
        sleep(0.1)
    links = list(set(links))
    with ThreadPool(THREADS) as pool:
        results = pool.map(parse_game, links)
    final = {
        "name": "Torrent-games",
        "downloads": [r for r in results if r]
    }
    with open("torrent-games.json", "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
