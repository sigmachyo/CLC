import requests

RUTUBE_CHANNEL_ID = '39733690'
RUTUBE_API_URL = f'https://rutube.ru/api/video/person/{RUTUBE_CHANNEL_ID}/?page=1&format=json'
_YT_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/122.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'ru-RU,ru;q=0.9',
}

try:
    print(f"Fetching from: {RUTUBE_API_URL}")
    resp = requests.get(RUTUBE_API_URL, timeout=15, headers=_YT_HEADERS)
    print(f"Status Code: {resp.status_code}")
    print(f"Content Type: {resp.headers.get('Content-Type')}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Results count: {len(data.get('results', []))}")
    else:
        print(f"Error Body: {resp.text[:500]}")
except Exception as e:
    print(f"Request failed: {e}")
