import json
import os
import requests
from bs4 import BeautifulSoup

api_key = os.environ.get("GOOGLE_MAPS_API_KEY")

# 1. 실제 사람인(Saramin) 채용 정보 수집 함수
def get_saramin_jobs(keyword):
    jobs = []
    # 사람인 검색 URL
    url = f"https://www.saramin.co.kr/zf_user/search/recruit?searchword={keyword}"
    
    # 크롤링 차단을 막기 위해 일반 크롬 브라우저처럼 위장합니다.
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 채용 공고 리스트 추출 (상위 15개)
        job_cards = soup.select('.item_recruit')[:15]
        
        for card in job_cards:
            title_elem = card.select_one('.job_tit a')
            company_elem = card.select_one('.corp_name a')
            condition_elems = card.select('.job_condition span')
            
            if title_elem and company_elem:
                title = title_elem.text.strip()
                company = company_elem.text.strip()
                # 조건 목록 중 첫 번째가 보통 '지역(예: 서울 강남구)' 입니다.
                address = condition_elems[0].text.strip() if condition_elems else "주소 미상"
                
                jobs.append({
                    "platform": "사람인",
                    "title": title,
                    "company": company,
                    "address": address
                })
    except Exception as e:
        print(f"크롤링 오류: {e}")
        
    return jobs

# 2. '영업기획' 키워드로 채용 정보 수집
real_jobs = get_saramin_jobs("영업기획")

# 3. 구글 API로 추출한 지역 이름을 좌표(위도/경도)로 변환
def get_coords(address):
    if not api_key or address == "주소 미상":
        return None, None
        
    # 정확도를 높이기 위해 주소 뒤에 '대한민국'을 붙여 검색합니다.
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

for job in real_jobs:
    lat, lng = get_coords(job["address"])
    job["lat"] = lat
    job["lng"] = lng

# 4. 수집한 진짜 데이터를 data.json 파일로 저장
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(real_jobs, f, ensure_ascii=False, indent=4)
