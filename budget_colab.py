# 파일 전체를 Google Colab 코드 셀 하나에 붙여넣고 실행하세요.
import importlib.util
import subprocess
import sys

missing = [name for name in ('ipywidgets', 'pandas', 'matplotlib')
           if importlib.util.find_spec(name) is None]
if missing:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', *missing])

if 'google.colab' in sys.modules:
    from google.colab import output
    output.enable_custom_widget_manager()

import json
from pathlib import Path
from uuid import uuid4
from tempfile import NamedTemporaryFile
import ipywidgets as widgets
from IPython.display import display, clear_output
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
from datetime import datetime

# 한글 폰트 설정
matplotlib.rcParams['font.family'] = ['NanumGothic', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

# 데이터 저장소
store = Path('budget_records.json')
all_records = json.loads(store.read_text(encoding='utf-8')) if store.exists() else []
records = []
month = widgets.Text(value=datetime.now().strftime('%Y-%m'), description='조회 월')
selected = widgets.Dropdown(description='거래 선택')
edit_btn = widgets.Button(description='선택 거래 수정')
delete_btn = widgets.Button(description='선택 거래 삭제')
confirm_delete = widgets.Checkbox(value=False, description='삭제 확인')

def save_records(updated):
    with NamedTemporaryFile(dir=store.parent, delete=False, mode='w', encoding='utf-8') as file:
        temporary = Path(file.name)
        json.dump(updated, file, ensure_ascii=False, indent=2)
    try:
        temporary.replace(store)
    finally:
        temporary.unlink(missing_ok=True)
    all_records[:] = updated


# ─────────────────────────────────────────
# 위젯 정의
# ─────────────────────────────────────────

# 입력 위젯
type_toggle = widgets.ToggleButtons(
    options=[('💸 지출', 'expense'), ('💵 수입', 'income')],
    value='expense',
    description='',
    style={'button_width': '120px', 'font_weight': 'bold'}
)

category_dropdown = widgets.Dropdown(
    options=['식비', '교통', '쇼핑', '의료', '문화/여가', '월급', '부수입', '기타'],
    value='식비',
    description='카테고리',
    style={'description_width': '70px'},
    layout=widgets.Layout(width='220px')
)

amount_input = widgets.IntText(
    value=0,
    description='금액 (원)',
    style={'description_width': '70px'},
    layout=widgets.Layout(width='220px')
)

memo_input = widgets.Text(
    value='',
    placeholder='메모 (선택)',
    description='메모',
    style={'description_width': '70px'},
    layout=widgets.Layout(width='300px')
)

add_btn = widgets.Button(
    description='+ 추가하기',
    button_style='primary',
    layout=widgets.Layout(width='130px', height='35px')
)

reset_btn = widgets.Button(
    description='🗑 초기화',
    button_style='danger',
    layout=widgets.Layout(width='100px', height='35px')
)

# 출력 영역
status_out   = widgets.Output()   # 상태 메시지
summary_out  = widgets.Output()   # 수입/지출 요약
table_out    = widgets.Output()   # 거래 내역 테이블
chart_out    = widgets.Output()   # 차트

# ─────────────────────────────────────────
# 헬퍼 함수
# ─────────────────────────────────────────

def fmt_won(n):
    return f"{n:,}원"

def update_summary():
    total_income  = sum(r['amount'] for r in records if r['type'] == 'income')
    total_expense = sum(r['amount'] for r in records if r['type'] == 'expense')
    balance = total_income - total_expense
    color = '#27ae60' if balance >= 0 else '#e74c3c'

    with summary_out:
        clear_output(wait=True)
        print(f"""
┌─────────────────────────────────┐
│  💵 총 수입  :  {fmt_won(total_income):>14}  │
│  💸 총 지출  :  {fmt_won(total_expense):>14}  │
│─────────────────────────────────│
│  {'🟢' if balance >= 0 else '🔴'} 잔  액  :  {fmt_won(balance):>14}  │
└─────────────────────────────────┘""")

def update_table():
    with table_out:
        clear_output(wait=True)
        if not records:
            print("아직 기록이 없습니다. 위에서 항목을 추가해 보세요!")
            return
        df = pd.DataFrame(records, columns=['type', 'category', 'amount', 'memo', 'time'])
        df['type']   = df['type'].map({'income': '💵 수입', 'expense': '💸 지출'})
        df['amount'] = df['amount'].apply(fmt_won)
        df.columns   = ['유형', '카테고리', '금액', '메모', '시간']
        df = df[['시간', '유형', '카테고리', '금액', '메모']]
        display(df.tail(10).reset_index(drop=True))

def update_chart():
    with chart_out:
        clear_output(wait=True)
        if not records:
            return

        expenses = [r for r in records if r['type'] == 'expense']

        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        fig.patch.set_facecolor('#f8f9fa')

        # ── 왼쪽: 카테고리별 지출 도넛 차트
        ax1 = axes[0]
        if expenses:
            df_exp = pd.DataFrame(expenses)
            cat_sum = df_exp.groupby('category')['amount'].sum()
            colors = ['#FF6B6B','#4ECDC4','#45B7D1','#96CEB4',
                      '#FFEAA7','#DDA0DD','#98D8C8','#F7DC6F']
            wedges, texts, autotexts = ax1.pie(
                cat_sum.values,
                labels=cat_sum.index,
                autopct='%1.1f%%',
                colors=colors[:len(cat_sum)],
                wedgeprops=dict(width=0.55, edgecolor='white', linewidth=2),
                pctdistance=0.8,
                startangle=90
            )
            for t in autotexts:
                t.set_fontsize(9)
            ax1.set_title('카테고리별 지출 비율', fontsize=13, fontweight='bold', pad=12)
        else:
            ax1.text(0.5, 0.5, '지출 내역 없음', ha='center', va='center',
                     fontsize=13, color='gray', transform=ax1.transAxes)
            ax1.set_title('카테고리별 지출 비율', fontsize=13, fontweight='bold')
            ax1.axis('off')

        # ── 오른쪽: 수입 vs 지출 막대 차트
        ax2 = axes[1]
        total_income  = sum(r['amount'] for r in records if r['type'] == 'income')
        total_expense = sum(r['amount'] for r in records if r['type'] == 'expense')
        bars = ax2.bar(
            ['💵 수입', '💸 지출'],
            [total_income, total_expense],
            color=['#2ecc71', '#e74c3c'],
            width=0.45,
            edgecolor='white',
            linewidth=1.5
        )
        for bar, val in zip(bars, [total_income, total_expense]):
            ax2.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(total_income, total_expense) * 0.02,
                fmt_won(val),
                ha='center', va='bottom', fontsize=10, fontweight='bold'
            )
        ax2.set_title('수입 vs 지출', fontsize=13, fontweight='bold', pad=12)
        ax2.set_ylabel('금액 (원)', fontsize=10)
        ax2.yaxis.set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda x, _: f'{int(x):,}')
        )
        ax2.set_facecolor('#f8f9fa')
        ax2.spines[['top','right']].set_visible(False)

        plt.tight_layout()
        plt.show()

def refresh_all():
    records[:] = [r for r in all_records if r['time'].startswith(month.value.strip())]
    selected.options = [(f"{r['time']} · {r['category']} · {r['amount']:,}원 · {r['memo']}", r['id']) for r in records]

    update_summary()
    update_table()
    update_chart()

# ─────────────────────────────────────────
# 이벤트 핸들러
# ─────────────────────────────────────────

def on_type_change(change):
    """수입/지출 전환 시 카테고리 자동 변경"""
    if change['new'] == 'expense':
        category_dropdown.options = ['식비', '교통', '쇼핑', '의료', '문화/여가', '기타']
    else:
        category_dropdown.options = ['월급', '부수입', '용돈', '환급', '기타']

def on_add_clicked(b):
    """추가 버튼 클릭"""
    amount = amount_input.value
    with status_out:
        clear_output(wait=True)
        if amount <= 0:
            print("⚠️  금액은 1원 이상 입력해 주세요.")
            return

        try:
            save_records(all_records + [{
                'id': uuid4().hex, 'type': type_toggle.value,
                'category': category_dropdown.value, 'amount': amount,
                'memo': memo_input.value or '-',
                'time': datetime.now().strftime('%Y-%m-%d %H:%M')
            }])
        except OSError:
            print('저장에 실패했습니다. 폴더 쓰기 권한을 확인하세요.')
            return
        month.value = datetime.now().strftime('%Y-%m')
        icon = '💸' if type_toggle.value == 'expense' else '💵'
        print(f"{icon}  [{category_dropdown.value}]  {fmt_won(amount)}  추가 완료!")

    # 입력 초기화
    amount_input.value = 0
    memo_input.value   = ''
    refresh_all()

def change_selected(delete=False):
    with status_out:
        clear_output(wait=True)
        if selected.value is None:
            print('거래를 선택하세요.')
            return
        if delete and not confirm_delete.value:
            print('삭제 확인을 선택하세요.')
            return
        if not delete and amount_input.value <= 0:
            print('수정할 유형·분류·내용과 1원 이상의 금액을 입력하세요.')
            return
        updated = []
        for record in all_records:
            if record['id'] != selected.value:
                updated.append(record)
            elif not delete:
                updated.append(dict(record, type=type_toggle.value, category=category_dropdown.value,
                                    amount=amount_input.value, memo=memo_input.value or '-'))
        try:
            save_records(updated)
        except OSError:
            print('저장에 실패했습니다.')
            return
        confirm_delete.value = False
        print('삭제했습니다.' if delete else '수정했습니다.')
    refresh_all()

# 이벤트 연결
type_toggle.observe(on_type_change, names='value')
add_btn.on_click(on_add_clicked)
month.observe(lambda _: refresh_all(), names='value')
edit_btn.on_click(lambda _: change_selected())
delete_btn.on_click(lambda _: change_selected(delete=True))

# ─────────────────────────────────────────
# 레이아웃 조립 & 출력
# ─────────────────────────────────────────

title = widgets.HTML(
    '<h2 style="margin:0 0 4px 0; color:#2c3e50;">💰 미니 가계부</h2>'
    '<p style="margin:0; color:#7f8c8d; font-size:13px;">수입과 지출을 기록하고 차트로 확인하세요</p>'
    '<hr style="border:none; border-top:2px solid #ecf0f1; margin: 8px 0;">'
)

input_row1 = widgets.HBox([type_toggle],
    layout=widgets.Layout(margin='4px 0'))
input_row2 = widgets.HBox([category_dropdown, amount_input],
    layout=widgets.Layout(gap='12px', margin='4px 0'))
input_row3 = widgets.HBox([memo_input, add_btn],
    layout=widgets.Layout(gap='8px', align_items='center', margin='4px 0'))

input_box = widgets.VBox(
    [title, input_row1, input_row2, input_row3, status_out],
    layout=widgets.Layout(
        border='1px solid #dfe6e9',
        padding='16px',
        border_radius='8px',
        margin='0 0 12px 0',
        background_color='#ffffff'
    )
)

summary_label = widgets.HTML('<b style="font-size:14px;">📊 요약</b>')
summary_box   = widgets.VBox([summary_label, summary_out])

table_label   = widgets.HTML('<b style="font-size:14px;">📋 최근 거래 내역 (최대 10건)</b>')
table_box     = widgets.VBox(
    [table_label, month, selected, widgets.HBox([edit_btn, delete_btn]), confirm_delete, table_out],
    layout=widgets.Layout(
        border='1px solid #dfe6e9',
        padding='12px',
        border_radius='8px',
        margin='0 0 12px 0'
    )
)

chart_label   = widgets.HTML('<b style="font-size:14px;">📈 차트</b>')
chart_box     = widgets.VBox(
    [chart_label, chart_out],
    layout=widgets.Layout(
        border='1px solid #dfe6e9',
        padding='12px',
        border_radius='8px'
    )
)

app = widgets.VBox([input_box, summary_box, table_box, chart_box])

# 초기 화면 렌더링
refresh_all()
display(app)
