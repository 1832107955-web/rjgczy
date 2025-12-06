import time
import threading
from core.models import Room
from core.logic.config import Config  # Deprecated path; kept for compatibility

class Scheduler:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(Scheduler, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        # 服务队列 (存储 room_id)
        self.service_queue = []
        # 等待队列 (存储 room_id)
        self.waiting_queue = []
        # 记录调度时的优先级
        self.room_priorities = {}
        
        self.running = False
        self.thread = threading.Thread(target=self._run_loop, daemon=True)

    def start(self):
        if not self.running:
            self.running = True
            self.thread.start()
            print("[Scheduler] Started.")

    def stop(self):
        self.running = False
        print("[Scheduler] Stopped.")

    def _run_loop(self):
        while self.running:
            time.sleep(1.0) # 1 second tick
            try:
                self.tick(1.0)
            except Exception as e:
                print(f"[Scheduler] Error in loop: {e}")

    def request_service(self, room_id):
        try:
            room = Room.objects.get(room_id=room_id)
        except Room.DoesNotExist:
            return

        current_prio = Config.SPEED_PRIORITY.get(room.fan_speed, 2)
        
        is_serving = room_id in self.service_queue
        is_waiting = room_id in self.waiting_queue
        
        if is_serving or is_waiting:
            last_prio = self.room_priorities.get(room_id, -1)
            if current_prio == last_prio:
                return
            else:
                if is_serving:
                    self.service_queue.remove(room_id)
                if is_waiting:
                    self.waiting_queue.remove(room_id)
        
        self.room_priorities[room_id] = current_prio
        self._schedule_new_request(room_id)

    def stop_service(self, room_id):
        try:
            room = Room.objects.get(room_id=room_id)
            room.status = 'IDLE'
            room.service_time = 0
            room.wait_time = 0
            room.save()
        except Room.DoesNotExist:
            pass
        
        if room_id in self.room_priorities:
            del self.room_priorities[room_id]
        
        removed = False
        if room_id in self.service_queue:
            self.service_queue.remove(room_id)
            removed = True
            
        if room_id in self.waiting_queue:
            self.waiting_queue.remove(room_id)
            
        if removed:
            self._promote_from_waiting()

    def tick(self, dt):
        # Update service time
        for rid in self.service_queue:
            try:
                r = Room.objects.get(room_id=rid)
                r.service_time += dt
                r.status = 'SERVING'
                r.save()
            except Room.DoesNotExist:
                pass

        # Update wait time
        for rid in list(self.waiting_queue): 
            try:
                r = Room.objects.get(room_id=rid)
                r.wait_time += dt
                r.status = 'WAITING'
                
                if r.wait_timeout > 0:
                    r.wait_timeout -= dt
                    if r.wait_timeout <= 0:
                        self._handle_timeslice_timeout(rid)
                r.save()
            except Room.DoesNotExist:
                pass

    def _schedule_new_request(self, new_room_id):
        try:
            new_room = Room.objects.get(room_id=new_room_id)
        except Room.DoesNotExist:
            return
            
        new_prio = Config.SPEED_PRIORITY.get(new_room.fan_speed, 2)

        if len(self.service_queue) < Config.MAX_SERVING_ROOMS:
            self._add_to_service(new_room_id)
            return

        # Find min priority in service queue
        # We need to fetch rooms to check their current speed/priority
        service_rooms = Room.objects.filter(room_id__in=self.service_queue)
        if not service_rooms:
             # Should not happen if queue not empty, but safety check
             self._add_to_service(new_room_id)
             return

        min_prio = min([Config.SPEED_PRIORITY.get(r.fan_speed, 2) for r in service_rooms])
        
        if new_prio > min_prio:
            # Find candidates with lower priority
            candidates = [r for r in service_rooms if Config.SPEED_PRIORITY.get(r.fan_speed, 2) < new_prio]
            
            # Sort by priority (asc), then service_time (desc)
            # We need to use the values from DB objects
            victim = sorted(
                candidates,
                key=lambda r: (
                    Config.SPEED_PRIORITY.get(r.fan_speed, 2),
                    -r.service_time
                )
            )[0]
            
            self._preempt(victim.room_id, new_room_id)
            
        elif new_prio == min_prio:
            self._add_to_waiting(new_room_id, timeout=Config.TIME_SLICE)
            
        else:
            self._add_to_waiting(new_room_id, timeout=Config.TIME_SLICE)

    def _handle_timeslice_timeout(self, waiting_room_id):
        try:
            waiting_room = Room.objects.get(room_id=waiting_room_id)
        except Room.DoesNotExist:
            return
            
        wait_prio = Config.SPEED_PRIORITY.get(waiting_room.fan_speed, 2)
        
        service_rooms = Room.objects.filter(room_id__in=self.service_queue)
        candidates = []
        for r in service_rooms:
            p = Config.SPEED_PRIORITY.get(r.fan_speed, 2)
            if p == wait_prio:
                candidates.append(r)
        
        if candidates:
            victim = max(candidates, key=lambda r: r.service_time)
            self._preempt(victim.room_id, waiting_room_id)

    def _add_to_service(self, room_id):
        if room_id not in self.service_queue:
            self.service_queue.append(room_id)
        if room_id in self.waiting_queue:
            self.waiting_queue.remove(room_id)
        
        try:
            room = Room.objects.get(room_id=room_id)
            room.status = 'SERVING'
            room.service_time = 0
            room.save()
        except Room.DoesNotExist:
            pass

    def _add_to_waiting(self, room_id, timeout=None):
        if room_id not in self.waiting_queue:
            self.waiting_queue.append(room_id)
        
        try:
            room = Room.objects.get(room_id=room_id)
            room.status = 'WAITING'
            room.wait_time = 0
            room.wait_timeout = timeout if timeout else 0
            room.save()
        except Room.DoesNotExist:
            pass

    def _preempt(self, victim_id, winner_id):
        self.service_queue.remove(victim_id)
        self._add_to_waiting(victim_id, timeout=Config.TIME_SLICE)
        self._add_to_service(winner_id)

    def _promote_from_waiting(self):
        if not self.waiting_queue:
            return

        waiting_rooms = Room.objects.filter(room_id__in=self.waiting_queue)
        if not waiting_rooms:
            return

        best_candidate = sorted(
            waiting_rooms,
            key=lambda r: (
                -Config.SPEED_PRIORITY.get(r.fan_speed, 2),
                -r.wait_time
            )
        )[0]
        
        self._add_to_service(best_candidate.room_id)
