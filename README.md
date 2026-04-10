# Title : myInvesting

### SubTitle : 주식 관련 유의미한 뉴스들을 수집해서 보여주는 개인 투자 보조 사이트.

## 주요 기능 (Features)

1. 종목 검색 : 메인페이지에서 주식티커를 통해 검색해 현재가, 기업명 등의 정보를 볼 수 있다.
2. 각 종목 별 페이지에서 관심종목에 추가해 포트폴리오를 구성할 수 있다.
3. 메인페이지에서 관심종목들의 뉴스와 현재가 등을 모니터링 할 수 있다.
4. 수집된 뉴스들의 클릭해 뉴스를 읽고 투자 인사이트를 기를 수 있다.

![use case diagram](images/use_case.png)

## 시작하기

git clone https://github.com/TakSakong/myInvesting.git
cd myInvesting

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

### 요구사항

Python 3.9+ (Mac M1 환경 최적화)
pip (Python 패키지 관리자)

requirements.txt 참고

### 설치방법

## 사용법

로컬 서버 실행
python app.py

웹 브라우저 접속
브라우저 주소창에 http://localhost:5001을 입력하여 접속합니다.

종목 관리
검색창에 AAPL, TSLA, NVDA 등의 티커를 입력합니다.
검색 결과에서 ⭐ 관심종목 등록 버튼을 눌러 내 리스트에 추가합니다.

## 기술스택

Backend
Framework: Flask (Lightweight Web Framework)
Data Source: yfinance (Yahoo Finance API Wrapper)
Language: Python 3.10

Frontened
Templating: Jinja2 (Flask default engine)
Markup/Styling: HTML5, CSS3

DevOps & Tools
Version Control: Git, GitHub
Environment: venv (Virtual Environment)
