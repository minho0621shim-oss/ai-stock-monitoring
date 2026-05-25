import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def dump_tables():
    r = requests.get('https://finance.naver.com/item/main.naver?code=005930', headers=HEADERS)
    r.encoding = 'euc-kr'
    s = BeautifulSoup(r.text, 'html.parser')
    
    with open('table_dump.txt', 'w', encoding='utf-8') as f:
        for i, table in enumerate(s.select('.no_info')):
            f.write(f"=== Table {i} ===\n")
            f.write(table.prettify())
            f.write("\n\n")

dump_tables()
print("Dumped tables to table_dump.txt")
