import requests
from bs4 import BeautifulSoup
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def test_volume_all():
    r = requests.get('https://finance.naver.com/item/main.naver?code=005930', headers=HEADERS)
    r.encoding = 'euc-kr'
    s = BeautifulSoup(r.text, 'html.parser')
    
    # Loop over all table.no_info
    for table in s.select('.no_info'):
        for td in table.select('td, th'):
            # Print text to see structure
            text = td.text.strip().replace('\n', ' ')
            # Print if contains volume-like keywords
            if '거래량' in text:
                print("Found cell with '거래량':", repr(text))
                # Print its sibling or elements inside it
                print("HTML:", td)
                # Naver usually has td containing span.sise_volume ("거래량") and span.blind (the actual number)
                blind = td.select_one('.blind')
                if blind:
                    print("Volume value:", blind.text.strip())

test_volume_all()
