import time
import threading
from core.models import Room
from core.logic.config import Config
from core.logic.scheduler import Scheduler

class SimulationEngine:
    def __init__(self):
        self.scheduler = Scheduler()
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)

    def start(self):
        self.thread.start()
        print("[Simulation] Started.")

    def stop(self):
        self.running = False
        print("[Simulation] Stopped.")

    def _run_loop(self):
        while self.running:
            time.sleep(1.0) # 1 second tick
            try:
                self._update_rooms()
            except Exception as e:
                print(f"[Simulation] Error: {e}")

    def _update_rooms(self):
        rooms = Room.objects.all()
        for room in rooms:
            if not room.is_on:
                self._recover_temperature(room)
                room.save()
                continue

            is_active = (room.status == 'SERVING')

            if is_active:
                self._apply_ac_effect(room)
                self._calculate_cost(room)
            else:
                self._recover_temperature(room)

            self._check_target_reached(room)
            room.save()

    def _apply_ac_effect(self, room):
        rate_per_min = Config.TEMP_CHANGE_RATE.get(room.fan_speed, 0.5)
        change_per_sec = rate_per_min / 60.0

        if room.mode == 'COOL':
            room.current_temp -= change_per_sec
            if room.current_temp < room.target_temp:
                room.current_temp = room.target_temp
        else: # HEAT
            room.current_temp += change_per_sec
            if room.current_temp > room.target_temp:
                room.current_temp = room.target_temp

    def _recover_temperature(self, room):
        ambient_temp = Config.AMBIENT_TEMP
        recovery_rate_per_min = 0.5
        change_per_sec = recovery_rate_per_min / 60.0

        if room.current_temp < ambient_temp:
            room.current_temp += change_per_sec
            if room.current_temp > ambient_temp:
                room.current_temp = ambient_temp
        elif room.current_temp > ambient_temp:
            room.current_temp -= change_per_sec
            if room.current_temp < ambient_temp:
                room.current_temp = ambient_temp

    def _calculate_cost(self, room):
        cost_per_min = Config.FEE_RATE.get(room.fan_speed, 1.0)
        cost_per_sec = cost_per_min / 60.0
        
        room.fee += cost_per_sec
        room.total_fee += cost_per_sec

    def _check_target_reached(self, room):
        if room.status == 'SERVING':
            if room.mode == 'COOL' and room.current_temp <= room.target_temp:
                room.status = 'IDLE'
                # We need to tell scheduler to stop serving this room
                # But we are in simulation loop. 
                # Calling scheduler.stop_service(room.room_id) is safe?
                # Yes, scheduler uses locks or is single threaded logic (mostly).
                # But scheduler modifies DB too.
                # Let's just call it.
                self.scheduler.stop_service(room.room_id)
                
            elif room.mode == 'HEAT' and room.current_temp >= room.target_temp:
                room.status = 'IDLE'
                self.scheduler.stop_service(room.room_id)
        
        elif room.status == 'IDLE':
            if room.mode == 'COOL' and room.current_temp >= (room.target_temp + 1.0):
                room.status = 'WAITING'
                self.scheduler.request_service(room.room_id)
            elif room.mode == 'HEAT' and room.current_temp <= (room.target_temp - 1.0):
                room.status = 'WAITING'
                self.scheduler.request_service(room.room_id)
