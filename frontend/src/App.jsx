import React, { useState, useEffect, useRef } from 'react';
import './index.css';
import { createChart, CandlestickSeries, HistogramSeries, LineSeries } from 'lightweight-charts';

const getChartAnalysis = (stock, timeframe) => {
  const isUp = stock.trend === 'up';
  const name = stock.name;
  
  const timeLabels = {
    day: '1일(당일)',
    week: '1주일',
    month3: '3개월',
    year: '1년',
    year3: '3년',
    year5: '5년'
  };

  const timeframeStr = timeLabels[timeframe] || '선택한 기간';

  if (isUp) {
    switch (timeframe) {
      case 'day':
        return `[당일 분석] ${name}은(는) 오늘 강한 매수세가 유입되며 상승 흐름을 타고 있습니다. 호가창에서 매도 잔량을 소화하는 모습이 긍정적이며, 종가 고가 형성 가능성이 높습니다. 거래량이 동반되어 신뢰도가 높습니다.`;
      case 'week':
        return `[단기 분석] 최근 1주일간 ${name}은(는) 저점을 서서히 높이며 단기 정배열 진입을 시도하고 있습니다. 5일 이동평균선 위에서 안착하는 흐름이 이어지고 있어 차주에도 긍정적인 추세 추종이 기대됩니다.`;
      case 'month3':
        return `[중기 분석] 지난 3개월간 ${name}의 차트는 완만한 우상향 채널을 형성하고 있습니다. 전고점 부근의 매물대를 돌파하기 위한 거래량 증가가 확인되며, 지지선(20일선) 이탈 전까지는 지속적인 보유 관점이 유효합니다.`;
      case 'year':
        return `[장기 분석] 1년 장기 차트 기준, ${name}은(는) 바닥권을 탈출하여 대세 상승 국면으로의 전환을 시도하고 있습니다. 매물 부담이 점차 경감되고 있으며, 실적 개선세와 함께 장기 이평선들의 골든크로스가 목전입니다.`;
      default:
        return `[장기 흐름 분석] 대세 상승 채널의 중상단에 위치해 있습니다. 역사적 고점 돌파를 시도하는 구간으로, 연간 단위 지지 라인이 탄탄하게 형성되어 있어 장기 가치 투자 매력도가 높은 상태입니다.`;
    }
  } else {
    switch (timeframe) {
      case 'day':
        return `[당일 분석] ${name}은(는) 오늘 매도세가 우위를 점하며 약세 흐름을 보이고 있습니다. 시가 대비 밀리는 음봉 흐름이 나타나고 있어, 장 마감 전까지 저가 매수세 유입 여부 및 지지 가격대 수성을 지켜봐야 합니다.`;
      case 'week':
        return `[단기 분석] 최근 1주일간 단기 매물이 출회되며 조정세를 겪고 있습니다. 5일선이 하향 꺾인 상태로 단기 반등 모멘텀이 다소 둔화되었습니다. 추가 하락 시 지지선에서의 기술적 반등 여부를 체크해야 합니다.`;
      case 'month3':
        return `[중기 분석] 3개월 중기 차트 관점에서 하향 횡보 흐름이 이어지고 있습니다. 전저점 지지 테스트가 지속되는 국면이며, 거래량이 급감한 상태에서의 조정이므로 하방 경직성을 확보한 후 반등 기회를 모색할 것으로 판단됩니다.`;
      case 'year':
        return `[장기 분석] 1년 장기 차트 기준, ${name}은(는) 상단의 두터운 매물대 저항에 막혀 하향 돌파가 발생했습니다. 장기 이동평균선이 역배열 상태로 수렴하는 중이므로, 바닥 다지기 확인을 위한 관망세가 필요한 구간입니다.`;
      default:
        return `[장기 흐름 분석] 역사적 지지선 부근까지 하락한 과매도 상태로 보입니다. 추가 낙폭은 제한적일 수 있으나, 본격적인 추세 전환 신호(대량 거래 동반 양봉)가 나오기 전까지는 성급한 추격 매수보다는 보수적 접근이 안전합니다.`;
    }
  }
};

const getTechnicalIndicators = (stock, timeframe) => {
  const isUp = stock.trend === 'up';
  const codeVal = parseInt(stock.code) || 0;
  
  let score = 50;
  if (isUp) {
    score = 72 + (codeVal % 18);
    if (timeframe === 'day') score += 6;
    if (timeframe === 'week') score += 3;
    if (timeframe === 'year5') score -= 5;
  } else {
    score = 22 + (codeVal % 18);
    if (timeframe === 'day') score -= 8;
    if (timeframe === 'week') score -= 4;
    if (timeframe === 'year5') score += 4;
  }
  score = Math.min(Math.max(score, 5), 98);

  let consensus = '중립/관망';
  let consensusColor = 'var(--text-muted)';
  let consensusClass = 'consensus-neutral';
  if (score >= 80) {
    consensus = '적극 매수';
    consensusColor = 'var(--accent-red)';
    consensusClass = 'consensus-strong-buy';
  } else if (score >= 60) {
    consensus = '매수';
    consensusColor = '#fca5a5';
    consensusClass = 'consensus-buy';
  } else if (score >= 40) {
    consensus = '중립/관망';
    consensusColor = 'var(--text-muted)';
    consensusClass = 'consensus-neutral';
  } else if (score >= 20) {
    consensus = '매도';
    consensusColor = '#93c5fd';
    consensusClass = 'consensus-sell';
  } else {
    consensus = '적극 매도';
    consensusColor = 'var(--accent-blue)';
    consensusClass = 'consensus-strong-sell';
  }

  const rsi = isUp ? (58 + (codeVal % 15)) : (22 + (codeVal % 15));
  const macd = isUp ? '골든크로스 / 매수 신호' : '데드크로스 / 매도 신호';
  const bband = isUp ? '상한선 돌파 시도' : '하한선 지지력 테스트';
  const ma = isUp ? '이평선 정배열 안착' : '이평선 역배열 지속';

  let stochK = 50;
  let stochD = 50;
  if (isUp) {
    stochK = 70 + (codeVal % 18);
    stochD = stochK - 3 - (codeVal % 3);
  } else {
    stochK = 10 + (codeVal % 18);
    stochD = stochK + 2 + (codeVal % 3);
  }
  const stochSignal = stochK >= 80 ? '과열' : stochK <= 20 ? '침체' : '중립';
  const stochVal = `%K: ${stochK}, %D: ${stochD} (${stochSignal})`;

  const obvBase = 50000 + (codeVal % 100) * 1000;
  const obvVal = isUp ? `${(obvBase * 1.5).toLocaleString()}K (상승 흐름)` : `${(obvBase * 0.8).toLocaleString()}K (하향 횡보)`;

  return {
    score,
    consensus,
    consensusColor,
    consensusClass,
    rsi,
    macd,
    bband,
    ma,
    stoch: stochVal,
    obv: obvVal
  };
};

const calculateMA = (data, period) => {
  const maData = [];
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) continue;
    let sum = 0;
    for (let j = 0; j < period; j++) {
      sum += data[i - j].close;
    }
    maData.push({
      time: data[i].time,
      value: sum / period,
    });
  }
  return maData;
};

const TradingViewWidget = ({ symbol, timeframe }) => {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { color: '#0f172a' }, // Slate 900
        textColor: '#94a3b8',
      },
      grid: {
        vertLines: { color: 'rgba(51, 65, 85, 0.3)' },
        horzLines: { color: 'rgba(51, 65, 85, 0.3)' },
      },
      crosshair: {
        mode: 0,
      },
      rightPriceScale: {
        borderColor: 'rgba(51, 65, 85, 0.5)',
      },
      timeScale: {
        borderColor: 'rgba(51, 65, 85, 0.5)',
        timeVisible: true,
        secondsVisible: false,
      },
    });
    chartRef.current = chart;

    // Candlestick series (Korean standard colors: Red = Up, Blue = Down)
    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#ef4444',
      downColor: '#3b82f6',
      borderUpColor: '#ef4444',
      borderDownColor: '#3b82f6',
      wickUpColor: '#ef4444',
      wickDownColor: '#3b82f6',
    });

    // 5-day MA (Yellow)
    const ma5Series = chart.addSeries(LineSeries, {
      color: '#eab308',
      lineWidth: 1.5,
      priceLineVisible: false,
    });

    // 20-day MA (Pink)
    const ma20Series = chart.addSeries(LineSeries, {
      color: '#ec4899',
      lineWidth: 2,
      priceLineVisible: false,
    });

    // 60-day MA (Cyan)
    const ma60Series = chart.addSeries(LineSeries, {
      color: '#06b6d4',
      lineWidth: 2,
      priceLineVisible: false,
    });

    // Volume series (overlay on bottom 20%)
    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '',
    });
    volumeSeries.priceScale().applyOptions({
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    });

    setLoading(true);
    setError(null);

    // Fetch historical data
    fetch(`http://localhost:8000/api/chart/${symbol}?timeframe=${timeframe}`)
      .then((res) => {
        if (!res.ok) throw new Error('차트 데이터를 불러오지 못했습니다.');
        return res.json();
      })
      .then((data) => {
        if (!data || data.length === 0) {
          throw new Error('차트 데이터가 비어 있습니다.');
        }

        const sortedData = [...data].sort((a, b) => new Date(a.time) - new Date(b.time));

        const candleData = sortedData.map((item) => ({
          time: item.time,
          open: item.open,
          high: item.high,
          low: item.low,
          close: item.close,
        }));

        const volumeData = sortedData.map((item) => ({
          time: item.time,
          value: item.volume,
          color: item.close >= item.open ? 'rgba(239, 68, 68, 0.4)' : 'rgba(59, 130, 246, 0.4)',
        }));

        // Calculate moving averages
        const ma5Data = calculateMA(sortedData, 5);
        const ma20Data = calculateMA(sortedData, 20);
        const ma60Data = calculateMA(sortedData, 60);

        candlestickSeries.setData(candleData);
        volumeSeries.setData(volumeData);
        ma5Series.setData(ma5Data);
        ma20Series.setData(ma20Data);
        ma60Series.setData(ma60Data);

        chart.timeScale().fitContent();
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching stock chart data:", err);
        setError(err.message);
        setLoading(false);
      });

    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        const { clientWidth, clientHeight } = chartContainerRef.current;
        chartRef.current.resize(clientWidth, clientHeight || 480);
      }
    };

    window.addEventListener('resize', handleResize);
    // Trigger initial sizing after a small delay to let DOM settle
    const timer = setTimeout(handleResize, 100);

    return () => {
      window.removeEventListener('resize', handleResize);
      clearTimeout(timer);
      chart.remove();
    };
  }, [symbol, timeframe]);

  return (
    <div className="tradingview-widget-container" style={{ width: '100%', height: '100%', minHeight: '480px', position: 'relative', background: '#0f172a', borderRadius: '8px', overflow: 'hidden' }}>
      {/* Chart Legend */}
      <div style={{
        position: 'absolute',
        top: '12px',
        left: '12px',
        zIndex: 10,
        background: 'rgba(15, 23, 42, 0.75)',
        backdropFilter: 'blur(4px)',
        border: '1px solid var(--border-color)',
        borderRadius: '6px',
        padding: '0.4rem 0.6rem',
        fontSize: '0.75rem',
        display: 'flex',
        gap: '0.8rem',
        pointerEvents: 'none'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
          <span style={{ display: 'inline-block', width: '10px', height: '3px', background: '#eab308' }} />
          <span style={{ color: '#eab308', fontWeight: '600' }}>5일선</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
          <span style={{ display: 'inline-block', width: '10px', height: '3px', background: '#ec4899' }} />
          <span style={{ color: '#ec4899', fontWeight: '600' }}>20일선</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
          <span style={{ display: 'inline-block', width: '10px', height: '3px', background: '#06b6d4' }} />
          <span style={{ color: '#06b6d4', fontWeight: '600' }}>60일선</span>
        </div>
      </div>

      {loading && (
        <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, display: 'flex', justifyContent: 'center', alignItems: 'center', background: 'rgba(15, 23, 42, 0.8)', color: '#94a3b8', zIndex: 10, fontSize: '0.95rem' }}>
          차트 데이터를 불러오는 중...
        </div>
      )}
      {error && (
        <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, display: 'flex', justifyContent: 'center', alignItems: 'center', background: 'rgba(15, 23, 42, 0.8)', color: '#f87171', zIndex: 10, fontSize: '0.95rem', padding: '1rem', textAlign: 'center' }}>
          ⚠️ 에러: {error}
        </div>
      )}
      <div ref={chartContainerRef} style={{ width: '100%', height: '100%', minHeight: '480px' }} />
    </div>
  );
};

function App() {
  const [data, setData] = useState(null);
  const [selectedStock, setSelectedStock] = useState(null);
  const [chartTimeframe, setChartTimeframe] = useState('month3');
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [stockNews, setStockNews] = useState([]);
  const [loadingNews, setLoadingNews] = useState(false);
  const [hoveredIndicator, setHoveredIndicator] = useState(null);
  const suggestionRef = useRef(null);

  // Fetch stock-specific news
  useEffect(() => {
    if (!selectedStock?.code) {
      setStockNews([]);
      return;
    }
    setLoadingNews(true);
    fetch(`http://localhost:8000/api/stocks/${selectedStock.code}/news`)
      .then(res => res.json())
      .then(news => {
        setStockNews(news || []);
        setLoadingNews(false);
      })
      .catch(err => {
        console.error("Error fetching stock news:", err);
        setStockNews([]);
        setLoadingNews(false);
      });
  }, [selectedStock?.code]);

  // Fetch suggestions as the user types
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSuggestions([]);
      return;
    }

    const timer = setTimeout(() => {
      fetch(`http://localhost:8000/api/stocks/search?query=${encodeURIComponent(searchQuery.trim())}`)
        .then(res => res.json())
        .then(data => {
          setSuggestions(data);
        })
        .catch(err => console.error("Error fetching suggestions:", err));
    }, 200); // 200ms debounce

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Click outside to close suggestions
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (suggestionRef.current && !suggestionRef.current.contains(event.target)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelectStock = (stock) => {
    const tempStock = {
      name: stock.name,
      code: stock.code,
      price: "불러오는 중...",
      change: "계산 중...",
      trend: "up",
      volume: "불러오는 중...",
      market: stock.market
    };
    setSelectedStock(tempStock);
    setChartTimeframe('month3');
    setShowSuggestions(false);
    setSearchQuery('');

    // Fetch live details
    fetch(`http://localhost:8000/api/stocks/${stock.code}`)
      .then(res => res.json())
      .then(detail => {
        setSelectedStock(prev => {
          if (prev && prev.code === stock.code) {
            return {
              ...prev,
              price: detail.price,
              change: detail.change,
              trend: detail.trend,
              volume: detail.volume,
              investor_trend: detail.investor_trend,
              overtime: detail.overtime
            };
          }
          return prev;
        });
      })
      .catch(err => console.error("Error fetching stock details:", err));
  };

  // Handle clicking stock to open modal
  const handleStockClick = (e, stock) => {
    e.preventDefault();
    setSelectedStock(stock);
    setChartTimeframe('month3');

    // Fetch fresh live details in case they changed
    fetch(`http://localhost:8000/api/stocks/${stock.code}`)
      .then(res => res.json())
      .then(detail => {
        setSelectedStock(prev => {
          if (prev && prev.code === stock.code) {
            return {
              ...prev,
              price: detail.price,
              change: detail.change,
              trend: detail.trend,
              volume: detail.volume,
              investor_trend: detail.investor_trend,
              overtime: detail.overtime
            };
          }
          return prev;
        });
      })
      .catch(err => console.error("Error fetching stock details:", err));
  };

  const handleSearch = () => {
    if (!searchQuery.trim()) return;
    
    if (suggestions.length > 0) {
      handleSelectStock(suggestions[0]);
    } else {
      fetch(`http://localhost:8000/api/stocks/search?query=${encodeURIComponent(searchQuery.trim())}`)
        .then(res => res.json())
        .then(data => {
          if (data && data.length > 0) {
            handleSelectStock(data[0]);
          } else {
            alert(`"${searchQuery}"에 해당하는 종목을 찾을 수 없습니다.`);
          }
        })
        .catch(err => {
          console.error("Error searching stock:", err);
          alert("검색 중 에러가 발생했습니다.");
        });
    }
  };

  const fallbackData = {
    "market": {
        "kospi": {"value": "2,750.32", "change": "23.45 (+0.85%)", "trend": "up"},
        "kosdaq": {"value": "865.11", "change": "3.67 (-0.42%)", "trend": "down"}
    },
    "insight": "코스피가 2760선에서 강한 저항을 받고 있습니다. 외국인 투자자들이 기술주를 매집하고 있어 돌파 가능성이 있습니다. 전반적인 뉴스 심리는 약간의 긍정(Bullish) 상태입니다.",
    "trends": {
      "kospi": [
        {"group": "개인", "amount": "-1,047억", "trend": "down"},
        {"group": "외국인", "amount": "+1,502억", "trend": "up"},
        {"group": "기관", "amount": "-455억", "trend": "down"}
      ],
      "kosdaq": [
        {"group": "개인", "amount": "+924억", "trend": "up"},
        {"group": "외국인", "amount": "-512억", "trend": "down"},
        {"group": "기관", "amount": "-412억", "trend": "down"}
      ]
    },
    "news": [
        {"title": "삼성전자, 차세대 AI 반도체 공개", "summary": "클릭하여 실시간 뉴스를 확인하세요.", "link": "https://finance.naver.com"},
        {"title": "한국은행, 기준금리 동결 결정", "summary": "클릭하여 실시간 뉴스를 확인하세요.", "link": "https://finance.naver.com"},
        {"title": "뉴욕증시, 엔비디아 실적 호조에 급등", "summary": "클릭하여 실시간 뉴스를 확인하세요.", "link": "https://finance.naver.com"},
        {"title": "정부, 밸류업 프로그램 세부안 발표", "summary": "클릭하여 실시간 뉴스를 확인하세요.", "link": "https://finance.naver.com"},
        {"title": "현대차, 북미 전기차 공장 조기 가동", "summary": "클릭하여 실시간 뉴스를 확인하세요.", "link": "https://finance.naver.com"}
    ],
    "popular_news": [
        {"title": "오늘 가장 핫한 주식 시장 이슈 분석", "summary": "오늘 가장 많이 본 뉴스입니다.", "link": "https://finance.naver.com"},
        {"title": "외국인이 쓸어담은 저평가 우량주 3선", "summary": "오늘 가장 많이 본 뉴스입니다.", "link": "https://finance.naver.com"},
        {"title": "내일의 급등 예상 종목 리포트", "summary": "오늘 가장 많이 본 뉴스입니다.", "link": "https://finance.naver.com"}
    ],
    "stock_details": {
      "KOSPI": {
        "반도체": [
          {"name": "삼성전자", "code": "005930", "price": "78,200", "change": "1,200 (+1.56%)", "trend": "up", "volume": "18,194,628", "top_surged": false},
          {"name": "SK하이닉스", "code": "000660", "price": "185,400", "change": "3,200 (-1.70%)", "trend": "down", "volume": "3,124,512", "top_surged": false},
          {"name": "한미반도체", "code": "042700", "price": "142,300", "change": "5,400 (+3.94%)", "trend": "up", "volume": "985,612", "top_surged": true},
          {"name": "DB하이텍", "code": "000990", "price": "43,200", "change": "300 (-0.69%)", "trend": "down", "volume": "412,852", "top_surged": false},
          {"name": "디아이", "code": "003160", "price": "24,500", "change": "150 (+0.61%)", "trend": "up", "volume": "152,431", "top_surged": false}
        ],
        "바이오": [
          {"name": "삼성바이오로직스", "code": "207940", "price": "795,000", "change": "15,000 (+1.92%)", "trend": "up", "volume": "89,120", "top_surged": false},
          {"name": "셀트리온", "code": "068270", "price": "198,700", "change": "9,100 (+4.80%)", "trend": "up", "volume": "1,412,850", "top_surged": true},
          {"name": "유한양행", "code": "000100", "price": "72,100", "change": "200 (+0.28%)", "trend": "up", "volume": "245,610", "top_surged": false},
          {"name": "한미약품", "code": "128940", "price": "315,000", "change": "5,000 (-1.56%)", "trend": "down", "volume": "45,210", "top_surged": false},
          {"name": "SK바이오팜", "code": "326030", "price": "91,200", "change": "100 (-0.11%)", "trend": "down", "volume": "125,410", "top_surged": false}
        ],
        "로봇": [
          {"name": "현대차", "code": "005380", "price": "248,000", "change": "3,500 (+1.43%)", "trend": "up", "volume": "1,542,100", "top_surged": false},
          {"name": "현대모비스", "code": "012330", "price": "265,000", "change": "5,000 (+1.92%)", "trend": "up", "volume": "342,500", "top_surged": false},
          {"name": "두산로보틱스", "code": "454910", "price": "79,500", "change": "4,200 (+5.58%)", "trend": "up", "volume": "542,100", "top_surged": true},
          {"name": "현대오토에버", "code": "307950", "price": "185,000", "change": "2,000 (+1.09%)", "trend": "up", "volume": "85,400", "top_surged": false},
          {"name": "한화에어로스페이스", "code": "012450", "price": "352,000", "change": "8,000 (+2.33%)", "trend": "up", "volume": "245,100", "top_surged": false}
        ],
        "AI 서비스": [
          {"name": "NAVER", "code": "035420", "price": "185,000", "change": "3,000 (-1.60%)", "trend": "down", "volume": "895,120", "top_surged": false},
          {"name": "카카오", "code": "035720", "price": "48,200", "change": "200 (+0.42%)", "trend": "up", "volume": "1,120,450", "top_surged": false},
          {"name": "삼성SDS", "code": "018260", "price": "152,000", "change": "1,500 (-0.98%)", "trend": "down", "volume": "85,400", "top_surged": false},
          {"name": "포스코DX", "code": "022100", "price": "12,500", "change": "200 (+1.63%)", "trend": "up", "volume": "342,100", "top_surged": true},
          {"name": "KT", "code": "030200", "price": "38,500", "change": "150 (+0.39%)", "trend": "up", "volume": "542,300", "top_surged": false}
        ],
        "MLCC": [
          {"name": "삼성전기", "code": "009150", "price": "148,200", "change": "2,300 (+1.58%)", "trend": "up", "volume": "245,612", "top_surged": false},
          {"name": "삼화콘덴서", "code": "001820", "price": "38,500", "change": "450 (+1.18%)", "trend": "up", "volume": "85,612", "top_surged": false},
          {"name": "코스모신소재", "code": "005070", "price": "165,300", "change": "5,400 (+3.38%)", "trend": "up", "volume": "142,300", "top_surged": true},
          {"name": "삼화전자", "code": "011230", "price": "3,420", "change": "30 (-0.87%)", "trend": "down", "volume": "110,420", "top_surged": false},
          {"name": "대덕전자", "code": "353200", "price": "24,500", "change": "150 (-0.61%)", "trend": "down", "volume": "152,431", "top_surged": false}
        ],
        "전력 수급": [
          {"name": "HD현대일렉트릭", "code": "267260", "price": "385,000", "change": "12,500 (+3.35%)", "trend": "up", "volume": "542,100", "top_surged": true},
          {"name": "LS일렉트릭", "code": "010120", "price": "154,200", "change": "2,100 (+1.38%)", "trend": "up", "volume": "210,400", "top_surged": false},
          {"name": "한국전력", "code": "015760", "price": "22,500", "change": "350 (+1.58%)", "trend": "up", "volume": "3,542,100", "top_surged": false},
          {"name": "효성중공업", "code": "298040", "price": "310,000", "change": "8,000 (+2.65%)", "trend": "up", "volume": "412,500", "top_surged": false},
          {"name": "대한전선", "code": "001440", "price": "15,800", "change": "200 (+1.28%)", "trend": "up", "volume": "985,400", "top_surged": false}
        ]
      },
      "KOSDAQ": {
        "반도체": [
          {"name": "리노공업", "code": "058470", "price": "260,000", "change": "5,000 (+1.96%)", "trend": "up", "volume": "120,450", "top_surged": false},
          {"name": "HPSP", "code": "403870", "price": "52,400", "change": "800 (-1.50%)", "trend": "down", "volume": "485,120", "top_surged": false},
          {"name": "이오테크닉스", "code": "039030", "price": "214,000", "change": "8,500 (+4.14%)", "trend": "up", "volume": "210,450", "top_surged": true},
          {"name": "솔브레인", "code": "357780", "price": "285,000", "change": "1,000 (-0.35%)", "trend": "down", "volume": "42,100", "top_surged": false},
          {"name": "동진쎄미켐", "code": "005290", "price": "41,200", "change": "200 (+0.49%)", "trend": "up", "volume": "310,420", "top_surged": false}
        ],
        "바이오": [
          {"name": "알테오젠", "code": "196170", "price": "270,000", "change": "12,000 (+4.65%)", "trend": "up", "volume": "542,100", "top_surged": true},
          {"name": "HLB", "code": "028300", "price": "98,400", "change": "1,200 (-1.21%)", "trend": "down", "volume": "895,420", "top_surged": false},
          {"name": "삼천당제약", "code": "000250", "price": "142,000", "change": "4,000 (+2.90%)", "trend": "up", "volume": "210,450", "top_surged": false},
          {"name": "휴젤", "code": "145020", "price": "210,000", "change": "3,000 (-1.41%)", "trend": "down", "volume": "25,120", "top_surged": false},
          {"name": "에스티팜", "code": "237690", "price": "89,500", "change": "500 (+0.56%)", "trend": "up", "volume": "104,200", "top_surged": false}
        ],
        "로봇": [
          {"name": "레인보우로보틱스", "code": "277810", "price": "165,000", "change": "2,000 (-1.20%)", "trend": "down", "volume": "185,420", "top_surged": false},
          {"name": "뉴로메카", "code": "348340", "price": "34,200", "change": "800 (+2.39%)", "trend": "up", "volume": "98,120", "top_surged": false},
          {"name": "에스피지", "code": "058610", "price": "31,400", "change": "200 (-0.63%)", "trend": "down", "volume": "112,400", "top_surged": false},
          {"name": "로보스타", "code": "090360", "price": "15,200", "change": "850 (+5.92%)", "trend": "up", "volume": "245,100", "top_surged": true},
          {"name": "로보티즈", "code": "108490", "price": "42,100", "change": "500 (+1.20%)", "trend": "up", "volume": "52,300", "top_surged": false}
        ],
        "AI 서비스": [
          {"name": "루닛", "code": "328130", "price": "62,300", "change": "4,100 (+7.04%)", "trend": "up", "volume": "342,100", "top_surged": true},
          {"name": "셀바스AI", "code": "108860", "price": "19,800", "change": "300 (+1.54%)", "trend": "up", "volume": "210,400", "top_surged": false},
          {"name": "솔트룩스", "code": "304100", "price": "5,420", "change": "120 (+2.26%)", "trend": "up", "volume": "142,500", "top_surged": false},
          {"name": "마음AI", "code": "377480", "price": "18,500", "change": "200 (-1.07%)", "trend": "down", "volume": "85,200", "top_surged": false},
          {"name": "코난테크놀로지", "code": "402030", "price": "8,120", "change": "80 (+0.99%)", "trend": "up", "volume": "32,100", "top_surged": false}
        ],
        "MLCC": [
          {"name": "대주전자재료", "code": "078600", "price": "114,200", "change": "3,400 (+3.07%)", "trend": "up", "volume": "189,450", "top_surged": true},
          {"name": "아모텍", "code": "052710", "price": "7,820", "change": "120 (-1.51%)", "trend": "down", "volume": "25,120", "top_surged": false},
          {"name": "아바텍", "code": "149950", "price": "12,100", "change": "100 (+0.83%)", "trend": "up", "volume": "14,200", "top_surged": false},
          {"name": "상신전자", "code": "263810", "price": "3,410", "change": "20 (-0.58%)", "trend": "down", "volume": "112,400", "top_surged": false},
          {"name": "아바코", "code": "074430", "price": "11,800", "change": "300 (+2.61%)", "trend": "up", "volume": "98,120", "top_surged": false}
        ],
        "전력 수급": [
          {"name": "제룡전기", "code": "033100", "price": "42,500", "change": "2,100 (+5.20%)", "trend": "up", "volume": "342,500", "top_surged": true},
          {"name": "서전기전", "code": "189860", "price": "8,420", "change": "120 (+1.45%)", "trend": "up", "volume": "85,420", "top_surged": false},
          {"name": "대양전기공업", "code": "108380", "price": "5,230", "change": "80 (-1.51%)", "trend": "down", "volume": "42,100", "top_surged": false},
          {"name": "서호전기", "code": "065710", "price": "12,100", "change": "350 (+2.98%)", "trend": "up", "volume": "98,200", "top_surged": false},
          {"name": "세명전기", "code": "017510", "price": "6,500", "change": "50 (-0.76%)", "trend": "down", "volume": "25,100", "top_surged": false}
        ]
      }
    },
    "reports": [
      {
        "title": "글로벌 AI 반도체 밸류체인 비교 리포트",
        "summary": "엔비디아(NVIDIA)를 중심으로 한 글로벌 AI 반도체 생태계 점검. HBM(고대역폭메모리) 시장에서 SK하이닉스의 독점적 지위와 삼성전자의 맹추격, 그리고 파운드리 TSMC와의 협업 구조가 핵심. 온디바이스 AI 칩(NPU) 시장 확대에 따른 팹리스 및 디자인하우스 수혜 예상.",
        "related_stocks": ["SK하이닉스", "삼성전자", "한미반도체"]
      },
      {
        "title": "중소형 강소기업 수혜주 리포트",
        "summary": "AI 인프라 투자 확대에 따른 전력기기(HD현대일렉트릭, LS일렉트릭), 냉각시스템(데이터센터 쿨링), 유리기판 관련 소부장(소재/부품/장비) 강소기업들의 실적 점프 기대. 특히 전력 부족 현상 수혜주들이 단기 급등 후 구조적 성장 국면에 진입.",
        "related_stocks": ["HD현대일렉트릭", "LS일렉트릭", "제룡전기"]
      },
      {
        "title": "중소형 장비/소재주(밸류체인 하위 레이어)의 숨겨진 수혜주 발굴",
        "summary": "AI 반도체 고도화(HBM, 온디바이스 AI)에 따라 필수적인 첨단 패키징(Advanced Packaging), EUV 공정, 신소재(High-K 등) 관련 중소형 장비 및 소재 기업들의 실적 레버리지 효과가 부각. 대형주 대비 밸류에이션 매력이 높고 특정 공정에서 독보적 기술력을 보유한 강소기업 집중 조명.",
        "related_stocks": ["이오테크닉스", "HPSP", "솔브레인", "동진쎄미켐", "대주전자재료"]
      },
      {
        "title": "전장 및 온디바이스 AI 확산: MLCC 수요 회복 및 수혜주 점검",
        "summary": "온디바이스 AI 탑재 IT 기기 확대 및 자율주행/전장화 가속에 따라 고용량·고신뢰성 MLCC(적층세라믹콘덴서) 수요가 급증하고 있습니다. 재고 조정이 마무리되며 본격적인 턴어라운드가 기대되는 주요 MLCC 관련주를 점검합니다.",
        "related_stocks": ["삼성전기", "삼화콘덴서", "코스모신소재", "대주전자재료", "아모텍"]
      }
    ]
  };

  useEffect(() => {
    const fetchData = () => {
      fetch('http://localhost:8000/api/dashboard')
        .then(res => res.json())
        .then(data => setData(data))
        .catch(err => {
          console.warn("Backend not reachable, using fallback mock data.");
          setData(fallbackData);
        });
    };

    fetchData(); // Initial fetch
    const intervalId = setInterval(fetchData, 60000); // Poll every 60s (1m)

    return () => clearInterval(intervalId);
  }, []);

  if (!data) {
    return (
      <div className="dashboard-container" style={{justifyContent: 'center', alignItems: 'center'}}>
        <h2>백엔드에서 라이브 데이터를 불러오는 중입니다...</h2>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <header className="header">
        <h1>AI 주식 시장 애널리스트</h1>
        <p style={{color: 'var(--text-muted)', marginTop: '0.5rem'}}>코스피 / 코스닥 실시간 모니터링 및 수급 분석</p>
      </header>

      <main className="grid-layout">
        <section className="main-content" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '2rem' }}>
            <div>
              <h2 className="card-title">시장 지수</h2>
              <div style={{ display: 'flex', gap: '2rem' }}>
                <div>
                  <h3 style={{ fontSize: '1.5rem' }}>KOSPI <span className={`trend-${data.market.kospi.trend}`} style={{ fontSize: '1rem', marginLeft: '0.5rem' }}>{data.market.kospi.trend === 'up' ? '▲' : (data.market.kospi.trend === 'down' ? '▼' : '')} {data.market.kospi.change}</span></h3>
                  <p style={{ fontSize: '2.5rem', fontWeight: 'bold', color: data.market.kospi.trend === 'up' ? 'var(--accent-red)' : (data.market.kospi.trend === 'down' ? 'var(--accent-blue)' : 'var(--text-muted)') }}>{data.market.kospi.value}</p>
                </div>
                <div>
                  <h3 style={{ fontSize: '1.5rem' }}>KOSDAQ <span className={`trend-${data.market.kosdaq.trend}`} style={{ fontSize: '1rem', marginLeft: '0.5rem' }}>{data.market.kosdaq.trend === 'up' ? '▲' : (data.market.kosdaq.trend === 'down' ? '▼' : '')} {data.market.kosdaq.change}</span></h3>
                  <p style={{ fontSize: '2.5rem', fontWeight: 'bold', color: data.market.kosdaq.trend === 'up' ? 'var(--accent-red)' : (data.market.kosdaq.trend === 'down' ? 'var(--accent-blue)' : 'var(--text-muted)') }}>{data.market.kosdaq.value}</p>
                </div>
              </div>
            </div>
            
            <div style={{ minWidth: '320px', flex: 1.5 }}>
              <h2 className="card-title">투자자별 수급 동향</h2>
              <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
                <div style={{ flex: 1, minWidth: '140px' }}>
                  <h4 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.5rem', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.2rem' }}>코스피</h4>
                  <ul style={{ listStyle: 'none', lineHeight: '2', fontSize: '0.9rem' }}>
                    {(data.trends?.kospi || []).map((t, i) => (
                      <li key={i} style={{ display: 'flex', justifyContent: 'space-between', borderBottom: i !== (data.trends.kospi.length - 1) ? '1px dashed rgba(255,255,255,0.03)' : 'none', paddingBottom: '0.2rem', marginBottom: '0.2rem' }}>
                        <span>{t.group}</span> <span className={`trend-${t.trend}`} style={{fontWeight: '600'}}>{t.amount}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div style={{ flex: 1, minWidth: '140px' }}>
                  <h4 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.5rem', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.2rem' }}>코스닥</h4>
                  <ul style={{ listStyle: 'none', lineHeight: '2', fontSize: '0.9rem' }}>
                    {(data.trends?.kosdaq || []).map((t, i) => (
                      <li key={i} style={{ display: 'flex', justifyContent: 'space-between', borderBottom: i !== (data.trends.kosdaq.length - 1) ? '1px dashed rgba(255,255,255,0.03)' : 'none', paddingBottom: '0.2rem', marginBottom: '0.2rem' }}>
                        <span>{t.group}</span> <span className={`trend-${t.trend}`} style={{fontWeight: '600'}}>{t.amount}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </div>
          
          <div className="card" style={{ flex: 1 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
              <h2 className="card-title" style={{ marginBottom: 0 }}>카테고리별 주요 종목 실시간 등락 및 거래량</h2>
              <div className="search-container" style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', position: 'relative' }} ref={suggestionRef}>
                <div style={{ position: 'relative' }}>
                  <input 
                    type="text" 
                    placeholder="종목명 또는 코드..." 
                    value={searchQuery}
                    onChange={(e) => {
                      setSearchQuery(e.target.value);
                      setShowSuggestions(true);
                    }}
                    onKeyDown={(e) => { if (e.key === 'Enter') handleSearch(); }}
                    style={{
                      padding: '0.4rem 0.8rem',
                      borderRadius: '6px',
                      border: '1px solid var(--border-color)',
                      background: 'rgba(255, 255, 255, 0.05)',
                      color: 'var(--text-main)',
                      fontSize: '0.85rem',
                      outline: 'none',
                      width: '180px',
                      transition: 'border-color 0.2s'
                    }}
                    onFocus={(e) => {
                      e.target.style.borderColor = 'var(--accent-blue)';
                      setShowSuggestions(true);
                    }}
                    onBlur={(e) => e.target.style.borderColor = 'var(--border-color)'}
                  />
                  {showSuggestions && suggestions.length > 0 && (
                    <ul style={{
                      position: 'absolute',
                      top: '100%',
                      left: 0,
                      right: 0,
                      background: '#1e293b',
                      border: '1px solid var(--border-color)',
                      borderRadius: '6px',
                      marginTop: '0.3rem',
                      maxHeight: '200px',
                      overflowY: 'auto',
                      zIndex: 100,
                      listStyle: 'none',
                      padding: '0.25rem 0',
                      boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)',
                      width: '180px'
                    }}>
                      {suggestions.map((stock) => (
                        <li 
                          key={stock.code}
                          onClick={() => handleSelectStock(stock)}
                          style={{
                            padding: '0.5rem 0.8rem',
                            cursor: 'pointer',
                            fontSize: '0.8rem',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            borderBottom: '1px solid rgba(255,255,255,0.02)',
                            transition: 'background-color 0.15s'
                          }}
                          onMouseOver={(e) => e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.08)'}
                          onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                        >
                          <span style={{ fontWeight: '500', color: 'var(--text-main)' }}>{stock.name}</span>
                          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{stock.code}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
                <button 
                  onClick={handleSearch}
                  style={{
                    padding: '0.4rem 0.6rem',
                    borderRadius: '6px',
                    border: 'none',
                    background: 'var(--accent-blue)',
                    color: '#fff',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.95rem',
                    transition: 'opacity 0.2s'
                  }}
                  onMouseOver={(e) => e.target.style.opacity = '0.9'}
                  onMouseOut={(e) => e.target.style.opacity = '1'}
                >
                  🔍
                </button>
              </div>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              {/* KOSPI */}
              <div>
                <h3 style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '0.3rem', color: 'var(--text-main)', marginBottom: '0.8rem', fontSize: '1.1rem' }}>KOSPI 주요 종목</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
                  {['반도체', '바이오', '로봇', 'AI 서비스', 'MLCC', '전력 수급'].map(category => (
                    <div key={category} style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                      <h4 style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '0.6rem', borderBottom: '1px dashed rgba(255,255,255,0.05)', paddingBottom: '0.2rem' }}>{category}</h4>
                      <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                        {(data.stock_details?.KOSPI?.[category] || []).slice(0, 5).map(s => (
                          <li key={s.code} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem', borderBottom: '1px solid rgba(255,255,255,0.02)', paddingBottom: '0.3rem' }}>
                            <div style={{ display: 'flex', flexDirection: 'column' }}>
                              <div style={{ display: 'flex', alignItems: 'center' }}>
                                <a href={`https://tossinvest.com/stocks/${s.code}`} onClick={(e) => handleStockClick(e, s)} target="_blank" rel="noopener noreferrer" style={{ textDecoration: 'none', color: 'inherit', fontWeight: '500', cursor: 'pointer' }} onMouseOver={e => e.target.style.color = 'var(--accent-blue)'} onMouseOut={e => e.target.style.color = 'inherit'}>
                                  {s.name}
                                </a>
                                {s.top_surged && (
                                  <span style={{ background: 'var(--accent-red)', color: '#fff', fontSize: '0.65rem', padding: '0.05rem 0.25rem', borderRadius: '4px', marginLeft: '0.4rem', fontWeight: 'bold' }}>🔥급등</span>
                                )}
                              </div>
                              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>거래: {s.volume}</span>
                            </div>
                            <div style={{ textAlign: 'right' }}>
                              <span style={{ fontWeight: '600', color: 'var(--text-main)' }}>{s.price}</span>
                              <span className={`trend-${s.trend}`} style={{ fontSize: '0.75rem', marginLeft: '0.4rem', fontWeight: '500', display: 'block' }}>
                                {s.trend === 'up' ? '▲' : (s.trend === 'down' ? '▼' : '')} {s.change}
                              </span>
                              {s.overtime && (
                                <span style={{ fontSize: '0.7rem', color: s.overtime.trend === 'down' ? 'var(--accent-blue)' : '#f97316', display: 'block', marginTop: '0.15rem', fontWeight: '500' }}>
                                  {s.overtime.session_type === 'AFTER_MARKET' ? '시간외' : '장전외'}: {s.overtime.price}
                                </span>
                              )}
                            </div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>

              {/* KOSDAQ */}
              <div>
                <h3 style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '0.3rem', color: 'var(--text-main)', marginBottom: '0.8rem', fontSize: '1.1rem' }}>KOSDAQ 주요 종목</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
                  {['반도체', '바이오', '로봇', 'AI 서비스', 'MLCC', '전력 수급'].map(category => (
                    <div key={category} style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                      <h4 style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '0.6rem', borderBottom: '1px dashed rgba(255,255,255,0.05)', paddingBottom: '0.2rem' }}>{category}</h4>
                      <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                        {(data.stock_details?.KOSDAQ?.[category] || []).slice(0, 5).map(s => (
                          <li key={s.code} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem', borderBottom: '1px solid rgba(255,255,255,0.02)', paddingBottom: '0.3rem' }}>
                            <div style={{ display: 'flex', flexDirection: 'column' }}>
                              <div style={{ display: 'flex', alignItems: 'center' }}>
                                <a href={`https://tossinvest.com/stocks/${s.code}`} onClick={(e) => handleStockClick(e, s)} target="_blank" rel="noopener noreferrer" style={{ textDecoration: 'none', color: 'inherit', fontWeight: '500', cursor: 'pointer' }} onMouseOver={e => e.target.style.color = 'var(--accent-blue)'} onMouseOut={e => e.target.style.color = 'inherit'}>
                                  {s.name}
                                </a>
                                {s.top_surged && (
                                  <span style={{ background: 'var(--accent-red)', color: '#fff', fontSize: '0.65rem', padding: '0.05rem 0.25rem', borderRadius: '4px', marginLeft: '0.4rem', fontWeight: 'bold' }}>🔥급등</span>
                                )}
                              </div>
                              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>거래: {s.volume}</span>
                            </div>
                            <div style={{ textAlign: 'right' }}>
                              <span style={{ fontWeight: '600', color: 'var(--text-main)' }}>{s.price}</span>
                              <span className={`trend-${s.trend}`} style={{ fontSize: '0.75rem', marginLeft: '0.4rem', fontWeight: '500', display: 'block' }}>
                                {s.trend === 'up' ? '▲' : (s.trend === 'down' ? '▼' : '')} {s.change}
                              </span>
                              {s.overtime && (
                                <span style={{ fontSize: '0.7rem', color: s.overtime.trend === 'down' ? 'var(--accent-blue)' : '#f97316', display: 'block', marginTop: '0.15rem', fontWeight: '500' }}>
                                  {s.overtime.session_type === 'AFTER_MARKET' ? '시간외' : '장전외'}: {s.overtime.price}
                                </span>
                              )}
                            </div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>


        </section>

        <aside className="sidebar" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div className="card">
            <h2 className="card-title" style={{ marginBottom: '1.2rem' }}>📊 AI 핵심 리포트 (비교 요약)</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
              {(data.reports || []).map((report, idx) => (
                <div key={idx} style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '1.2rem', borderRadius: '8px', border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
                  <h3 style={{ color: 'var(--accent-blue)', fontSize: '1.05rem', borderBottom: '1px dashed rgba(255,255,255,0.1)', paddingBottom: '0.5rem' }}>
                    {report.title}
                  </h3>
                  <p style={{ color: 'var(--text-main)', fontSize: '0.9rem', lineHeight: '1.6' }}>
                    {report.summary}
                  </p>
                  {report.related_stocks && report.related_stocks.length > 0 && (
                    <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                      {report.related_stocks.map((stock, i) => (
                        <span key={i} style={{ background: 'rgba(59, 130, 246, 0.2)', color: 'var(--accent-blue)', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.8rem', fontWeight: '500' }}>
                          # {stock}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <h2 className="card-title">최신 실시간 뉴스</h2>
            <ul style={{ listStyle: 'none', gap: '1rem', display: 'flex', flexDirection: 'column' }}>
              {(data.news || []).map((n, i) => (
                <li key={i} style={{ paddingBottom: '0.8rem', borderBottom: i !== data.news.length - 1 ? '1px solid var(--border-color)' : 'none' }}>
                  <a href={n.link} target="_blank" rel="noopener noreferrer" style={{ textDecoration: 'none', color: 'inherit' }}>
                    <h4 style={{ fontSize: '0.95rem', marginBottom: '0.3rem', transition: 'color 0.2s ease' }} onMouseOver={(e) => e.target.style.color = 'var(--accent-blue)'} onMouseOut={(e) => e.target.style.color = 'inherit'}>{n.title}</h4>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{n.summary}</p>
                  </a>
                </li>
              ))}
            </ul>
          </div>

          <div className="card">
            <h2 className="card-title">오늘 가장 많이 본 뉴스 (인기)</h2>
            <ul style={{ listStyle: 'none', gap: '1rem', display: 'flex', flexDirection: 'column' }}>
              {(data.popular_news || []).map((n, i) => (
                <li key={i} style={{ paddingBottom: '0.8rem', borderBottom: i !== (data.popular_news || []).length - 1 ? '1px solid var(--border-color)' : 'none' }}>
                  <a href={n.link} target="_blank" rel="noopener noreferrer" style={{ textDecoration: 'none', color: 'inherit' }}>
                    <h4 style={{ fontSize: '0.95rem', marginBottom: '0.3rem', transition: 'color 0.2s ease' }} onMouseOver={(e) => e.target.style.color = 'var(--accent-red)'} onMouseOut={(e) => e.target.style.color = 'inherit'}>{n.title}</h4>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{n.summary}</p>
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </aside>
      </main>

      {selectedStock && (() => {
        const indicators = getTechnicalIndicators(selectedStock, chartTimeframe);
        return (
          <div className="modal-overlay" onClick={() => setSelectedStock(null)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <div>
                  <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    {selectedStock.name}
                    <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)', fontWeight: 'normal' }}>
                      ({selectedStock.code})
                    </span>
                  </h2>
                </div>
                <button className="modal-close-btn" onClick={() => setSelectedStock(null)}>&times;</button>
              </div>

              <div className="modal-grid">
                {/* Left Panel: TradingView Interactive Chart */}
                <div className="modal-left-panel">
                  <div className="timeframe-selector">
                    {[
                      { label: '1일', value: 'day' },
                      { label: '1주', value: 'week' },
                      { label: '3달', value: 'month3' },
                      { label: '1년', value: 'year' },
                      { label: '3년', value: 'year3' },
                      { label: '5년', value: 'year5' }
                    ].map((tf) => (
                      <button
                        key={tf.value}
                        className={`timeframe-btn ${chartTimeframe === tf.value ? 'active' : ''}`}
                        onClick={() => setChartTimeframe(tf.value)}
                      >
                        {tf.label}
                      </button>
                    ))}
                  </div>

                  <div className="chart-wrapper">
                    <TradingViewWidget symbol={selectedStock.code} timeframe={chartTimeframe} />
                  </div>

                  <div className="stock-news-section" style={{ marginTop: '0.5rem' }}>
                    <h3 style={{ fontSize: '0.95rem', fontWeight: '600', color: 'var(--text-muted)', marginBottom: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      📰 종목 관련 주요 뉴스 (인기/최신)
                    </h3>
                    {loadingNews ? (
                      <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>뉴스를 불러오는 중...</p>
                    ) : stockNews.length > 0 ? (
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '0.8rem' }}>
                        {stockNews.map((news, idx) => (
                          <a
                            key={idx}
                            href={news.link}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{
                              textDecoration: 'none',
                              color: 'inherit',
                              background: 'rgba(255, 255, 255, 0.02)',
                              border: '1px solid var(--border-color)',
                              borderRadius: '8px',
                              padding: '0.8rem',
                              display: 'flex',
                              flexDirection: 'column',
                              gap: '0.4rem',
                              transition: 'all 0.2s ease',
                              cursor: 'pointer'
                            }}
                            onMouseOver={(e) => {
                              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
                              e.currentTarget.style.borderColor = 'var(--accent-blue)';
                            }}
                            onMouseOut={(e) => {
                              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.02)';
                              e.currentTarget.style.borderColor = 'var(--border-color)';
                            }}
                          >
                            <h4
                              style={{
                                fontSize: '0.85rem',
                                fontWeight: '500',
                                color: 'var(--text-main)',
                                display: '-webkit-box',
                                WebkitLineClamp: 2,
                                WebkitBoxOrient: 'vertical',
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                height: '2.4rem',
                                lineHeight: '1.2',
                                transition: 'color 0.2s ease'
                              }}
                            >
                              {news.title}
                            </h4>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 'auto' }}>
                              <span style={{ fontWeight: news.is_popular ? 'bold' : 'normal', color: news.is_popular ? 'var(--accent-red)' : 'var(--text-muted)' }}>
                                {news.office}
                              </span>
                              <span>{news.date}</span>
                            </div>
                          </a>
                        ))}
                      </div>
                    ) : (
                      <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>등록된 관련 뉴스가 없습니다.</p>
                    )}
                  </div>
                </div>

                {/* Right Panel: Technical Details & AI Analysis */}
                <div className="modal-right-panel">
                  <div className="stock-info-card">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                      <span className="info-price">{selectedStock.price}원</span>
                      <span className={`trend-${selectedStock.trend}`} style={{ fontWeight: '600', fontSize: '1.1rem' }}>
                        {selectedStock.trend === 'up' ? '▲' : (selectedStock.trend === 'down' ? '▼' : '')} {selectedStock.change}
                      </span>
                    </div>
                    {selectedStock.overtime && (
                      <div style={{ 
                        display: 'flex', 
                        justifyContent: 'space-between', 
                        background: selectedStock.overtime.trend === 'down' ? 'rgba(59, 130, 246, 0.08)' : 'rgba(249, 115, 22, 0.08)', 
                        padding: '0.5rem 0.8rem', 
                        borderRadius: '6px', 
                        border: selectedStock.overtime.trend === 'down' ? '1px solid rgba(59, 130, 246, 0.2)' : '1px solid rgba(249, 115, 22, 0.15)', 
                        marginTop: '0.6rem', 
                        alignItems: 'center' 
                      }}>
                        <span style={{ fontSize: '0.75rem', color: selectedStock.overtime.trend === 'down' ? 'var(--accent-blue)' : '#f97316', fontWeight: '700' }}>
                          {selectedStock.overtime.session_type === 'AFTER_MARKET' ? '🕒 시간외 단일가' : '🌅 장전 시간외'} {selectedStock.overtime.status === 'OPEN' ? '(진행중)' : '(종료)'}
                        </span>
                        <span className={`trend-${selectedStock.overtime.trend}`} style={{ fontSize: '0.8rem', fontWeight: 'bold' }}>
                          {selectedStock.overtime.price}원 ({selectedStock.overtime.trend === 'up' ? '▲' : (selectedStock.overtime.trend === 'down' ? '▼' : '')} {selectedStock.overtime.change})
                        </span>
                      </div>
                    )}
                    <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '0.5rem' }}>
                      <span>거래량: {selectedStock.volume}주</span>
                      <span>종목코드: {selectedStock.code}</span>
                    </div>
                  </div>

                  {/* Investor Flow Card (NEW) */}
                  {selectedStock.investor_trend && (
                    <div className="analysis-card" style={{ padding: '0.8rem 1rem', display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                      <h3 style={{ fontSize: '0.9rem', fontWeight: '600', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>당일 투자자별 매매동향</h3>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.4rem' }}>
                        <span style={{ flex: 1, fontWeight: '500' }}>투자자</span>
                        <span style={{ width: '90px', textAlign: 'right', fontWeight: '500' }}>순매매량</span>
                        <span style={{ width: '95px', textAlign: 'right', fontWeight: '500' }}>순매매금액(추정)</span>
                      </div>
                      {[
                        { label: '개인', data: selectedStock.investor_trend.individual },
                        { label: '외국인', data: selectedStock.investor_trend.foreigner },
                        { label: '기관', data: selectedStock.investor_trend.organ }
                      ].map((item, idx) => (
                        <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8rem', paddingBottom: idx !== 2 ? '0.3rem' : '0', borderBottom: idx !== 2 ? '1px dashed rgba(255,255,255,0.02)' : 'none' }}>
                          <span style={{ flex: 1, fontWeight: '500', color: 'var(--text-main)' }}>{item.label}</span>
                          <span className={`trend-${item.data.trend}`} style={{ width: '90px', textAlign: 'right', fontWeight: '600' }}>{item.data.volume}</span>
                          <span className={`trend-${item.data.trend}`} style={{ width: '95px', textAlign: 'right', fontWeight: '600' }}>{item.data.amount}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="analysis-card">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.8rem' }}>
                      <h3 style={{ fontSize: '0.95rem', fontWeight: '600', color: 'var(--text-muted)' }}>종합 분석 의견</h3>
                      <span className={`consensus-badge ${indicators.consensusClass}`}>
                        {indicators.consensus}
                      </span>
                    </div>

                    <div className="score-container" style={{ marginBottom: '1rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.3rem', color: 'var(--text-muted)' }}>
                        <span>기술 분석 점수</span>
                        <span style={{ fontWeight: 'bold', color: 'var(--text-main)' }}>{indicators.score} / 100점</span>
                      </div>
                      <div className="score-bar-bg">
                        <div
                          className="score-bar-fill"
                          style={{
                            width: `${indicators.score}%`,
                            background: indicators.score >= 60 ? 'linear-gradient(90deg, var(--accent-red), #eab308)' : 'linear-gradient(90deg, var(--accent-blue), #38bdf8)'
                          }}
                        />
                      </div>
                    </div>

                    <table className="indicators-table">
                      <thead>
                        <tr>
                          <th>보조 지표</th>
                          <th>현황 / 시그널</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>
                            <span 
                              className="tooltip-indicator"
                              onMouseEnter={() => setHoveredIndicator('RSI')}
                              onMouseLeave={() => setHoveredIndicator(null)}
                            >
                              RSI (14)
                            </span>
                          </td>
                          <td>
                            <span style={{ fontWeight: '600', color: indicators.rsi >= 70 ? 'var(--accent-red)' : indicators.rsi <= 30 ? 'var(--accent-blue)' : 'var(--text-main)' }}>
                              {indicators.rsi}
                            </span>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginLeft: '0.3rem' }}>
                              ({indicators.rsi >= 70 ? '과매수' : indicators.rsi <= 30 ? '과매도' : '적정'})
                            </span>
                          </td>
                        </tr>
                        <tr>
                          <td>
                            <span 
                              className="tooltip-indicator"
                              onMouseEnter={() => setHoveredIndicator('MACD')}
                              onMouseLeave={() => setHoveredIndicator(null)}
                            >
                              MACD
                            </span>
                          </td>
                          <td>{indicators.macd}</td>
                        </tr>
                        <tr>
                          <td>
                            <span 
                              className="tooltip-indicator"
                              onMouseEnter={() => setHoveredIndicator('BBAND')}
                              onMouseLeave={() => setHoveredIndicator(null)}
                            >
                              볼린저 밴드
                            </span>
                          </td>
                          <td>{indicators.bband}</td>
                        </tr>
                        <tr>
                          <td>
                            <span 
                              className="tooltip-indicator"
                              onMouseEnter={() => setHoveredIndicator('MA')}
                              onMouseLeave={() => setHoveredIndicator(null)}
                            >
                              이동평균선
                            </span>
                          </td>
                          <td>{indicators.ma}</td>
                        </tr>
                        <tr>
                          <td>
                            <span 
                              className="tooltip-indicator"
                              onMouseEnter={() => setHoveredIndicator('STOCH')}
                              onMouseLeave={() => setHoveredIndicator(null)}
                            >
                              스토캐스틱
                            </span>
                          </td>
                          <td>{indicators.stoch}</td>
                        </tr>
                        <tr>
                          <td>
                            <span 
                              className="tooltip-indicator"
                              onMouseEnter={() => setHoveredIndicator('OBV')}
                              onMouseLeave={() => setHoveredIndicator(null)}
                            >
                              OBV
                            </span>
                          </td>
                          <td>{indicators.obv}</td>
                        </tr>
                      </tbody>
                    </table>

                    {/* Dynamic Indicator Explanation Box */}
                    <div style={{
                      marginTop: '0.8rem',
                      padding: '0.6rem 0.8rem',
                      borderRadius: '6px',
                      background: 'rgba(255, 255, 255, 0.02)',
                      border: '1px solid var(--border-color)',
                      fontSize: '0.75rem',
                      color: hoveredIndicator ? 'var(--text-main)' : 'var(--text-muted)',
                      lineHeight: '1.4',
                      minHeight: '4.5rem',
                      display: 'flex',
                      alignItems: 'center',
                      transition: 'all 0.15s ease-in-out'
                    }}>
                      <p style={{ margin: 0 }}>
                        {hoveredIndicator ? (
                          <>
                            <strong style={{ color: 'var(--accent-blue)' }}>💡 {
                              hoveredIndicator === 'RSI' ? "RSI (14)" :
                              hoveredIndicator === 'MACD' ? "MACD" :
                              hoveredIndicator === 'BBAND' ? "볼린저 밴드" :
                              hoveredIndicator === 'MA' ? "이동평균선" :
                              hoveredIndicator === 'STOCH' ? "스토캐스틱" :
                              "OBV"
                            }</strong>: {
                              hoveredIndicator === 'RSI' ? "상대강도지수. 주가의 상승/하락 강도를 나타내며 70 이상은 과매수, 30 이하는 과매도 상태로 판별합니다." :
                              hoveredIndicator === 'MACD' ? "이동평균 수렴확산 지수. 단기/장기 이동평균선 간의 괴리를 분석하여 추세의 골든/데드크로스를 포착합니다." :
                              hoveredIndicator === 'BBAND' ? "볼린저 밴드. 표준편차를 활용하여 주가가 상한선에 오면 저항/과열, 하한선에 오면 지지/침체로 해석합니다." :
                              hoveredIndicator === 'MA' ? "이동평균선. 일정 기간의 주가 평균선 배열 상태(정배열/역배열)를 확인하여 장기적인 지지와 저항 흐름을 판별합니다." :
                              hoveredIndicator === 'STOCH' ? "Stochastic. 최근 가격 범위 내에서 현재 주가의 상대적인 강도를 %K와 %D선으로 보여주며, 단기 과열(80 이상)/침체(20 이하)를 식별합니다." :
                              "On Balance Volume. 거래량은 주가에 선행한다는 원리로, 주가 상승일 거래량 합계에서 하락일 거래량 합계를 차감하여 자금의 매집 여부를 포착합니다."
                            }
                          </>
                        ) : (
                          "💡 보조 지표 이름에 마우스를 올리면 상세 설명이 여기에 표시됩니다."
                        )}
                      </p>
                    </div>
                  </div>

                  <div className="ai-opinion-card">
                    <h4 style={{ color: 'var(--accent-blue)', marginBottom: '0.4rem', display: 'flex', alignItems: 'center', gap: '0.3rem', fontWeight: '600', fontSize: '0.85rem' }}>
                      💡 기술적 차트 분석 의견
                    </h4>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', lineHeight: '1.5' }}>
                      {getChartAnalysis(selectedStock, chartTimeframe)}
                    </p>
                  </div>

                  <div className="modal-footer" style={{ marginTop: 'auto', paddingTop: '1rem' }}>
                    <a
                      href={`https://tossinvest.com/stocks/${selectedStock.code}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="toss-link-btn"
                      style={{ width: '100%', textAlign: 'center' }}
                    >
                      토스증권 PC에서 보기 &rarr;
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
}

export default App;
