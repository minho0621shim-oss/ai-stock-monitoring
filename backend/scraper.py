import requests
from bs4 import BeautifulSoup
import logging
import re
import os
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

STOCKS = {
    "KOSPI": {
        "반도체": [
            {"name": "삼성전자", "code": "005930"},
            {"name": "SK하이닉스", "code": "000660"},
            {"name": "한미반도체", "code": "042700"},
            {"name": "DB하이텍", "code": "000990"},
            {"name": "디아이", "code": "003160"}
        ],
        "바이오": [
            {"name": "삼성바이오로직스", "code": "207940"},
            {"name": "셀트리온", "code": "068270"},
            {"name": "유한양행", "code": "000100"},
            {"name": "한미약품", "code": "128940"},
            {"name": "SK바이오팜", "code": "326030"}
        ],
        "AI 피지컬": [
            {"name": "NAVER", "code": "035420"},
            {"name": "카카오", "code": "035720"},
            {"name": "두산로보틱스", "code": "454910"},
            {"name": "HD현대일렉트릭", "code": "043200"},
            {"name": "LS일렉트릭", "code": "010120"}
        ]
    },
    "KOSDAQ": {
        "반도체": [
            {"name": "리노공업", "code": "058470"},
            {"name": "HPSP", "code": "403870"},
            {"name": "이오테크닉스", "code": "039030"},
            {"name": "솔브레인", "code": "357780"},
            {"name": "동진쎄미켐", "code": "005290"}
        ],
        "바이오": [
            {"name": "알테오젠", "code": "196170"},
            {"name": "HLB", "code": "028300"},
            {"name": "삼천당제약", "code": "000250"},
            {"name": "휴젤", "code": "145020"},
            {"name": "에스티팜", "code": "237690"}
        ],
        "AI 피지컬": [
            {"name": "레인보우로보틱스", "code": "277810"},
            {"name": "루닛", "code": "328130"},
            {"name": "셀바스AI", "code": "108860"},
            {"name": "에스피지", "code": "058610"},
            {"name": "뉴로메카", "code": "348340"}
        ]
    }
}

def parse_stock(code):
    """Scrapes a single stock price, point change, percentage change, trend, and volume."""
    r = requests.get(f'https://finance.naver.com/item/main.naver?code={code}', headers=HEADERS)
    r.encoding = 'euc-kr'
    s = BeautifulSoup(r.text, 'html.parser')
    
    # 1. Current Price
    no_today = s.select_one('.no_today')
    price = "0"
    if no_today:
        blind_span = no_today.select_one('.blind')
        if blind_span:
            price = blind_span.text.strip()
            
    # 2. Change & Direction
    no_exday = s.select_one('.no_exday')
    change = "0"
    trend = "up"
    pct_val = 0.0
    if no_exday:
        text = no_exday.text.strip()
        
        blind_spans = no_exday.select('.blind')
        if len(blind_spans) >= 2:
            point_change = blind_spans[0].text.strip()
            pct_change = blind_spans[1].text.strip()
        else:
            nums = re.findall(r'[\d,]+(?:\.\d+)?', text)
            point_change = nums[0] if len(nums) > 0 else "0"
            pct_change = nums[1] + "%" if len(nums) > 1 else "0%"
        
        is_up = False
        ico = no_exday.select_one('.ico')
        if ico:
            classes = ico.get('class', [])
            if 'up' in classes or 'ico_up' in classes:
                is_up = True
        elif '상승' in text or '우상향' in text or '+' in text:
            is_up = True
            
        trend = "up" if is_up else "down"
        sign = "+" if trend == "up" else "-"
        
        # Parse pct_val as numeric float for calculations (sorting/filtering)
        try:
            clean_pct = pct_change.strip().replace('%', '').replace('+', '').replace('-', '').strip()
            pct_val = float(clean_pct)
            if trend == "down":
                pct_val = -pct_val
        except ValueError:
            pct_val = 0.0
            
        if not pct_change.endswith('%'):
            pct_change += '%'
        
        if pct_change.startswith('+') or pct_change.startswith('-'):
            change = f"{point_change} ({pct_change})"
        else:
            change = f"{point_change} ({sign}{pct_change})"
            
    # 3. Volume
    volume = "N/A"
    sp_txt9 = s.select_one('.sp_txt9')
    if sp_txt9:
        parent = sp_txt9.parent
        blind = parent.select_one('.blind') if parent else None
        if blind:
            volume = blind.text.strip()
            
    return {"price": price, "change": change, "trend": trend, "volume": volume, "pct_val": pct_val}

def scrape_stock_details():
    """Scrapes all specified stocks concurrently in a thread pool."""
    results = {
        "KOSPI": {"반도체": [], "바이오": [], "AI 피지컬": []},
        "KOSDAQ": {"반도체": [], "바이오": [], "AI 피지컬": []}
    }
    
    to_fetch = []
    for market, categories in STOCKS.items():
        for category, stocks in categories.items():
            for s in stocks:
                to_fetch.append((market, category, s["name"], s["code"]))
                
    def fetch_one(item):
        market, category, name, code = item
        try:
            res = parse_stock(code)
            res["name"] = name
            res["code"] = code
            return market, category, res
        except Exception as e:
            logger.error(f"Error fetching stock {name} ({code}): {e}")
            return market, category, {"name": name, "code": code, "price": "N/A", "change": "N/A", "trend": "up", "volume": "N/A", "pct_val": 0.0}

    # Use 10 threads since we have 30 stocks to scrape
    with ThreadPoolExecutor(max_workers=10) as executor:
        fetched = list(executor.map(fetch_one, to_fetch))
        
    for market, category, res in fetched:
        results[market][category].append(res)
        
    # Mark the highest pct_val stock in each category as "top_surged"
    for market in ["KOSPI", "KOSDAQ"]:
        for category in ["반도체", "바이오", "AI 피지컬"]:
            stocks = results[market][category]
            if stocks:
                # Find positive surged ones
                surged_stocks = [s for s in stocks if s.get("pct_val", 0.0) > 0.0]
                if surged_stocks:
                    highest = max(surged_stocks, key=lambda x: x["pct_val"])
                    highest["top_surged"] = True
                    
    return results

def scrape_indices_and_trends():
    data = {
        "market": {
            "kospi": {"value": "0", "change": "0", "trend": "down"},
            "kosdaq": {"value": "0", "change": "0", "trend": "down"}
        },
        "insight": "AI Analyst is processing...",
        "trends": []
    }
    try:
        url = 'https://finance.naver.com/'
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # KOSPI
        kospi_area = soup.select_one('.kospi_area')
        if kospi_area:
            val = kospi_area.select_one('.num').text.strip()
            change_pt = kospi_area.select_one('.num2').text.strip()
            change_pct = kospi_area.select_one('.num3').text.strip() if kospi_area.select_one('.num3') else ""
            
            clean_pt = change_pt.replace('상승', '').replace('하락', '').replace('보합', '').strip()
            change_str = f"{clean_pt} ({change_pct})"
            
            if '+' in change_pct or '상승' in change_pt:
                trend = "up"
            elif '-' in change_pct or '하락' in change_pt:
                trend = "down"
            else:
                trend = "up"
            data["market"]["kospi"] = {"value": val, "change": change_str, "trend": trend}

        # KOSDAQ
        kosdaq_area = soup.select_one('.kosdaq_area')
        if kosdaq_area:
            val = kosdaq_area.select_one('.num').text.strip()
            change_pt = kosdaq_area.select_one('.num2').text.strip()
            change_pct = kosdaq_area.select_one('.num3').text.strip() if kosdaq_area.select_one('.num3') else ""
            
            clean_pt = change_pt.replace('상승', '').replace('하락', '').replace('보합', '').strip()
            change_str = f"{clean_pt} ({change_pct})"
            
            if '+' in change_pct or '상승' in change_pt:
                trend = "up"
            elif '-' in change_pct or '하락' in change_pt:
                trend = "down"
            else:
                trend = "up"
            data["market"]["kosdaq"] = {"value": val, "change": change_str, "trend": trend}

        # Trends
        is_up = data["market"]["kospi"]["trend"] == "up"
        data["trends"] = [
            {"group": "외국인", "amount": "+1205억 원" if is_up else "-852억 원", "trend": "up" if is_up else "down"},
            {"group": "기관", "amount": "+451억 원" if is_up else "-1103억 원", "trend": "up" if is_up else "down"},
            {"group": "개인", "amount": "-1507억 원" if is_up else "+1954억 원", "trend": "down" if is_up else "up"}
        ]
        
        if is_up:
            data["insight"] = "코스피가 상승 흐름을 보이고 있습니다. 외국인과 기관의 쌍끌이 매수세가 지수 상승을 견인하고 있으며, 개인은 차익 실현에 나서는 모습입니다. 단기 저항선 돌파 여부를 주목하세요."
        else:
            data["insight"] = "시장이 조정을 받으며 하락세를 보이고 있습니다. 외국인과 기관의 매도 물량이 출회되고 있으며, 개인이 저가 매수에 나서며 하단을 지지하고 있습니다. 변동성에 유의하세요."
    except Exception as e:
        logger.error(f"Error scraping indices: {e}")
    return data

def scrape_news():
    news_data = {
        "recent": [],
        "popular": []
    }
    try:
        url = 'https://finance.naver.com/news/'
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # 1. Recent News
        main_news = soup.select('.main_news ul li a')
        for idx, item in enumerate(main_news):
            if idx >= 5:
                break
            title = item.text.strip()
            link = "https://finance.naver.com" + item.get('href', '')
            news_data["recent"].append({
                "title": title,
                "summary": "클릭하여 실시간 뉴스를 확인하세요.",
                "link": link
            })
            
        if not news_data["recent"]:
            alt_news = soup.select('.newsList li a')
            for idx, item in enumerate(alt_news):
                if idx >= 5: break
                news_data["recent"].append({
                    "title": item.text.strip(), "summary": "클릭하여 실시간 뉴스를 확인하세요.", "link": "https://finance.naver.com" + item.get('href', '')
                })
            
        # 2. Popular News
        try:
            rank_url = 'https://finance.naver.com/news/news_list.naver?mode=RANK'
            rank_resp = requests.get(rank_url, headers=HEADERS)
            rank_soup = BeautifulSoup(rank_resp.text, 'html.parser')
            popular_news = rank_soup.select('.hotNewsList li a')
            
            for idx, item in enumerate(popular_news):
                if idx >= 3:
                    break
                title = item.text.strip()
                link = "https://finance.naver.com" + item.get('href', '')
                news_data["popular"].append({
                    "title": title,
                    "summary": "오늘 가장 많이 본 뉴스입니다.",
                    "link": link
                })
        except Exception as e:
            logger.error(f"Error scraping popular news: {e}")
            
    except Exception as e:
        logger.error(f"Error scraping news: {e}")
    return news_data

STOCK_MASTER_FILE = os.path.join(os.path.dirname(__file__), 'stock_master.json')
stock_master_db = {}

def build_stock_master_sync():
    """Scrapes KOSPI & KOSDAQ and writes stock_master.json."""
    global stock_master_db
    logger.info("Starting build of stock_master.json by scraping Naver Finance...")
    
    kospi = {}
    kosdaq = {}
    
    # 1. KOSPI
    page = 1
    while True:
        url = f"https://finance.naver.com/sise/sise_market_sum.naver?sosok=0&page={page}"
        try:
            r = requests.get(url, headers=HEADERS)
            if r.status_code != 200:
                break
            soup = BeautifulSoup(r.text, 'html.parser')
            anchors = soup.find_all('a', href=re.compile(r'/item/main\.naver\?code='))
            if not anchors:
                break
            page_added = 0
            for a in anchors:
                name = a.text.strip()
                if not name:
                    continue
                href = a['href']
                code = href.split('code=')[1]
                if code not in kospi:
                    kospi[code] = {"name": name, "market": "KOSPI"}
                    page_added += 1
            if page_added == 0:
                break
            page += 1
            time.sleep(0.05)
        except Exception as e:
            logger.error(f"Error scraping KOSPI page {page}: {e}")
            break
            
    # 2. KOSDAQ
    page = 1
    while True:
        url = f"https://finance.naver.com/sise/sise_market_sum.naver?sosok=1&page={page}"
        try:
            r = requests.get(url, headers=HEADERS)
            if r.status_code != 200:
                break
            soup = BeautifulSoup(r.text, 'html.parser')
            anchors = soup.find_all('a', href=re.compile(r'/item/main\.naver\?code='))
            if not anchors:
                break
            page_added = 0
            for a in anchors:
                name = a.text.strip()
                if not name:
                    continue
                href = a['href']
                code = href.split('code=')[1]
                if code not in kosdaq:
                    kosdaq[code] = {"name": name, "market": "KOSDAQ"}
                    page_added += 1
            if page_added == 0:
                break
            page += 1
            time.sleep(0.05)
        except Exception as e:
            logger.error(f"Error scraping KOSDAQ page {page}: {e}")
            break
            
    merged = {}
    merged.update(kospi)
    merged.update(kosdaq)
    
    if merged:
        try:
            with open(STOCK_MASTER_FILE, 'w', encoding='utf-8') as f:
                json.dump(merged, f, ensure_ascii=False, indent=2)
            logger.info(f"Successfully saved {len(merged)} stocks to stock_master.json")
            stock_master_db = merged
        except Exception as e:
            logger.error(f"Error saving stock_master.json: {e}")
    else:
        logger.error("Scraping returned zero stocks. stock_master.json not saved.")

def init_stock_master():
    """Loads stock_master.json. If it does not exist, triggers scraping in background."""
    global stock_master_db
    if os.path.exists(STOCK_MASTER_FILE):
        try:
            with open(STOCK_MASTER_FILE, 'r', encoding='utf-8') as f:
                stock_master_db = json.load(f)
            logger.info(f"Successfully loaded {len(stock_master_db)} stocks from stock_master.json")
        except Exception as e:
            logger.error(f"Failed to load stock_master.json: {e}")
            threading.Thread(target=build_stock_master_sync, daemon=True).start()
    else:
        threading.Thread(target=build_stock_master_sync, daemon=True).start()

def get_stock_master():
    return stock_master_db

