# DriveTalk - 지능형 차량 어시스턴트

DriveTalk은 음성 인식, 자연어 처리 및 음악 재생 기능을 통합한 지능형 차량 어시스턴트입니다. 이 애플리케이션은 OpenAI, Google's YouTube API 및 Google Text-to-Speech를 활용하여 사용자에게 원활하고 인터랙티브한 드라이빙 경험을 제공합니다.

### 목차
1. [설치](#설치)
2. [구성](#구성)
3. [사용법](#사용법)
4. [API 엔드포인트](#api-엔드포인트)
5. [음성 명령](#음성-명령)
6. [파일 구조](#파일-구조)

### 설치

1. **레포지토리 클론:**
   ```sh
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **가상 환경 생성 및 활성화:**
   ```sh
   python -m venv venv
   source venv/bin/activate  # 윈도우에서는: venv\Scripts\activate
   ```

3. **필수 패키지 설치:**
   ```sh
   pip install -r requirements.txt
   ```

### 구성

1. **환경 변수 설정:**
   `.env` 파일을 생성하고, 다음과 같은 형식으로 API 키를 입력합니다:
   ```env
   OPENAI_API_KEY=<your-openai-api-key>
   GOOGLE_API_KEY=<your-google-api-key>
   ```

2. **로그 디렉토리 설정:**
   로그 파일을 저장할 디렉토리를 생성합니다:
   ```sh
   mkdir -p ../log
   ```

3. **사운드 파일 및 CSV 파일 준비:**
   프로젝트 디렉토리 내에 필요한 사운드 파일과 CSV 파일을 준비합니다:
   - `../sounds/ping-82822.mp3`
   - `../sounds/ding-36029.mp3`
   - `../csvs/car_info_list.csv`
   - `../csvs/seongsu_restaurant_final.csv`

### 사용법

1. **서버 실행:**
   FastAPI 서버를 실행합니다:
   ```sh
   uvicorn main:app --reload
   ```

2. **음성 명령 사용:**
   서버가 실행 중일 때, 음성 명령을 통해 차량 정보 조회, 음악 재생, 맛집 추천 등의 기능을 사용할 수 있습니다.

### API 엔드포인트

- **`POST /listen`**
  - 설명: 음성 명령을 인식하고 처리합니다.
  - 요청 바디: 
    ```json
    {
      "userId": "string",
      "userAgent": "string",
      "carCode": "string",
      "dttm": "string",
      "query": "string"
    }
    ```
  - 응답: 
    ```json
    {
      "success": true,
      "answerType": "string",
      "answer": "string"
    }
    ```

- **`POST /stop_music`**
  - 설명: 현재 재생 중인 음악을 중지합니다.
  - 응답: 
    ```json
    {
      "response": "음악 재생을 중지했습니다."
    }
    ```

### 음성 명령

- **음악 재생 관련 명령:**
  - "음악 재생", "틀어 줘", "들려줘" 등

- **맛집 추천 관련 명령:**
  - "맛집 추천", "맛집 알려줘", "맛집 추천해 줘" 등
  - 다양한 음식 종류에 대한 추천도 가능: "양식", "한식", "카페" 등

- **차량 정보 관련 명령:**
  - 차량 정보 조회를 요청하는 다양한 명령

### 파일 구조

```
DriveTalk/
├── main.py  # 메인 애플리케이션 코드
├── requirements.txt  # 필요한 패키지 목록
├── .env  # 환경 변수 파일
├── ../log/  # 로그 파일 디렉토리
├── ../sounds/  # 사운드 파일 디렉토리
└── ../csvs/  # CSV 파일 디렉토리
```

### 기여

프로젝트에 기여하고 싶다면, 풀 리퀘스트를 제출하거나 이슈를 생성해 주세요.

---

이 문서가 DriveTalk 프로젝트의 설치, 구성 및 사용법을 이해하는 데 도움이 되길 바랍니다. 추가 질문이 있거나 지원이 필요하면 언제든지 문의해 주세요.
