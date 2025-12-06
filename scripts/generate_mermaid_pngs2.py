import base64
import requests
import os

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

results = {}
for name, code in diagrams.items():
    b64 = base64.urlsafe_b64encode(code.encode('utf-8')).decode('ascii')
    url = f'https://mermaid.ink/img/{b64}'
    headers = {'Accept': 'image/png'}
    try:
        r = requests.get(url, headers=headers, timeout=30)
        if r.status_code == 200:
            ctype = r.headers.get('Content-Type','')
            if 'png' in ctype:
                out = os.path.join(OUT_DIR, f'{name}.png')
                with open(out, 'wb') as f:
                    f.write(r.content)
                results[name] = out
                print('Wrote', out)
            else:
                results[name] = f'Unexpected Content-Type: {ctype}'
                print('Unexpected content type', ctype)
        else:
            results[name] = f'HTTP {r.status_code}'
            print('Failed', name, r.status_code)
    except Exception as e:
        results[name] = f'ERROR: {e}'
        print('Exception', name, e)

print('\nResults:')
for k, v in results.items():
    print(k, '->', v)
