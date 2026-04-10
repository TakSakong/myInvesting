# 1. Title : myInvesting

### SubTitle : 주식 관련 유의미한 뉴스들을 수집해서 보여주는 개인 투자 보조 사이트.

[use case diagram](images/use_case.png)

# 2. Visual Demonstration
![use case diagram](images/interest.gif)
관심종목 등록 및 홈에서 관심종목 조회

![use case diagram](images/news.gif)
뉴스 조회

![use case diagram](images/newsinterests.gif)
뉴스 관심종목 등록 및 조회

# 3. Motivation & Problem
저는 기존에 미국 주식을 주로 하는데 미국 주식에 대한 뉴스들은 한국주식과 달리 한국 뉴스에서 직접 쉽게 접할 수 없고 직접 찾아봐야 합니다.
많은 사람들이 한국인들이 미국 뉴스를 가공한 형태의 정보를 접하지만 이는 시간이 중요한 주식 특성상 뉴스가 발생한지 몇 시간 뒤에 우리가 한글로 접하게 되고 이미 정보의 가치는 떨어진 상태가 됩니다. 
그래서 저는 미국 주식에 대한 뉴스를 실시간으로 접할 수 있는 사이트를 만들고 싶었습니다.

# 4. Tech Stack & Rationale

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

# 5. Key Features

1. 종목 검색 : 메인페이지에서 주식티커를 통해 검색해 현재가, 기업명 등의 정보를 볼 수 있다.
2. 각 종목 별 페이지에서 관심종목에 추가해 포트폴리오를 구성할 수 있다.
3. 메인페이지에서 관심종목들의 뉴스와 현재가 등을 모니터링 할 수 있다.
4. 수집된 뉴스들의 클릭해 뉴스를 읽고 투자 인사이트를 기를 수 있다.

# 6. Getting Started Guide

git clone https://github.com/TakSakong/myInvesting.git
cd myInvesting

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

로컬 서버 실행
python app.py

웹 브라우저 접속
브라우저 주소창에 http://localhost:5001을 입력하여 접속합니다.

종목 관리
검색창에 AAPL, TSLA, NVDA 등의 티커를 입력합니다.
검색 결과에서 ⭐ 관심종목 등록 버튼을 눌러 내 리스트에 추가합니다.

# 7.Lessons Leanred / Challenges

260327 수업
평소 개인적으로 홈페이지를 만들때에는 vercel이나 railway를 이용해서 간단하게 배포했었는데 만약 대규모 프로젝트나 기업에서 운영하는 서비스는 쿠버네티스를 사용하는 것이 자명해 언젠가 쿠버네티스를 배워야겠다는 생각을 했습니다. 이번 수업을 통해서 쿠버네티스가 왜 필요햔지에 대해서 자세히 배웠고 개인적으로 어떻게 사용하는지에 대해서 공부해 봐야 할 필요를 느꼈습니다.

260403 수업
여러 가지 유지보수에 장애물이 되는 code smell에 대해서 배우고, AI를 활용해 리팩토링을 빠르고 쉽게 할 수 있는 방법에 대해서 배웠습니다.
기존에는 수업에서 프로젝트를 열심히 하고 나서 깃헙에서 코드가 유기되는 상태였는데 이제는 기능 구현을 마친 후에 리팩토링을 통해 더 좋은 코드로 발전시켜나가야 한다는 인식이 자리잡은 것 같습니다.

260410 수업
기존에는 API 기능 구현 자체에만 집중했는데 이제 docstrings를 통해 사용자에게 어떻게 사용하는지를 설명하고 주석을 통해 왜 이런 코드를 작성했는지에 대해 생각을 해볼 것 같습니다. 또한 이런 문서화를 이용해서 Swagger UI와 같은 API 문서를 자동으로 생성할 수 있다는 것을 알게 되었습니다. 또, Sphinx 를 이용해서 프로젝트의 API 문서를 자동으로 생성할 수 있다는 것을 알게 되었습니다. 