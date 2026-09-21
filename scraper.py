import json
import os
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
keyword = "영업기획" 
all_jobs = []

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
driver = webdriver.Chrome(options=chrome_options)

def safe_append(platform, title, company, address, link, experience):
    if title and company:
        all_jobs.append({
            "platform": platform,
            "title": title.strip(),
            "company": company.strip(),
            "address": address.strip() if address else "주소 미상",
            "link": link if link else "#",
            "experience": experience.strip() if experience else "경력 무관"
        })

# [1] 사람인 (수집량 최대 40~50개로 증가, 경력 추출 추가)
try:
    driver.get(f"https://www.saramin.co.kr/zf_user/search/recruit?searchword={keyword}")
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    for card in soup.select('.item_recruit')[:50]:
        title_elem = card.select_one('.job_tit a')
        title = title_elem.text if title_elem else ""
        company = card.select_one('.corp_name a').text if card.select_one('.corp_name a') else ""
        
        # 사람인은 span 태그에 지역, 경력 정보가 나열됨
        conditions = card.select('.job_condition span')
        addr = conditions[0].text if len(conditions) > 0 else "주소 미상"
        exp = conditions[1].text if len(conditions) > 1 else "경력 무관"
        
        link = "https://www.saramin.co.kr" + title_elem['href'] if title_elem and 'href' in title_elem.attrs else "#"
        safe_append("사람인", title, company, addr, link, exp)
except Exception as e:
    pass

# [2] 잡코리아 (수집량 증가, 경력 추출 추가)
try:
    driver.get(f"https://www.jobkorea.co.kr/Search/?stext={keyword}")
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    for card in soup.select('.list-default .list-post')[:50]:
        title_elem = card.select_one('.title')
        title = title_elem.text if title_elem else ""
        company = card.select_one('.name').text if card.select_one('.name') else ""
        
        # 잡코리아는 option 태그 안에 경력, 학력, 지역 정보가 나열됨
        addr = card.select_one('.loc').text if card.select_one('.loc') else "주소 미상"
        exp_elem = card.select_one('.exp')
        exp = exp_elem.text if exp_elem else "경력 무관"
        
        link = "https://www.jobkorea.co.kr" + title_elem['href'] if title_elem and 'href' in title_elem.attrs else "#"
        safe_append("잡코리아", title, company, addr, link, exp)
except Exception as e:
    pass

# [3] 원티드 (무한 스크롤 다운을 통해 수집량 증가)
try:
    driver.get(f"https://www.wanted.co.kr/search?query={keyword}")
    time.sleep(2)
    # 스크롤을 내려 더 많은 데이터를 로딩
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    for card in soup.select('div[class*="JobCard_container"]')[:40]:
        title = card.select_one('strong[class*="JobCard_title"]').text if card.select_one('strong[class*="JobCard_title"]') else ""
        company = card.select_one('span[class*="JobCard_companyName"]').text if card.select_one('span[class*="JobCard_companyName"]') else ""
        
        a_tag = card.find_parent('a') or card.select_one('a')
        link = "https://www.wanted.co.kr" + a_tag['href'] if a_tag and 'href' in a_tag.attrs else "#"
        safe_append("원티드", title, company, "서울 주요지역", link, "경력") 
except Exception as e:
    pass

driver.quit()

# 비상용 테스트 데이터
if len(all_jobs) == 0:
    all_jobs = [
        {"platform": "시스템", "title": "서버 접속이 원활하지 않습니다.", "company": "오류 안내", "address": "경기도 성남시 분당구", "link": "#", "experience": "안내"}
    ]

# 구글 API 위경도 변환
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

with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(all_jobs, f, ensure_ascii=False, indent=4)
