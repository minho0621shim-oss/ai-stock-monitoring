import asyncio
import logging
import datetime
import ast
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scraper import scrape_indices_and_trends, scrape_news, scrape_stock_details, init_stock_master, get_stock_master, parse_stock, HEADERS

logger = logging.getLogger(__name__)

app = FastAPI(title="AI Stock Monitoring Service", version="1.0.0")

# Setup CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state to hold the latest scraped data
latest_market_data = {
    "market": {
        "kospi": {"value": "Loading...", "change": "0", "trend": "up"},
        "kosdaq": {"value": "Loading...", "change": "0", "trend": "up"}
    },
    "insight": "AI is gathering data...",
    "trends": {
        "kospi": [],
        "kosdaq": []
    },
    "news": [],
    "popular_news": [],
    "stock_details": {
        "KOSPI": {"반도체": [], "바이오": [], "AI 피지컬": [], "MLCC": []},
        "KOSDAQ": {"반도체": [], "바이오": [], "AI 피지컬": [], "MLCC": []}
    }
}

async def periodic_scraper():
    """Background task to scrape indices, stock details, and news every 60s."""
    global latest_market_data
    
    while True:
        try:
            # 1. Scrape indices (every 60 seconds)
            indices_data = scrape_indices_and_trends()
            latest_market_data.update(indices_data)
            
            # 2. Scrape stock details (every 60 seconds)
            stock_data = scrape_stock_details()
            latest_market_data["stock_details"] = stock_data
            
            # 3. Scrape news (every 60 seconds)
            news_data = scrape_news()
            if news_data.get("recent"):
                latest_market_data["news"] = news_data["recent"]
            if news_data.get("popular"):
                latest_market_data["popular_news"] = news_data["popular"]
                
            logger.info("Successfully scraped latest Naver Finance INDICES, STOCK DETAILS, and NEWS data.")
        except Exception as e:
            logger.error(f"Failed to scrape Naver Finance: {e}")
            
        await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    """Start background tasks on startup."""
    init_stock_master()
    asyncio.create_task(periodic_scraper())

@app.get("/")
def read_root():
    return {"message": "AI Stock Monitoring API is running"}

@app.get("/api/dashboard")
def get_dashboard_data():
    """Returns the latest scraped dashboard data."""
    return latest_market_data

@app.get("/api/stocks/search")
def search_stocks(query: str = ""):
    """Searches through KOSPI & KOSDAQ stock master list by name or code."""
    query = query.strip().lower()
    if not query:
        return []
    
    master = get_stock_master()
    matches = []
    
    for code, info in master.items():
        name = info["name"]
        market = info["market"]
        # Match by name substring or exact code prefix
        if query in name.lower() or query in code:
            matches.append({
                "name": name,
                "code": code,
                "market": market
            })
            if len(matches) >= 15: # limit results to 15
                break
                
    return matches

@app.get("/api/stocks/{code}")
def get_stock_detail(code: str):
    """Scrapes and returns live details for a single stock code."""
    try:
        details = parse_stock(code)
        # Add name and code to details
        master = get_stock_master()
        name = master.get(code, {}).get("name", "알 수 없음")
        details["name"] = name
        details["code"] = code

        # Fetch investor trend
        trend_url = f"https://m.stock.naver.com/api/stock/{code}/trend"
        try:
            tr = requests.get(trend_url, headers=HEADERS)
            if tr.status_code == 200:
                trend_data = tr.json()
                if trend_data and len(trend_data) > 0:
                    latest_trend = trend_data[0]
                    close_price_str = latest_trend.get("closePrice", "0")
                    
                    def format_inv(qty_str):
                        if not qty_str:
                            return {"volume": "0주", "amount": "0원", "trend": "up"}
                        qty_val = float(qty_str.replace(",", "").replace("+", "").replace("-", "").strip())
                        sign = -1 if "-" in qty_str else 1
                        price_val = float(close_price_str.replace(",", "").strip())
                        krw = qty_val * price_val * sign
                        
                        eok = krw / 100_000_000.0
                        if abs(eok) >= 10000:
                            amount_str = f"{eok/10000.0:+.2f}조 원"
                        else:
                            amount_str = f"{eok:+.1f}억 원"
                            
                        # Format volume
                        vol_val = int(qty_str.replace(",", "").replace("+", "").replace("-", "").strip())
                        vol_sign = "-" if "-" in qty_str else "+"
                        vol_str = f"{vol_sign}{vol_val:,}주"
                        
                        return {
                            "volume": vol_str,
                            "amount": amount_str,
                            "trend": "up" if sign >= 0 else "down"
                        }
                    
                    details["investor_trend"] = {
                        "individual": format_inv(latest_trend.get("individualPureBuyQuant")),
                        "foreigner": format_inv(latest_trend.get("foreignerPureBuyQuant")),
                        "organ": format_inv(latest_trend.get("organPureBuyQuant"))
                    }
        except Exception as te:
            logger.error(f"Error fetching investor trend for {code}: {te}")

        if "investor_trend" not in details:
            details["investor_trend"] = {
                "individual": {"volume": "N/A", "amount": "N/A", "trend": "up"},
                "foreigner": {"volume": "N/A", "amount": "N/A", "trend": "up"},
                "organ": {"volume": "N/A", "amount": "N/A", "trend": "up"}
            }

        return details
    except Exception as e:
        logger.error(f"Error fetching stock details for {code}: {e}")
        return {
            "name": "알 수 없음",
            "code": code,
            "price": "N/A",
            "change": "N/A",
            "trend": "up",
            "volume": "N/A",
            "pct_val": 0.0,
            "investor_trend": {
                "individual": {"volume": "N/A", "amount": "N/A", "trend": "up"},
                "foreigner": {"volume": "N/A", "amount": "N/A", "trend": "up"},
                "organ": {"volume": "N/A", "amount": "N/A", "trend": "up"}
            }
        }

@app.get("/api/chart/{code}")
def get_chart_data(code: str, timeframe: str = "month3"):
    """Fetches and returns historical chart data for a stock code from Naver siseJson."""
    today = datetime.date.today()
    if timeframe == 'day':
        # Last 45 days (to ensure ~30 trading days)
        start = today - datetime.timedelta(days=45)
        naver_tf = 'day'
    elif timeframe == 'week':
        # Last 90 days
        start = today - datetime.timedelta(days=90)
        naver_tf = 'day'
    elif timeframe == 'month3':
        # Last 150 days
        start = today - datetime.timedelta(days=150)
        naver_tf = 'day'
    elif timeframe == 'year':
        # Last 380 days
        start = today - datetime.timedelta(days=380)
        naver_tf = 'day'
    elif timeframe == 'year3':
        # Last 4 years (to get weekly candles)
        start = today - datetime.timedelta(days=4 * 365)
        naver_tf = 'week'
    elif timeframe == 'year5':
        # Last 7 years (to get monthly candles)
        start = today - datetime.timedelta(days=7 * 365)
        naver_tf = 'month'
    else:
        start = today - datetime.timedelta(days=150)
        naver_tf = 'day'

    start_str = start.strftime('%Y%m%d')
    end_str = today.strftime('%Y%m%d')
    
    url = f"https://api.finance.naver.com/siseJson.naver?symbol={code}&requestType=1&startTime={start_str}&endTime={end_str}&timeframe={naver_tf}"
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        raw_text = r.text.strip()
        data = ast.literal_eval(raw_text)
        
        parsed_data = []
        for row in data[1:]: # skip headers
            if len(row) >= 6:
                date_str = str(row[0])
                # Format to YYYY-MM-DD
                formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
                parsed_data.append({
                    "time": formatted_date,
                    "open": float(row[1]),
                    "high": float(row[2]),
                    "low": float(row[3]),
                    "close": float(row[4]),
                    "volume": float(row[5])
                })
        return parsed_data
    except Exception as e:
        logger.error(f"Error fetching historical chart data for {code}: {e}")
        # Return fallback mock data
        parsed_data = []
        curr = today - datetime.timedelta(days=30)
        for i in range(30):
            parsed_data.append({
                "time": curr.strftime('%Y-%m-%d'),
                "open": 70000.0 + i*100,
                "high": 71000.0 + i*100,
                "low": 69000.0 + i*100,
                "close": 70500.0 + i*100,
                "volume": 1000000.0
            })
            curr += datetime.timedelta(days=1)
        return parsed_data

@app.get("/api/stocks/{code}/news")
def get_stock_news(code: str):
    """Fetches stock-specific news, filtering global popular news if possible, fallback to stock's latest news."""
    try:
        master = get_stock_master()
        stock_name = master.get(code, {}).get("name", "")
        
        # 1. Fetch latest stock-specific news
        stock_news_url = f"https://m.stock.naver.com/api/news/stock/{code}?pageSize=10"
        latest_news = []
        try:
            r = requests.get(stock_news_url, headers=HEADERS)
            if r.status_code == 200:
                data = r.json()
                for group in data:
                    for item in group.get("items", []):
                        title = item.get("titleFull") or item.get("title")
                        oid = item.get("officeId")
                        aid = item.get("articleId")
                        office = item.get("officeName")
                        dt = item.get("datetime", "")
                        
                        formatted_date = ""
                        if len(dt) >= 12:
                            formatted_date = f"{dt[:4]}-{dt[4:6]}-{dt[6:8]} {dt[8:10]}:{dt[10:12]}"
                        else:
                            formatted_date = dt
                            
                        link = f"https://n.news.naver.com/mnews/article/{oid}/{aid}" if oid and aid else ""
                        latest_news.append({
                            "title": title,
                            "link": link,
                            "office": office,
                            "date": formatted_date,
                            "is_popular": False
                        })
        except Exception as ne:
            logger.error(f"Error fetching stock latest news for {code}: {ne}")
            
        # 2. Try to find if there are matching global popular news (from Naver Finance rank page)
        popular_news_matches = []
        try:
            rank_url = 'https://finance.naver.com/news/news_list.naver?mode=RANK'
            rank_resp = requests.get(rank_url, headers=HEADERS)
            if rank_resp.status_code == 200:
                from bs4 import BeautifulSoup
                rank_soup = BeautifulSoup(rank_resp.text, 'html.parser')
                hot_items = rank_soup.select('.hotNewsList li a')
                for item in hot_items:
                    title = item.text.strip()
                    link_href = item.get('href', '')
                    if stock_name and stock_name.lower() in title.lower():
                        final_link = "https://finance.naver.com" + link_href
                        if "article_id" in link_href and "office_id" in link_href:
                            params = dict(x.split('=') for x in link_href.split('?')[-1].split('&') if '=' in x)
                            oid = params.get("office_id") or params.get("officeId")
                            aid = params.get("article_id") or params.get("articleId")
                            if oid and aid:
                                final_link = f"https://n.news.naver.com/mnews/article/{oid}/{aid}"
                                
                        popular_news_matches.append({
                            "title": title,
                            "link": final_link,
                            "office": "네이버 뉴스(인기)",
                            "date": "인기 뉴스",
                            "is_popular": True
                        })
        except Exception as pe:
            logger.error(f"Error matching global popular news for {code}: {pe}")
            
        # 3. Combine them: popular matches first, then latest
        combined = []
        seen_links = set()
        
        for item in popular_news_matches:
            if item["link"] not in seen_links:
                combined.append(item)
                seen_links.add(item["link"])
                
        for item in latest_news:
            if item["link"] not in seen_links:
                combined.append(item)
                seen_links.add(item["link"])
                
        return combined[:3]
    except Exception as e:
        logger.error(f"Error compiling news list for code {code}: {e}")
        return []
