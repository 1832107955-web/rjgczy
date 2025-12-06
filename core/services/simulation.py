import time
import threading
from core.models import Room
from core.services.config import Config
from core.services.scheduler import Scheduler

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
            time.sleep(1.0)
            try:
                self._update_rooms()
            except Exception as e:
                print(f"[Simulation] Error: {e}")

    def _update_rooms(self):
        rooms = Room.objects.all()
        for room in rooms:
            update_fields = ['current_temp']

            # 1. Calculate Natural Change Vector (Recovery to Ambient)
            natural_change = 0.0
            ambient_temp = Config.AMBIENT_TEMP
            # Requirement: 0.5 degrees per minute recovery
            recovery_rate = 0.5 / 60.0
            
            if room.current_temp < ambient_temp:
                natural_change = recovery_rate
            elif room.current_temp > ambient_temp:
                natural_change = -recovery_rate
            
            # 2. Calculate AC Change Vector
            ac_change = 0.0
            if room.is_on and room.status == 'SERVING':
                rate = Config.TEMP_CHANGE_RATE.get(room.fan_speed, 0.5) / 60.0
                if room.mode == 'COOL':
                    ac_change = -rate
                else: # HEAT
                    ac_change = rate
                
                self._calculate_cost(room)
                update_fields.extend(['fee', 'total_fee'])

            # 3. Apply Changes
            # If AC is SERVING, we apply ONLY AC change (Ignore natural recovery)
            if room.is_on and room.status == 'SERVING':
                room.current_temp += ac_change
            else:
                # Only natural recovery, clamp to ambient to prevent overshoot
                if natural_change != 0:
                    new_temp = room.current_temp + natural_change
                    if natural_change > 0 and new_temp > ambient_temp:
                        new_temp = ambient_temp
                    elif natural_change < 0 and new_temp < ambient_temp:
                        new_temp = ambient_temp
                    room.current_temp = new_temp

            if self._check_state_transitions(room):
                update_fields.append('status')
            
            room.save(update_fields=update_fields)

    def _calculate_cost(self, room):
        cost_per_min = Config.FEE_RATE.get(room.fan_speed, 1.0)
        cost_per_sec = cost_per_min / 60.0
        
        room.fee += cost_per_sec
        room.total_fee += cost_per_sec

    def _check_state_transitions(self, room):
        if not room.is_on:
            if room.status != 'IDLE':
                room.status = 'IDLE'
                return True
            return False

        # Requirement: Re-request service when temp deviates by 1.0 degree
        THRESHOLD = 1.0 # Hysteresis threshold

        # Determine if there is demand for AC
        demand = False
        if room.mode == 'COOL':
            if room.status == 'SERVING':
                # Keep running until target reached
                if room.current_temp > room.target_temp:
                    demand = True
            else:
                # Start running if threshold exceeded (Resume condition)
                # Or if just turned on and temp is high enough
                if room.current_temp >= room.target_temp + THRESHOLD:
                    demand = True
        else: # HEAT
            if room.status == 'SERVING':
                # Keep running until target reached
                if room.current_temp < room.target_temp:
                    demand = True
            else:
                # Start running if threshold exceeded (Resume condition)
                if room.current_temp <= room.target_temp - THRESHOLD:
                    demand = True
        
        # Apply State Transitions
        if demand:
            if room.status == 'IDLE':
                # room.status = 'WAITING' # Let scheduler handle this
                self.scheduler.request_service(room.room_id)
                return False
        else:
            # No demand (Target reached or within hysteresis buffer)
            if room.status == 'SERVING' or room.status == 'WAITING':
                room.status = 'IDLE'
                self.scheduler.stop_service(room.room_id)
                return True
        
        return False
