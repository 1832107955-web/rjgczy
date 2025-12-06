import os
import base64
import requests

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'docs', 'images', 'class_maps')
os.makedirs(OUT_DIR, exist_ok=True)

diagrams = {
    'Room': '''graph LR
    Room[Room]
    PowerOn((PowerOn))
    PowerOff((PowerOff))
    RequestState((RequestState))
    CheckRoomState((Check_RoomState))
    SetRoomState((Set_RoomState))
    CreateDoorCard((Create_DoorCard))

    Room --> PowerOn
    Room --> PowerOff
    Room --> RequestState
    Room --> CheckRoomState
    Room --> SetRoomState
    Room --> CreateDoorCard
''',

    'ServiceObject_Scheduler': '''graph LR
    SO[ServiceObject / Scheduler]
    PowerOn((PowerOn))
    PowerOff((PowerOff))
    ChangeTemp((ChangeTemp))
    ChangeSpeed((ChangeSpeed))
    Scheduling((调度策略: 时间片/抢占))

    SO --> PowerOn
    SO --> PowerOff
    SO --> ChangeTemp
    SO --> ChangeSpeed
    SO --> Scheduling
''',

    'DetailRecord': '''graph LR
    DR[DetailRecord]
    CreateDetail((Create_DetailRecord_AC))
    UpdateOnChangeSpeed((ChangeSpeed -> 详单))
    FinalizeOnPowerOff((PowerOff -> 结单))

    DR --> CreateDetail
    DR --> UpdateOnChangeSpeed
    DR --> FinalizeOnPowerOff
''',

    'AccommodationOrder_Customer': '''graph LR
    AO[AccommodationOrder / Customer]
    RegisteCustomer((Registe_CustomerInfo))
    CreateOrder((Create_Accommodation_Order))
    Deposit((Deposit))

    AO --> RegisteCustomer
    AO --> CreateOrder
    AO --> Deposit
''',

    'AccommodationBill': '''graph LR
    AB[AccommodationBill]
    CalcFee((calculate_Accommodation_Fee))
    CreateBill((Create_Accommodation_Bill))
    ProcessPayment((ProcessPayment))

    AB --> CalcFee
    AB --> CreateBill
    AB --> ProcessPayment
''',

    'ACBill': '''graph LR
    ACB[ACBill]
    CalcAC((calculate_AC_Fee))
    CreateACBill((Create_AC_Bill))
    ProcessPayment((ProcessPayment))

    ACB --> CalcAC
    ACB --> CreateACBill
    ACB --> ProcessPayment
''',

    'SimulationEngine': '''graph LR
    SE[SimulationEngine]
    UpdateRooms((update_rooms))
    CalculateCost((calculate_cost))
    TriggerScheduler((触发 Scheduler / 定时事件))

    SE --> UpdateRooms
    SE --> CalculateCost
    SE --> TriggerScheduler
''',
}

def render_to_png(mermaid_text: str, out_path: str):
    b64 = base64.urlsafe_b64encode(mermaid_text.encode('utf-8')).decode('ascii')
    url = f'https://mermaid.ink/img/{b64}'
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
    except Exception as e:
        print('Failed to fetch:', e)
        return False
    with open(out_path, 'wb') as f:
        f.write(r.content)
    return True

def main():
    results = []
    for name, text in diagrams.items():
        safe_name = name.replace(' ', '_')
        out_png = os.path.join(OUT_DIR, f'{safe_name}.png')
        ok = render_to_png(text, out_png)
        results.append((safe_name, ok, out_png))
        print('Wrote' if ok else 'Failed', out_png)
    print('\nSummary:')
    for r in results:
        print(r[0], 'OK' if r[1] else 'FAILED', r[2])

if __name__ == '__main__':
    main()
