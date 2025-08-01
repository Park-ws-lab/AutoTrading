# 🔥 Upbit Auto-Trading Bot (Multi-Ticker Version)

업비트 API를 사용한 **자동 매매 봇 템플릿**입니다.  
`pyupbit` 라이브러리를 기반으로 작성되었으며, 여러 종목을 동시에 감시하고 **단순 이동평균 크로스 전략**을 통해 매수/매도를 실행합니다.

---

## ⚙ 주요 특징

- **멀티 티커 지원:** `TICKERS` 리스트에 원하는 종목을 넣으면 여러 코인을 동시에 감시.
- **단순한 전략:** 5이평선과 20이평선의 크로스 신호로 매수/매도.
- **DRY-RUN 모드:** `DRY_RUN=True` 로 설정 시 **실제 주문 없이 시뮬레이션**만 수행.
- **구조가 단순하여 초보자도 바로 수정 가능.**

---

## 📂 프로젝트 구조

AutoTrading/<br>
 ├─ **.env**                   # 세팅 값 ✅<br>
 ├─ **Main.py**                # 실행 루프 스크립트<br>
 ├─ **Strategy.py**            # 매매 전략 스크립트 ✅<br>
 ├─ **Utils.py**               # 매매 함수 라이브러리 <br>
 ├─ **requirements.txt**       # 설치할 Python 패키지 목록<br>
 └─ **README.md**              # 프로젝트 설명<br>

여러분이 건드릴 파일은 ✅ 표시 된 파일들 입니다!

‼️ **.env** 파일에서는 매매에 필요한 값들을 설정하고,<br>
‼️ **Strategy.py** 파일에서 루프가 돌아갈 algorithm 메소드를 작성합니다.

---

## 🔧 설치 방법

### 1. Python 설치
- Python 3.8 이상을 권장합니다.
- [Python 공식 다운로드](https://www.python.org/downloads/)

### 2. 저장소 클론
- 프로젝트를 클론할 폴더로 이동한다. (cd 사용)
```bash
git clone https://github.com/Park-ws-lab/AutoTrading.git
```

### 3. 패키지 설치
- 클론한 AutoTrading 폴더 안에서 다음 명령어를 입력한다.
```bash
python3 -m pip install -r requirements.txt
```

## 📑 업비트 API 키 발급 방법

1. **업비트 회원가입 & 로그인**  
   [https://upbit.com](https://upbit.com) 에 접속하여 계정을 생성하고 로그인합니다.

2. **Open API 관리 페이지 이동**  
   [업비트 Open API 관리](https://upbit.com/mypage/open_api_management)로 들어갑니다.

3. **새 API 키 발급**  
   - **'Open API Key 생성'** 버튼 클릭.
   - API 키의 **이름(메모)**를 지정하고 **사용할 기능(자산조회, 주문조회, 주문하기)**을 선택합니다.  
     - **조회만 테스트하려면 조회 권한만 부여**해도 됩니다.
   - **IP 제한**  
     - 특정 IP에서만 접근하도록 제한할 수 있습니다. 서버 IP를 등록해두는 게 안전합니다.  
       (테스트용이면 **IP 제한 해제** 가능하지만 보안상 권장하지 않음.)

4. **Access Key / Secret Key 확인**  
   발급 후 **Access Key**와 **Secret Key**를 안전하게 저장하세요.  
   **Secret Key는 최초 발급 시만 표시**되므로 복사해두지 않으면 다시 확인할 수 없습니다.


---

## 🚀 실행 방법

### 1. 환경 변수(API 키) 설정
업비트 오픈 API 키를 발급받아 환경변수로 지정합니다.

#### Linux / Mac
```bash
export UPBIT_ACCESS_KEY="발급받은_액세스키"
export UPBIT_SECRET_KEY="발급받은_시크릿키"
```

#### Windows PowerShell
```powershell
setx UPBIT_ACCESS_KEY "발급받은_액세스키"
setx UPBIT_SECRET_KEY "발급받은_시크릿키"
```

> 키를 입력하지 않으면 **조회는 가능하지만 주문이 실패**합니다.  
> 테스트만 할 경우에는 `DRY_RUN=True` 로 두면 키가 없어도 됩니다.

---

### 2. 실행
```bash
python multi_upbit_bot.py
```

실행 시 다음과 같은 로그가 출력됩니다:
```
=== 시작 ===
TICKERS=['KRW-BTC', 'KRW-ETH'], INTERVAL=minute1, DRY_RUN=True
[KRW-BTC][SIGNAL] HOLD
[KRW-ETH][SIGNAL] BUY
...
```

---

## ⚠ 주의사항

1. **실거래 전 충분히 테스트**
   - `DRY_RUN=True` 로 반드시 전략과 로직을 먼저 검증하세요.
   - 잘못된 전략으로 실거래 시 큰 손실이 발생할 수 있습니다.

2. **주문 최소 금액 확인**
   - 업비트 최소 주문 금액은 **5,000 KRW**입니다.  
     `ORDER_BUDGET`를 5,000원 이상으로 설정하세요.

3. **레이트 리밋**
   - API 호출 제한이 있습니다.  
     `SLEEP_SECONDS`를 너무 낮추면 `429 Too Many Requests` 에러가 발생할 수 있습니다.

4. **전략 커스터마이징**
   - `algorithm()` 함수를 수정하여 원하는 매매 전략을 직접 구현하세요.

---

## 🧩 커스터마이징 예시

### 1. 티커 추가
```python
TICKERS = ["KRW-BTC", "KRW-ETH", "KRW-XRP"]
```

### 2. 예산 변경
```python
ORDER_BUDGET = 20000  # 2만원 매수
```

### 3. 전략 변경
가격이 전봉보다 오르면 BUY:
```python
def algorithm(candles, ticker: str):
    if candles["close"].iloc[-1] > candles["close"].iloc[-2]:
        return "BUY"
    return "HOLD"
```

---

## 🧑‍💻 기여 (Contribution)

- 버그 제보, 전략 개선, 코드 간소화 등 PR/Issue 환영합니다.

---

## 📜 라이선스

이 프로젝트는 **MIT 라이선스**를 따릅니다.  
상업적 사용 가능하지만, **모든 리스크는 사용자 본인에게 있습니다.**

---

## 💡 참고 자료

- [업비트 오픈 API 문서](https://docs.upbit.com/)
- [pyupbit 깃허브](https://github.com/sharebook-kr/pyupbit)
