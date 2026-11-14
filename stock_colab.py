# 전체를 Colab 코드 셀 하나에 붙여넣고 실행하세요.
import importlib.util
import math
import subprocess
import sys
from unicodedata import normalize
from datetime import datetime

missing = [name for name in ("ipywidgets", "yfinance") if importlib.util.find_spec(name) is None]
if missing:
    subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])

import ipywidgets as widgets
import yfinance as yf
from IPython.display import clear_output, display

if "google.colab" in sys.modules:
    from google.colab import output
    output.enable_custom_widget_manager()


class StockSimulator:
    def __init__(self):
        self.cash = 10_000_000
        self.rate = 1350
        self.holdings = {}
        self.quotes = {}
        self.ticker = widgets.Text(description="미국 종목", placeholder="AAPL")
        self.quantity = widgets.BoundedIntText(description="수량", value=1, min=1, max=1_000_000)
        self.result = widgets.Output()
        buttons = []
        for label, action in (("가격 조회", self.lookup), ("가상 매수", self.buy), ("가상 매도", self.sell)):
            button = widgets.Button(description=label)
            button.on_click(action)
            buttons.append(button)
        self.view = widgets.VBox([widgets.HTML("<h2>주식 모의 거래</h2>"),
                                  self.ticker, self.quantity, widgets.HBox(buttons), self.result])

    def lookup(self, _):
        symbol = "".join(normalize("NFKC", self.ticker.value).split()).upper()
        if not symbol:
            self.render("종목 코드를 입력하세요.")
            return
        try:
            ticker = yf.Ticker(symbol)
            prices = ticker.history(period="5d", auto_adjust=False, timeout=8)["Close"].dropna()
            usd = float(prices.iloc[-1])
            if ticker.history_metadata.get("currency") != "USD" or not math.isfinite(usd) or usd <= 0:
                raise ValueError
        except Exception:
            self.render("USD 종목의 가격을 가져오지 못했습니다. 종목 코드와 연결 상태를 확인하세요.")
            return
        price = round(usd * self.rate)
        self.quotes[symbol] = price
        self.render(f"{symbol} 최근 가격 {price:,}원 · 조회 {datetime.now().astimezone():%m/%d %H:%M %Z}")

    def buy(self, _):
        self.trade(self.quantity.value)

    def sell(self, _):
        self.trade(-self.quantity.value)

    def trade(self, quantity):
        symbol = "".join(normalize("NFKC", self.ticker.value).split()).upper()
        if symbol not in self.quotes:
            self.render("먼저 해당 종목의 가격을 조회하세요.")
            return
        owned = self.holdings.get(symbol, 0)
        payment = quantity * self.quotes[symbol]
        if owned + quantity < 0 or payment > self.cash:
            self.render("보유 수량 또는 현금이 부족합니다.")
            return
        self.cash -= payment
        if owned + quantity:
            self.holdings[symbol] = owned + quantity
        else:
            self.holdings.pop(symbol, None)
        self.render(f"{symbol} {abs(quantity)}주 {'매수' if quantity > 0 else '매도'} 완료")

    def render(self, message=""):
        with self.result:
            clear_output(wait=True)
            if message:
                print(message)
            print(f"모의 거래 · 고정 환율 {self.rate:,}원/USD · 수수료 미반영")
            print(f"보유 현금 {self.cash:,}원")
            total = self.cash
            for symbol, shares in sorted(self.holdings.items()):
                value = shares * self.quotes[symbol]
                total += value
                print(f"{symbol} · {shares}주 · 평가액 {value:,}원")
            print(f"총자산 {total:,}원")


simulator = StockSimulator()
display(simulator.view)
simulator.render()
