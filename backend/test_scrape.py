import requests
from bs4 import BeautifulSoup

url = 'https://finance.naver.com/news/'
HEADERS = {'User-Agent': 'Mozilla/5.0'}
response = requests.get(url, headers=HEADERS)
soup = BeautifulSoup(response.text, 'html.parser')

print("main_news:", len(soup.select('.main_news ul li a')))
print("newsList:", len(soup.select('.newsList li a')))
print("right_list_1:", len(soup.select('.right_list_1 li a')))
print("right_list_2:", len(soup.select('.right_list_2 li a')))
print("rank_news:", len(soup.select('.ranknews_box li a')))
print("news_rank:", len(soup.select('#right_rank_list li a')))

# Print all classes containing 'list' or 'rank' that have 'li a'
for div in soup.select('div[class*="list"], div[class*="rank"]'):
    links = div.select('li a')
    if links:
        print(f"Class {div.get('class')}: {len(links)} links")
