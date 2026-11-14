# 파이썬 실습 프로젝트

가계부와 주식 시뮬레이션 코드를 모아 둔 저장소입니다.

| 프로젝트 | 내용 | 코드 |
| --- | --- | --- |
| 가계부 | 수입과 지출을 입력하고 내역을 확인하는 Jupyter Notebook | [Budget book.ipynb](Budget%20book.ipynb) |
| 주식 시뮬레이션 | 가상으로 주식 거래를 연습하는 Python 코드 | [stock_simulator.py](stock_simulator.py) |

가계부를 직접 실행하려면 Jupyter에서 노트북을 열고 코드 셀을 실행하세요. 필요한 패키지는 `ipywidgets`, `pandas`, `matplotlib`입니다.

가계부는 변경 내용을 로컬 `budget_records.json`에 저장합니다. 조회 월은 `YYYY-MM`으로 입력하고, 수정하려면 거래를 선택한 뒤 새 값을 입력하세요.

주식 시뮬레이션은 `python -m pip install yfinance matplotlib`로 패키지를 설치한 뒤 `python stock_simulator.py`로 실행합니다. 각 종목의 최근 조회 가격을 평가에 사용하며, 조회 시각과 고정 적용 환율을 표시합니다.
