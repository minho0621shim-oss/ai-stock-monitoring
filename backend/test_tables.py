import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def test_tables():
    r = requests.get('https://finance.naver.com/item/main.naver?code=005930', headers=HEADERS)
    r.encoding = 'euc-kr'
    s = BeautifulSoup(r.text, 'html.parser')
    
    # Print all tables class names
    for i, table in enumerate(s.select('table')):
        print(f"Table {i} class: {table.get('class')}")
        # Print first few chars of text
        text = table.text.strip().replace('\n', ' ')[:100]
        # print safe characters only
        safe_text = "".join([c if ord(c) < 128 else '?' for c in text])
        print(f"  Text: {safe_text}")

test_tables()
