# HydraLinks-torrent-games.games

## How to run

1. Install python3 and pip:

```Shell
apt install python3 python3-pip python3-venv -y
```

2. Make and active virtual environment:

```Shell
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```Shell
pip install requests beautifulsoup4 bencodepy
```

4. Start parser:

```Shell
python torrent-games.py
```
