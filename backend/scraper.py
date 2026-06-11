import requests
from bs4 import BeautifulSoup
import logging
import re
import os
import json
import time
import datetime
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
        "로봇": [
            {"name": "현대차", "code": "005380"},
            {"name": "현대모비스", "code": "012330"},
            {"name": "두산로보틱스", "code": "454910"},
            {"name": "현대오토에버", "code": "307950"},
            {"name": "한화에어로스페이스", "code": "012450"}
        ],
        "AI 서비스": [
            {"name": "NAVER", "code": "035420"},
            {"name": "카카오", "code": "035720"},
            {"name": "삼성SDS", "code": "018260"},
            {"name": "포스코DX", "code": "022100"},
            {"name": "KT", "code": "030200"}
        ],
        "MLCC": [
            {"name": "삼성전기", "code": "009150"},
            {"name": "삼화콘덴서", "code": "001820"},
            {"name": "코스모신소재", "code": "005070"},
            {"name": "삼화전자", "code": "011230"},
            {"name": "대덕전자", "code": "353200"}
        ],
        "전력 수급": [
            {"name": "HD현대일렉트릭", "code": "267260"},
            {"name": "LS일렉트릭", "code": "010120"},
            {"name": "한국전력", "code": "015760"},
            {"name": "효성중공업", "code": "298040"},
            {"name": "대한전선", "code": "001440"}
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
        "로봇": [
            {"name": "레인보우로보틱스", "code": "277810"},
            {"name": "뉴로메카", "code": "348340"},
            {"name": "에스피지", "code": "058610"},
            {"name": "로보스타", "code": "090360"},
            {"name": "로보티즈", "code": "108490"}
        ],
        "AI 서비스": [
            {"name": "루닛", "code": "328130"},
            {"name": "셀바스AI", "code": "108860"},
            {"name": "솔트룩스", "code": "304100"},
            {"name": "마음AI", "code": "377480"},
            {"name": "코난테크놀로지", "code": "402030"}
        ],
        "MLCC": [
            {"name": "대주전자재료", "code": "078600"},
            {"name": "아모텍", "code": "052710"},
            {"name": "아바텍", "code": "149950"},
            {"name": "상신전자", "code": "263810"},
            {"name": "아바코", "code": "074430"}
        ],
        "전력 수급": [
            {"name": "제룡전기", "code": "033100"},
            {"name": "서전기전", "code": "189860"},
            {"name": "대양전기공업", "code": "108380"},
            {"name": "서호전기", "code": "065710"},
            {"name": "세명전기", "code": "017510"}
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
        is_down = False
        ico = no_exday.select_one('.ico')
        if ico:
            classes = ico.get('class', [])
            if any('up' in c for c in classes):
                is_up = True
            elif any('down' in c for c in classes):
                is_down = True
        
        # Fallback to text check if no ico or no clear direction class
        if not is_up and not is_down:
            if '상승' in text or '우상향' in text or '+' in text or '상한' in text:
                is_up = True
            elif '하락' in text or '우하향' in text or '-' in text or '하한' in text:
                is_down = True
            
        if point_change == "0" or (not is_up and not is_down):
            trend = "flat"
            sign = ""
        else:
            trend = "up" if is_up else "down"
            sign = "+" if trend == "up" else "-"
        
        # Parse pct_val as numeric float for calculations (sorting/filtering)
        try:
            clean_pct = pct_change.strip().replace('%', '').replace('+', '').replace('-', '').strip()
            pct_val = float(clean_pct)
            if trend == "down":
                pct_val = -pct_val
            elif trend == "flat":
                pct_val = 0.0
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
    results = {}
    for market, categories in STOCKS.items():
        results[market] = {cat: [] for cat in categories}
    
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

    # Use 20 threads since we have 40 stocks to scrape
    with ThreadPoolExecutor(max_workers=20) as executor:
        fetched = list(executor.map(fetch_one, to_fetch))
        
    for market, category, res in fetched:
        results[market][category].append(res)
        
    # Mark the highest pct_val stock in each category as "top_surged"
    for market in ["KOSPI", "KOSDAQ"]:
        for category in results[market]:
            stocks = results[market][category]
            if stocks:
                # Find positive surged ones
                surged_stocks = [s for s in stocks if s.get("pct_val", 0.0) > 0.0]
                if surged_stocks:
                    highest = max(surged_stocks, key=lambda x: x["pct_val"])
                    highest["top_surged"] = True
                    
    return results

def generate_ai_reports(stock_data=None):
    """
    Dynamically generates AI reports based on the latest scraped stock details.
    Prepend a server generation time to demonstrate report generation on startup/refresh.
    """
    # Helper to find a stock's price/change by name in stock_data
    def get_stock_info(name):
        if not stock_data:
            return None
        for market, categories in stock_data.items():
            for category, stocks in categories.items():
                for s in stocks:
                    if s["name"] == name:
                        return s
        return None

    # Current server time to prove dynamic generation on restart
    gen_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    reports = []

    # Report 1
    s1 = get_stock_info("SK하이닉스")
    s2 = get_stock_info("삼성전자")
    s3 = get_stock_info("한미반도체")
    desc1 = f"[실시간 분석 {gen_time}] 엔비디아(NVIDIA) 중심의 AI 반도체 생태계 점검. "
    if s1 and s2 and s3:
        desc1 += f"현재 HBM 시장 1위인 SK하이닉스({s1['price']}원, {s1['change']})의 위상과 삼성전자({s2['price']}원, {s2['change']})의 기회 모색, 그리고 패키징 핵심 장비 공급사인 한미반도체({s3['price']}원, {s3['change']})의 견조함이 유지되고 있습니다."
    else:
        desc1 += "HBM(고대역폭메모리) 시장에서 SK하이닉스의 독점적 지위와 삼성전자의 맹추격, 그리고 파운드리 TSMC와의 협업 구조가 핵심. 온디바이스 AI 칩(NPU) 시장 확대에 따른 팹리스 및 디자인하우스 수혜 예상."
    reports.append({
        "title": "글로벌 AI 반도체 밸류체인 비교 리포트",
        "summary": desc1,
        "related_stocks": ["SK하이닉스", "삼성전자", "한미반도체"]
    })

    # Report 2
    s4 = get_stock_info("HD현대일렉트릭")
    s5 = get_stock_info("LS일렉트릭")
    s6 = get_stock_info("제룡전기")
    desc2 = f"[실시간 분석 {gen_time}] AI 데이터센터 가동으로 인한 전력 부족 수혜주 분석. "
    if s4 and s5 and s6:
        desc2 += f"북미 변압기 수출 호조로 HD현대일렉트릭({s4['price']}원, {s4['change']})과 LS일렉트릭({s5['price']}원, {s5['change']})의 실적 성장이 눈부시며, 중소형 변압기 공급사 제룡전기({s6['price']}원, {s6['change']})도 실적 동반 레버리지를 극대화하고 있습니다."
    else:
        desc2 += "AI 인프라 투자 확대에 따른 전력기기(HD현대일렉트릭, LS일렉트릭), 냉각시스템(데이터센터 쿨링), 유리기판 관련 소부장(소재/부품/장비) 강소기업들의 실적 점프 기대. 특히 전력 부족 현상 수혜주들이 단기 급등 후 구조적 성장 국면에 진입."
    reports.append({
        "title": "중소형 강소기업 수혜주 리포트",
        "summary": desc2,
        "related_stocks": ["HD현대일렉트릭", "LS일렉트릭", "제룡전기"]
    })

    # Report 3
    s7 = get_stock_info("이오테크닉스")
    s8 = get_stock_info("HPSP")
    s9 = get_stock_info("솔브레인")
    desc3 = f"[실시간 분석 {gen_time}] AI 반도체 미세공정 소부장 강소기업 발굴. "
    if s7 and s8 and s9:
        desc3 += f"레이저 어닐링 장비의 이오테크닉스({s7['price']}원, {s7['change']}) 및 고압 수소 어닐링 독점의 HPSP({s8['price']}원, {s8['change']})가 공정 필수 장비로 자리잡았으며, 솔브레인({s9['price']}원, {s9['change']}) 등 미세공정 소재사들의 견고한 이익률이 돋보입니다."
    else:
        desc3 += "AI 반도체 고도화(HBM, 온디바이스 AI)에 따라 필수적인 첨단 패키징(Advanced Packaging), EUV 공정, 신소재(High-K 등) 관련 중소형 장비 및 소재 기업들의 실적 레버리지 효과가 부각. 대형주 대비 밸류에이션 매력이 높고 특정 공정에서 독보적 기술력을 보유한 강소기업 집중 조명."
    reports.append({
        "title": "중소형 장비/소재주(밸류체인 하위 레이어)의 숨겨진 수혜주 발굴",
        "summary": desc3,
        "related_stocks": ["이오테크닉스", "HPSP", "솔브레인", "동진쎄미켐", "대주전자재료"]
    })

    # Report 4
    s10 = get_stock_info("삼성전기")
    s11 = get_stock_info("삼화콘덴서")
    s12 = get_stock_info("코스모신소재")
    desc4 = f"[실시간 분석 {gen_time}] 온디바이스 AI 기기 및 전장화 확산에 따른 고부가가치 MLCC 업황 확인. "
    if s10 and s11 and s12:
        desc4 += f"삼성전기({s10['price']}원, {s10['change']})의 전장 및 IT 기기용 하이엔드 MLCC 턴어라운드와 삼화콘덴서({s11['price']}원, {s11['change']})의 전기차 전장 제품 다변화, 그리고 소재 계열의 코스모신소재({s12['price']}원, {s12['change']})가 주된 흐름을 견인 중입니다."
    else:
        desc4 += "온디바이스 AI 탑재 IT 기기 확대 및 자율주행/전장화 가속에 따라 고용량·고신뢰성 MLCC(적층세라믹콘덴서) 수요가 급증하고 있습니다. 재고 조정이 마무리되며 본격적인 턴어라운드가 기대되는 주요 MLCC 관련주를 점검합니다."
    reports.append({
        "title": "전장 및 온디바이스 AI 확산: MLCC 수요 회복 및 수혜주 점검",
        "summary": desc4,
        "related_stocks": ["삼성전기", "삼화콘덴서", "코스모신소재", "대주전자재료", "아모텍"]
    })

    return reports

def scrape_indices_and_trends(stock_data=None):
    data = {
        "market": {
            "kospi": {"value": "0", "change": "0", "trend": "up"},
            "kosdaq": {"value": "0", "change": "0", "trend": "up"}
        },
        "insight": "AI Analyst is processing...",
        "trends": {
            "kospi": [],
            "kosdaq": []
        },
        "reports": generate_ai_reports(stock_data)
    }
    try:
        url = 'https://finance.naver.com/sise/'
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        response.encoding = 'euc-kr'
        soup = BeautifulSoup(response.text, 'html.parser')

        # 1. KOSPI Index
        kospi_now = soup.find(id="KOSPI_now")
        kospi_change = soup.find(id="KOSPI_change")
        if kospi_now and kospi_change:
            val = kospi_now.text.strip()
            change_text = kospi_change.text.strip()
            parts = change_text.split()
            pt = parts[0] if len(parts) > 0 else "0"
            pct = parts[1] if len(parts) > 1 else ""
            pct_clean = pct.replace("상승", "").replace("하락", "").replace("보합", "").strip()
            change_str = f"{pt} ({pct_clean})"
            
            trend = "up"
            if "하락" in change_text or "-" in change_text:
                trend = "down"
            data["market"]["kospi"] = {"value": val, "change": change_str, "trend": trend}

        # 2. KOSDAQ Index
        kosdaq_now = soup.find(id="KOSDAQ_now")
        kosdaq_change = soup.find(id="KOSDAQ_change")
        if kosdaq_now and kosdaq_change:
            val = kosdaq_now.text.strip()
            change_text = kosdaq_change.text.strip()
            parts = change_text.split()
            pt = parts[0] if len(parts) > 0 else "0"
            pct = parts[1] if len(parts) > 1 else ""
            pct_clean = pct.replace("상승", "").replace("하락", "").replace("보합", "").strip()
            change_str = f"{pt} ({pct_clean})"
            
            trend = "up"
            if "하락" in change_text or "-" in change_text:
                trend = "down"
            data["market"]["kosdaq"] = {"value": val, "change": change_str, "trend": trend}

        # 3. Trends
        def extract_trend_list(ul_id):
            trends = []
            ul = soup.find(id=ul_id)
            if ul:
                items = ul.find_all('li')
                if len(items) >= 4:
                    for idx, group_name in [(1, "개인"), (2, "외국인"), (3, "기관")]:
                        text = items[idx].text.strip()
                        amount = text.replace(group_name, "").strip()
                        trend = "up" if "+" in amount else "down"
                        trends.append({
                            "group": group_name,
                            "amount": amount,
                            "trend": trend
                        })
            return trends

        data["trends"]["kospi"] = extract_trend_list("tab_sel1_deal_trend")
        data["trends"]["kosdaq"] = extract_trend_list("tab_sel2_deal_trend")
        
        is_up = data["market"]["kospi"]["trend"] == "up"
        direction = "상승" if is_up else "하락"
        
        kospi_trends = data["trends"].get("kospi", [])
        if kospi_trends:
            actions = []
            for t in kospi_trends:
                action = "매수" if t["trend"] == "up" else "매도"
                actions.append(f"{t['group']}은 {action}")
            trend_str = ", ".join(actions)
            data["insight"] = f"코스피가 {direction} 흐름을 보이고 있습니다. 수급 주체별로 {trend_str} 우위를 보이고 있습니다."
        else:
            data["insight"] = f"코스피가 {direction} 흐름을 보이고 있습니다. 실시간 수급 동향을 주시하세요."
            
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

