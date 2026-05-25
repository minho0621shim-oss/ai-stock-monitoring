import requests
from bs4 import BeautifulSoup
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def parse_stock(code):
    r = requests.get(f'https://finance.naver.com/item/main.naver?code={code}', headers=HEADERS)
    r.encoding = 'euc-kr'
    s = BeautifulSoup(r.text, 'html.parser')
    
    # Current Price
    no_today = s.select_one('.no_today')
    price = "0"
    if no_today:
        blind_span = no_today.select_one('.blind')
        if blind_span:
            price = blind_span.text.strip()
            
    # Change & Direction
    no_exday = s.select_one('.no_exday')
    change = "0"
    trend = "up"
    if no_exday:
        text = no_exday.text.strip()
        
        # Get point change and percentage change from blind spans if possible
        blind_spans = no_exday.select('.blind')
        if len(blind_spans) >= 2:
            point_change = blind_spans[0].text.strip()
            pct_change = blind_spans[1].text.strip()
        else:
            nums = re.findall(r'[\d,]+(?:\.\d+)?', text)
            point_change = nums[0] if len(nums) > 0 else "0"
            pct_change = nums[1] + "%" if len(nums) > 1 else "0%"
        
        # Determine trend based on whether it rose or fell
        # We can look for ico_up/ico_down or text
        is_up = False
        ico = no_exday.select_one('.ico')
        if ico:
            # Naver often has <span class="ico up"> or <span class="ico down">
            classes = ico.get('class', [])
            if 'up' in classes or 'ico_up' in classes:
                is_up = True
        elif '상승' in text or '우상향' in text or '+' in text:
            is_up = True
            
        trend = "up" if is_up else "down"
        sign = "+" if trend == "up" else "-"
        
        # Check if pct_change has percentage sign
        if not pct_change.endswith('%'):
            pct_change += '%'
        
        if pct_change.startswith('+') or pct_change.startswith('-'):
            change = f"{point_change} ({pct_change})"
        else:
            change = f"{point_change} ({sign}{pct_change})"
            
    return {"price": price, "change": change, "trend": trend}

print("Samsung:", parse_stock("005930"))
print("Celltrion:", parse_stock("068270"))
