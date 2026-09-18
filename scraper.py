import json
import os
import requests

# 깃허브 Secret에 저장해둔 구글 API 키를 불러옵니다.
api_key = os.environ.get("GOOGLE_MAPS_API_KEY")

# 1. 수집된 채용 데이터 (현재는 크롤링 대신 임시 데이터를 넣었습니다)
jobs = [
    {
        "title": "영업 데이터 분석 담당자", 
        "company": "A기업", 
        "address": "서울특별시 강남구 테헤란로 123", 
        "platform": "원티드"
    },
    {
        "title": "B2B 굿즈 사업 기획 및 영업", 
        "company": "B기업", 
        "address": "경기도 성남시 분당구 판교역로 146", 
        "platform": "사람인"
    },
    {
        "title": "신제품 출시 및 마케팅 전략 기획", 
        "company": "C기업", 
        "address": "서울특별시 송파구 올림픽로 300", 
        "platform": "잡코리아"
    }
]

# 2. 구글 Geocoding API로 주소를 텍스트에서 좌표(위도/경도)로 변환하는 함수
def get_coords(address):
    # API 키가 없으면 실행하지 않음
    if not api_key:
        return None, None
        
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}"
    res = requests.get(url).json()
    
    if res.get('status') == 'OK':
        loc = res['results'][0]['geometry']['location']
        return loc['lat'], loc['lng']
    return None, None

# 3. 위에서 만든 임시 데이터의 주소를 하나씩 꺼내서 위도/경도를 찾아 추가합니다.
for job in jobs:
    lat, lng = get_coords(job["address"])
    job["lat"] = lat
    job["lng"] = lng

# 4. 나중에 웹 화면(index.html)에서 읽을 수 있도록 data.json 파일로 저장합니다.
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(jobs, f, ensure_ascii=False, indent=4)
