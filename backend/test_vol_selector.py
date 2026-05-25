import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def test():
    r = requests.get('https://finance.naver.com/item/main.naver?code=005930', headers=HEADERS)
    s = BeautifulSoup(r.text, 'html.parser')
    sp_txt9 = s.select_one('.sp_txt9')
    if sp_txt9:
        parent = sp_txt9.parent
        blind = parent.select_one('.blind')
        if blind:
            print("Volume:", blind.text.strip())
        else:
            print("No blind found inside parent")
    else:
        print("No sp_txt9 found")

test()
