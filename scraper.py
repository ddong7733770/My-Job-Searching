import json
import os
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
keyword = "영업기획"
all_jobs = []

# 크롬 브라우저 세팅 (사람처럼 위장)
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

driver = webdriver.Chrome(options=chrome_options)

def safe_append(platform, title, company, address):
    if title and company:
        all_jobs.append({
            "platform": platform,
            "title": title.strip(),
            "company": company.strip(),
            "address": address.strip() if address else "주소 미상"
        })

# [1] 사람인 수집
try:
    driver.get(f"https://www.saramin.co.kr/zf_user/search/recruit?searchword={keyword}")
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    for card in soup.select('.item_recruit')[:5]:
        title = card.select_one('.job_tit a').text if card.select_one('.job_tit a') else ""
        company = card.select_one('.corp_name a').text if card.select_one('.corp_name a') else ""
        addr = card.select('.job_condition span')[0].text if card.select('.job_condition span') else ""
        safe_append("사람인", title, company, addr)
except Exception as e:
    print(f"사람인 에러: {e}")

# [2] 잡코리아 수집
try:
    driver.get(f"https://www.jobkorea.co.kr/Search/?stext={keyword}")
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    for card in soup.select('.list-default .list-post')[:5]:
        title = card.select_one('.title').text if card.select_one('.title') else ""
        company = card.select_one('.name').text if card.select_one('.name') else ""
        addr = card.select_one('.loc').text if card.select_one('.loc') else ""
        safe_append("잡코리아", title, company, addr)
except Exception as e:
    print(f"잡코리아 에러: {e}")

# [3] 원티드 수집 (스크롤이 필요한 자바스크립트 페이지)
try:
    driver.get(f"https://www.wanted.co.kr/search?query={keyword}")
    time.sleep(3)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    for card in soup.select('div[class*="JobCard_container"]')[:5]:
        title = card.select_one('strong[class*="JobCard_title"]').text if card.select_one('strong[class*="JobCard_title"]') else ""
        company = card.select_one('span[class*="JobCard_companyName"]').text if card.select_one('span[class*="JobCard_companyName"]') else ""
        # 원티드는 검색창에 상세 주소가 노출되지 않아 기본 지역으로 세팅
        safe_append("원티드", title, company, "서울 강남구")
except Exception as e:
    print(f"원티드 에러: {e}")

# [4] 리멤버 수집 (로그인 장벽이 높아 공개 채용관 접근)
try:
    driver.get(f"https://career.rememberapp.co.kr/job/search?keyword={keyword}")
    time.sleep(3)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    for card in soup.select('.job-posting-item')[:5]:
        title = card.select_one('.title').text if card.select_one('.title') else ""
        company = card.select_one('.company-name').text if card.select_one('.company-name') else ""
        safe_append("리멤버", title, company, "서울 강남구") # 임시 주소
except Exception as e:
    print(f"리멤버 에러: {e}")

driver.quit()

# 봇 차단으로 데이터가 0건일 경우 테스트 데이터 강제 삽입 (화면 백지 방지)
if len(all_jobs) == 0:
    all_jobs = [
        {"platform": "사람인", "title": "B2B 영업 데이터 분석 담당", "company": "(테스트)아이코닉스", "address": "경기도 성남시 분당구 판교로 242"},
        {"platform": "잡코리아", "title": "영업기획 및 신제품 마케팅", "company": "(테스트)넥슨", "address": "경기도 성남시 분당구 판교로 256"},
        {"platform": "원티드", "title": "B2B 굿즈 기획 및 제휴", "company": "(테스트)카카오", "address": "제주특별자치도 제주시 첨단로 242"},
        {"platform": "리멤버", "title": "영업 전략 기획 (5년차 이상)", "company": "(테스트)네이버", "address": "경기도 성남시 분당구 정자일로 95"}
    ]

# 구글 API로 주소 -> 좌표 변환
def get_coords(address):
    if not api_key or address == "주소 미상":
        return None, None
    search_address = f"{address} 대한민국"
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={search_address}&key={api_key}"
    try:
        res = requests.get(url).json()
        if res.get('status') == 'OK':
            loc = res['results'][0]['geometry']['location']
            return loc['lat'], loc['lng']
    except:
        pass
    return None, None

for job in all_jobs:
    lat, lng = get_coords(job["address"])
    job["lat"] = lat
    job["lng"] = lng

# JSON 파일로 저장
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(all_jobs, f, ensure_ascii=False, indent=4)
