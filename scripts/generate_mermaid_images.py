import os
import base64
import requests

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'docs', 'images')
os.makedirs(OUT_DIR, exist_ok=True)

diagrams = {
    'create_accommodation_order': '''sequenceDiagram
    participant Reception as 前台
    participant API as System
    participant Customer as 顾客
    participant Room as 客房
    participant Order as 住宿订单

    Reception->>API: Create_Accommodation_Order(Customer_id, Room_id)
    API->>Customer: Create()/关联房间
    Note right of Customer: 顾客与客房建立关联
    API->>Order: Create()
    Note right of Order: 住宿订单对象被创建\n订单属性被赋值
    API->>Room: 更新状态(Occupied)
    Note right of Room: 客房状态、信息被修改
    API-->>Reception: Return(isOK)
''',

    'create_accommodation_bill': '''sequenceDiagram
    participant API as System
    participant AccBill as 住宿费账单
    participant Room as 客房
    participant Reception as 前台

    API->>AccBill: calculate_Accommodation_Fee(days, fee_per_day)
    Note right of AccBill: 计算住宿总费用\n创建住宿费账单对象
    AccBill-->>API: Return(Total_Fee_of_Accommodation)
    API->>AccBill: Create_Accommodation_Bill(Room_Id, date)
    Note right of AccBill: 设置账单其他属性\n保存账单
    AccBill-->>API: Return(isOK)
    API-->>Reception: Return(isOK)
''',

    'create_ac_bill': '''sequenceDiagram
    participant API as System
    participant ACBill as 空调使用费账单
    participant Detail as 详单
    participant Room as 客房

    API->>Detail: query_DetailRecords(RoomId, date_in, date_out)
    Detail-->>API: Return(list_DR_AC)
    API->>ACBill: calculate_AC_Fee(list_DR_AC)
    Note right of ACBill: 计算空调使用总费用\n创建空调账单对象
    ACBill-->>API: Return(Total_Fee_of_AC)
    API->>ACBill: Create_AC_Bill(Room_Id, date)
    Note right of ACBill: 关联详单并保存账单\n修改账单属性
    ACBill-->>API: Return(isOK)
''',

    'create_detailrecord_ac': '''sequenceDiagram
    participant API as System
    participant Room as 客房
    participant Service as ServiceObject
    participant Detail as 详单

    API->>Room: query_AC_usage(RoomId, date_in, date_out)
    Note right of Room: 返回空调使用请求记录
    Room-->>API: Return(list_of_requests)
    API->>Detail: Create_DetailRecord_AC(RoomId, date_in, date_out)
    Note right of Detail: 为每条请求生成详单项\n(请求时间, 持续时间, 风速, 费率, 费用)
    Detail-->>API: Return(list_DR_AC)
'''
}

def sanitize(text: str) -> str:
    # keep arrows intact, remove stray quotes and convert <br> to newline
    t = text.replace('"', '').replace("'", '')
    t = t.replace('<br/>', '\n').replace('<br>', '\n')
    t = t.replace('\r\n', '\n').replace('\r', '\n')
    return t


def render_via_mermaid_ink(mermaid_text: str):
    b64 = base64.urlsafe_b64encode(mermaid_text.encode('utf-8')).decode('ascii')
    url = f'https://mermaid.ink/svg/{b64}'
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
    except Exception as e:
        return False, f'HTTP error: {e}', None
    return True, 'ok', r.content


for name, diag in diagrams.items():
    cleaned = sanitize(diag)
    ok, info, content = render_via_mermaid_ink(cleaned)
    if not ok:
        print(f'Failed to render {name}: {info}')
        continue
    out_path = os.path.join(OUT_DIR, f'{name}.svg')
    with open(out_path, 'wb') as f:
        f.write(content)
    print(f'Wrote {out_path}')
    # Also fetch raster PNG via /img/<b64>
    try:
        b64 = base64.urlsafe_b64encode(cleaned.encode('utf-8')).decode('ascii')
        img_url = f'https://mermaid.ink/img/{b64}'
        r2 = requests.get(img_url, timeout=20)
        r2.raise_for_status()
        out_png = os.path.join(OUT_DIR, f'{name}.png')
        with open(out_png, 'wb') as f2:
            f2.write(r2.content)
        print(f'Wrote {out_png}')
    except Exception as e:
        print(f'Failed to render PNG for {name}: {e}')
