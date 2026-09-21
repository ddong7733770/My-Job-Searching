import json
import os
import time
import requests
from bs4 import BeautifulSoup

api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
keyword = "영업기획" 
all_jobs = []

# 일반 사용자(사람)처럼 보이게 하는 헤더
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

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

# [1] 사람인 (리스트 수집 후 상세페이지 접속하여 정확한 주소 파싱)
try:
    url = f"https://www.saramin.co.kr/zf_user/search/recruit?searchword={keyword}&recruitPageCount=30"
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    for card in soup.select('.item_recruit')[:30]:
        title_elem = card.select_one('.job_tit a')
        title = title_elem.text if title_elem else ""
        company = card.select_one('.corp_name a').text if card.select_one('.corp_name a') else ""
        
        conditions = card.select('.job_condition span')
        exp = conditions[1].text if len(conditions) > 1 else "경력 무관"
        address = conditions[0].text if len(conditions) > 0 else "서울"
        link = "https://www.saramin.co.kr" + title_elem['href'] if title_elem else ""
        
        # 상세페이지 접속하여 정확한 주소 확보
        if link:
            try:
                time.sleep(0.5)
                d_res = requests.get(link, headers=headers)
                d_soup = BeautifulSoup(d_res.text, 'html.parser')
                # 사람인 상세 근무지 추출
                info_dl = d_soup.select('.info_period dd')
                if len(info_dl) >= 2: # 보통 두번째 dd가 근무지
                    address = info_dl[1].text.strip()
            except: pass
            
        safe_append("사람인", title, company, address, link, exp)
except Exception as e: print(f"사람인 에러: {e}")

# [2] 잡코리아
try:
    url = f"https://www.jobkorea.co.kr/Search/?stext={keyword}&tabType=recruit&Page_No=1"
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    for card in soup.select('.list-default .list-post')[:30]:
        title_elem = card.select_one('.title')
        title = title_elem.text if title_elem else ""
        company = card.select_one('.name').text if card.select_one('.name') else ""
        exp_elem = card.select_one('.exp')
        exp = exp_elem.text if exp_elem else "경력 무관"
        link = "https://www.jobkorea.co.kr" + title_elem['href'] if title_elem else ""
        address = "서울"

        # 상세페이지 접속하여 정확한 주소 확보
        if link:
            try:
                time.sleep(0.5)
                d_res = requests.get(link, headers=headers)
                d_soup = BeautifulSoup(d_res.text, 'html.parser')
                addr_elem = d_soup.select_one('.address')
                if addr_elem: address = addr_elem.text.strip()
            except: pass

        safe_append("잡코리아", title, company, address, link, exp)
except Exception as e: print(f"잡코리아 에러: {e}")

# [3] 원티드 (원티드는 봇 차단이 심해 공개 API로 다이렉트 통신하여 상세 주소 확보)
try:
    url = f"https://www.wanted.co.kr/api/v4/jobs?country=kr&locations=all&years=-1&query={keyword}&limit=30"
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        jobs_data = res.json().get('data', [])
        for job in jobs_data:
            title = job.get('position', '')
            company = job.get('company', {}).get('name', '')
            job_id = job.get('id', '')
            link = f"https://www.wanted.co.kr/wd/{job_id}"
            address = "서울"
            
            # 원티드 상세 주소 API 호출
            if job_id:
                try:
                    time.sleep(0.3)
                    d_url = f"https://www.wanted.co.kr/api/v4/jobs/{job_id}"
                    d_res = requests.get(d_url, headers=headers).json()
                    addr = d_res.get('job', {}).get('address', {}).get('full_location', '')
                    if addr: address = addr
                except: pass
                
            safe_append("원티드", title, company, address, link, "경력")
except Exception as e: print(f"원티드 에러: {e}")

# 구글 지오코딩 (수집된 상세 주소를 지도 좌표로 변환)
def get_coords(address):
    if not api_key or len(address) < 3:
        return None, None
    search_address = f"{address.split(',')[0]} 대한민국" 
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={search_address}&key={api_key}"
    try:
        res = requests.get(url).json()
        if res.get('status') == 'OK':
            loc = res['results'][0]['geometry']['location']
            return loc['lat'], loc['lng']
    except: pass
    return None, None

for job in all_jobs:
    lat, lng = get_coords(job["address"])
    job["lat"] = lat
    job["lng"] = lng

# 최종 저장
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(all_jobs, f, ensure_ascii=False, indent=4)
