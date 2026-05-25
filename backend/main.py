import asyncio
import logging
import datetime
import ast
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scraper import scrape_indices_and_trends, scrape_news, scrape_stock_details, init_stock_master, get_stock_master, parse_stock

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
    "trends": [],
    "news": [],
    "popular_news": [],
    "stock_details": {
        "KOSPI": {"반도체": [], "바이오": [], "AI 피지컬": []},
        "KOSDAQ": {"반도체": [], "바이오": [], "AI 피지컬": []}
    }
}

async def periodic_scraper():
    """Background task to scrape indices, stock details, and news every 30s."""
    global latest_market_data
    
    while True:
        try:
            # 1. Scrape indices (every 30 seconds)
            indices_data = scrape_indices_and_trends()
            latest_market_data.update(indices_data)
            
            # 2. Scrape stock details (every 30 seconds)
            stock_data = scrape_stock_details()
            latest_market_data["stock_details"] = stock_data
            
            # 3. Scrape news (every 30 seconds)
            news_data = scrape_news()
            if news_data.get("recent"):
                latest_market_data["news"] = news_data["recent"]
            if news_data.get("popular"):
                latest_market_data["popular_news"] = news_data["popular"]
                
            logger.info("Successfully scraped latest Naver Finance INDICES, STOCK DETAILS, and NEWS data.")
        except Exception as e:
            logger.error(f"Failed to scrape Naver Finance: {e}")
            
        await asyncio.sleep(30)

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
            "pct_val": 0.0
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
