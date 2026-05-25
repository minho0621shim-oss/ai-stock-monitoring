import requests
from bs4 import BeautifulSoup
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def test_volume():
    r = requests.get('https://finance.naver.com/item/main.naver?code=005930', headers=HEADERS)
    r.encoding = 'euc-kr'
    s = BeautifulSoup(r.text, 'html.parser')
    
    # Let's search for any element containing "거래량"
    volume = "N/A"
    
    # Method 1: Look at the table.no_info
    no_info = s.select_one('.no_info')
    if no_info:
        # Let's look for td that contains '거래량'
        for td in no_info.select('td'):
            if '거래량' in td.text:
                blind = td.select_one('.blind')
                if blind:
                    volume = blind.text.strip()
                    print("Found via no_info td:", volume)
                    break
                    
    # Method 2: Look at the summary table
    if volume == "N/A":
        # Search all tds
        for td in s.select('td'):
            if '거래량' in td.text:
                print("TD text:", repr(td.text))
                # print siblings or blind
                blind = td.select_one('.blind')
                if blind:
                    print("Blind inside td:", blind.text)
                
test_volume()
