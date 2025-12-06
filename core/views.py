from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from .models import Room, Bill, ACSession
from .services.scheduler import Scheduler
from .services.config import Config
from django.utils import timezone
import json
import datetime

def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # 1. Try Admin/Staff Login
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('core:index')
            
        # 2. Try Room Login
        try:
            room = Room.objects.get(username=username, password=password)
            # Store room_id in session
            request.session['room_id'] = room.room_id
            return redirect('core:customer', room_id=room.room_id)
        except Room.DoesNotExist:
            pass
            
        return render(request, 'core/login.html', {'error': '用户名或密码错误'})
        
    if request.user.is_authenticated:
        return redirect('core:index')
        
    return render(request, 'core/login.html')

@login_required
def index(request):
    rooms = Room.objects.all().order_by('room_id')
    floors = {}
    for room in rooms:
        try:
            floor = int(room.room_id) // 100
            if floor not in floors:
                floors[floor] = []
            floors[floor].append(room)
        except ValueError:
            pass # Skip invalid room ids
            
    # Get Scheduler queues from DB state (since Scheduler instance memory is not shared)
    serving_queue = list(Room.objects.filter(status='SERVING'))
    waiting_queue = list(Room.objects.filter(status='WAITING'))
    
    # Sort Waiting Queue to match Scheduler logic: Priority (Desc), Wait Timeout (Asc)
    # Higher priority first. If same priority, smaller timeout (closer to expiration/waited longer) first.
    waiting_queue.sort(key=lambda r: (
        -Config.SPEED_PRIORITY.get(r.fan_speed, 0),
        r.wait_timeout
    ))
            
    return render(request, 'core/index.html', {
        'floors': dict(sorted(floors.items())),
        'serving_queue': serving_queue,
        'waiting_queue': waiting_queue
    })

@login_required
def monitor(request):
    return render(request, 'core/monitor.html')

def customer(request, room_id):
    # Check authentication
    if not request.user.is_authenticated:
        if request.session.get('room_id') != room_id:
            return redirect('core:login')
            
    room = get_object_or_404(Room, room_id=room_id)
    return render(request, 'core/customer.html', {'room': room})

@login_required
def checkin_page(request):
    rooms = Room.objects.filter(occupancy_status='EMPTY').order_by('room_id')
    return render(request, 'core/checkin.html', {'rooms': rooms})

@login_required
def checkout_page(request):
    rooms = Room.objects.filter(occupancy_status='OCCUPIED').order_by('room_id')
    return render(request, 'core/checkout.html', {'rooms': rooms})

@login_required
def bill_history(request):
    bills = Bill.objects.all().order_by('-check_out_time')
    return render(request, 'core/bill_history.html', {'bills': bills})

@login_required
def bill_detail(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id)
    ac_sessions = ACSession.objects.filter(bill=bill).order_by('start_time')
    
    # Calculate days for display (re-calculate or store? We didn't store days in Bill model, only fees)
    # But we can infer or just show fees. The user asked for "detailed bill".
    # Let's calculate days just for display if needed, or just show the fees.
    # Accommodation fee / daily rate = days (roughly).
    # But room daily rate might have changed.
    # Let's just show what we have.
    
    return render(request, 'core/bill_detail.html', {
        'bill': bill,
        'ac_sessions': ac_sessions
    })

# APIs

def api_room_status(request):
    # Only return occupied rooms for monitoring
    rooms = Room.objects.filter(occupancy_status='OCCUPIED').values()
    return JsonResponse({'rooms': list(rooms)})

def api_room_detail(request, room_id):
    room = get_object_or_404(Room, room_id=room_id)
    data = {
        'room_id': room.room_id,
        'current_temp': room.current_temp,
        'target_temp': room.target_temp,
        'fan_speed': room.fan_speed,
        'mode': room.mode,
        'fee': room.fee,
        'status': room.status,
        'is_on': room.is_on,
        'occupancy_status': room.occupancy_status
    }
    return JsonResponse(data)

@csrf_exempt
def api_control_room(request, room_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            room = get_object_or_404(Room, room_id=room_id)
            scheduler = Scheduler()
            
            # Handle AC Session Logic
            if 'is_on' in data:
                new_state = data['is_on']
                if new_state and not room.is_on:
                    # Turning ON: Start Session
                    ACSession.objects.create(
                        room=room,
                        mode=room.mode,
                        fan_speed=room.fan_speed,
                        start_temp=room.current_temp,
                        target_temp=room.target_temp,
                        initial_fee=room.fee
                    )
                    scheduler.request_service(room_id)
                elif not new_state and room.is_on:
                    # Turning OFF: End Session
                    session = ACSession.objects.filter(room=room, end_time__isnull=True).last()
                    if session:
                        session.end_time = timezone.now()
                        session.fee = room.fee - session.initial_fee
                        session.save()
                    scheduler.stop_service(room_id)
                room.is_on = new_state
            
            # If settings change while ON, maybe split session? 
            # For simplicity, we just update the room settings. 
            # If strict logging is needed, we should close current and start new.
            # Let's implement strict logging for better detail.
            if room.is_on and ('mode' in data or 'fan_speed' in data or 'target_temp' in data):
                 # Close current
                session = ACSession.objects.filter(room=room, end_time__isnull=True).last()
                if session:
                    session.end_time = timezone.now()
                    session.fee = room.fee - session.initial_fee
                    session.save()
                
                # Update room
                if 'target_temp' in data: room.target_temp = float(data['target_temp'])
                if 'fan_speed' in data: room.fan_speed = data['fan_speed']
                if 'mode' in data: room.mode = data['mode']
                
                # Start new
                ACSession.objects.create(
                    room=room,
                    mode=room.mode,
                    fan_speed=room.fan_speed,
                    start_temp=room.current_temp,
                    target_temp=room.target_temp,
                    initial_fee=room.fee
                )
            else:
                # Just update settings if OFF
                if 'target_temp' in data: room.target_temp = float(data['target_temp'])
                if 'fan_speed' in data: room.fan_speed = data['fan_speed']
                if 'mode' in data: room.mode = data['mode']

            room.save()
            
            # Requirement C: Adjusting fan speed counts as new request, adjusting temp does not.
            # We only request service if:
            # 1. Room was just turned ON
            # 2. Fan speed changed (Priority changed)
            # 3. Mode changed (Treat as major change, though not explicitly specified, safer to re-eval)
            should_request_service = False
            
            if 'is_on' in data and data['is_on']:
                should_request_service = True
            elif room.is_on:
                if 'fan_speed' in data:
                    should_request_service = True
                # If only target_temp changed, we DO NOT request service to avoid resetting wait timer.
            
            if should_request_service:
                scheduler.request_service(room_id)
                
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error'}, status=400)

@csrf_exempt
def api_checkin(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        room_id = data.get('room_id')
        guest_id = data.get('guest_id')
        
        room = get_object_or_404(Room, room_id=room_id)
        if room.occupancy_status == 'OCCUPIED':
            return JsonResponse({'status': 'error', 'message': 'Room occupied'})
            
        room.occupancy_status = 'OCCUPIED'
        room.guest_id = guest_id
        room.check_in_time = timezone.now()
        room.fee = 0.0 # Reset AC fee
        room.save()
        return JsonResponse({'status': 'ok'})

@csrf_exempt
def api_checkout(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        room_id = data.get('room_id')
        
        room = get_object_or_404(Room, room_id=room_id)
        
        if room.occupancy_status != 'OCCUPIED':
             return JsonResponse({'status': 'error', 'message': 'Room not occupied'})

        # Close any active AC session
        if room.is_on:
            session = ACSession.objects.filter(room=room, end_time__isnull=True).last()
            if session:
                session.end_time = timezone.now()
                session.fee = room.fee - session.initial_fee
                session.save()
            room.is_on = False
            Scheduler().stop_service(room_id)

        # Calculate Accommodation Fee
        check_out_time = timezone.now()
        check_in_time = room.check_in_time or check_out_time # Fallback
        
        # Logic: Day 1 checkin. Day 2 12:00 is deadline.
        # If checkout > 12:00, count as new day.
        # Calculate number of nights.
        # If check_in is today, and now is today -> 1 day.
        
        # Algorithm:
        # 1. Get dates.
        # 2. Base days = (checkout_date - checkin_date).days
        # 3. If checkout_time > 12:00:00, days += 1
        # 4. If days == 0, days = 1.
        
        days = (check_out_time.date() - check_in_time.date()).days
        if check_out_time.hour >= 12:
            days += 1
        if days == 0:
            days = 1
            
        accommodation_fee = days * room.daily_rate
        
        # Create Bill
        bill = Bill.objects.create(
            room=room,
            guest_id=room.guest_id or "Unknown",
            check_in_time=check_in_time,
            check_out_time=check_out_time,
            ac_fee=room.fee,
            accommodation_fee=accommodation_fee,
            total_amount=room.fee + accommodation_fee
        )
        
        # Link AC Sessions to Bill
        # Find all sessions for this room that don't have a bill yet?
        # Or better, sessions that happened after check_in_time.
        sessions = ACSession.objects.filter(room=room, start_time__gte=check_in_time, bill__isnull=True)
        
        # Capture details BEFORE updating the bill field, or use the list
        session_list = list(sessions)
        
        sessions.update(bill=bill)
        
        session_details = []
        for s in session_list:
            session_details.append({
                'start': s.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                'end': s.end_time.strftime("%Y-%m-%d %H:%M:%S") if s.end_time else "N/A",
                'mode': s.mode,
                'fan': s.fan_speed,
                'fee': s.fee
            })

        # Reset Room
        room.occupancy_status = 'EMPTY'
        room.guest_id = None
        room.fee = 0.0
        room.total_fee = 0.0
        room.check_in_time = None
        room.status = 'IDLE'
        room.save()
        
        return JsonResponse({
            'status': 'ok',
            'bill': {
                'room_id': room.room_id,
                'days': days,
                'daily_rate': room.daily_rate,
                'accommodation_fee': bill.accommodation_fee,
                'ac_fee': bill.ac_fee,
                'total': bill.total_amount,
                'ac_details': session_details
            }
        })

def api_scheduler_queues(request):
    # Get Scheduler queues from DB state
    serving_queue = Room.objects.filter(status='SERVING').values('room_id', 'fan_speed', 'service_time')
    waiting_queue = list(Room.objects.filter(status='WAITING'))
    
    # Sort Waiting Queue to match Scheduler logic
    waiting_queue.sort(key=lambda r: (
        -Config.SPEED_PRIORITY.get(r.fan_speed, 0),
        r.wait_timeout
    ))
    
    waiting_data = [{'room_id': r.room_id, 'fan_speed': r.fan_speed, 'wait_timeout': r.wait_timeout} for r in waiting_queue]
    
    return JsonResponse({
        'serving': list(serving_queue),
        'waiting': waiting_data
    })

