import threading
import time
from core.models import Room
from core.services.config import Config

class Scheduler:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(Scheduler, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.running = False
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        # Queues store room_ids
        self.waiting_queue = [] 
        self.serving_queue = [] 
        
        # Sync from DB to handle restarts
        self._sync_queues_from_db()

    def _sync_queues_from_db(self):
        try:
            # Restore queues from database state
            serving_rooms = Room.objects.filter(status='SERVING')
            for room in serving_rooms:
                if room.room_id not in self.serving_queue:
                    self.serving_queue.append(room.room_id)
                    
            waiting_rooms = Room.objects.filter(status='WAITING')
            for room in waiting_rooms:
                if room.room_id not in self.waiting_queue:
                    self.waiting_queue.append(room.room_id)
            
            print(f"[Scheduler] Restored state: Serving={self.serving_queue}, Waiting={self.waiting_queue}")
            
            # Try to fill slots if available
            while len(self.serving_queue) < Config.MAX_SERVING_ROOMS and self.waiting_queue:
                self._fill_free_slot()
                
        except Exception as e:
            print(f"[Scheduler] Error syncing from DB: {e}")

    def start(self):
        if not self.running:
            self.running = True
            self.thread.start()
            print("[Scheduler] Started.")

    def stop(self):
        self.running = False
        print("[Scheduler] Stopped.")

    def request_service(self, room_id):
        """
        Called when a room requests service (e.g. turned on, or temp deviation).
        Implements the dispatch strategy.
        """
        # Optimization: If already waiting and priority hasn't changed, don't reset queue position
        if room_id in self.waiting_queue:
            # We assume that if request_service is called, the room state (fan_speed) might have changed.
            # But if it's just a periodic check, we shouldn't reset.
            # Since we don't track "queued priority", we'll just remove and re-evaluate.
            # This is safer for correctness but resets wait time.
            # To optimize, we could check if the new priority is same as old, but we don't have old.
            # For now, we keep the behavior of re-evaluating to ensure priority upgrades are respected.
            self.waiting_queue.remove(room_id)
            print(f"[Scheduler] Re-evaluating waiting request: {room_id}")

        # If already serving, we generally keep it serving.
        if room_id in self.serving_queue:
            return

        print(f"[Scheduler] Request: {room_id}")
        
        # 1. If slots available, assign immediately
        if len(self.serving_queue) < Config.MAX_SERVING_ROOMS:
            self._add_to_serving(room_id)
            return

        # 2. Slots full, run scheduling logic
        self._handle_full_capacity_request(room_id)

    def stop_service(self, room_id):
        """
        Called when a room stops service (e.g. turned off, or target reached).
        """
        print(f"[Scheduler] Stop: {room_id}")
        if room_id in self.serving_queue:
            self.serving_queue.remove(room_id)
            # Slot freed, fill it
            self._fill_free_slot()
        elif room_id in self.waiting_queue:
            self.waiting_queue.remove(room_id)

    def _run_loop(self):
        while self.running:
            time.sleep(Config.SCHEDULER_TICK)
            self._update_timers()
            self._check_time_slice()

    def _update_timers(self):
        # Update service_time for serving rooms
        for rid in self.serving_queue:
            self._update_room_timer(rid, service_delta=Config.SCHEDULER_TICK)
        
        # Update wait_time (countdown) for waiting rooms
        for rid in self.waiting_queue:
            self._update_room_timer(rid, wait_delta=-Config.SCHEDULER_TICK)

    def _check_time_slice(self):
        # 2.2.2: Check if any waiting room has timed out (wait_timeout <= 0)
        # Only applies if we are in Time Slice mode (implied by having a timeout set)
        
        # We need to iterate a copy because we might modify the queue
        for waiter_id in list(self.waiting_queue):
            room = self._get_room(waiter_id)
            if not room: continue
            
            if room.wait_timeout <= 0:
                # Time slice expired. 
                # Find serving room with SAME speed (Time Slice Strategy)
                # And preempt the one with longest service time.
                
                victim_id = self._find_longest_serving_victim(room.fan_speed)
                if victim_id:
                    print(f"[Scheduler] Time Slice: Swapping {victim_id} (Longest Serve) with {waiter_id} (Timeout)")
                    self._preempt(victim_id, waiter_id, victim_timeout=Config.TIME_SLICE)

    def _handle_full_capacity_request(self, request_id):
        req_room = self._get_room(request_id)
        if not req_room: return

        req_prio = Config.SPEED_PRIORITY.get(req_room.fan_speed, 0)
        
        # Analyze serving rooms
        serving_rooms = [self._get_room(rid) for rid in self.serving_queue]
        serving_rooms = [r for r in serving_rooms if r] # Filter None

        # 2.1 Check for Lower Priority (Higher Speed > Lower Speed)
        # Find rooms with lower priority
        lower_prio_rooms = [r for r in serving_rooms if Config.SPEED_PRIORITY.get(r.fan_speed, 0) < req_prio]
        
        if lower_prio_rooms:
            # 2.1.1 / 2.1.2 / 2.1.3
            # We need to pick ONE victim.
            # Rule: Lowest speed first. If speeds equal, longest service time.
            
            # Sort by Priority (Asc), then Service Time (Desc)
            lower_prio_rooms.sort(key=lambda r: (
                Config.SPEED_PRIORITY.get(r.fan_speed, 0), 
                -r.service_time
            ))
            
            victim = lower_prio_rooms[0]
            print(f"[Scheduler] Priority Preemption: {request_id} (High) replaces {victim.room_id} (Low)")
            # Victim gets infinite timeout because it was kicked by higher priority
            self._preempt(victim.room_id, request_id, victim_timeout=999999)
            return

        # 2.2 Check for Equal Priority
        # If we are here, no lower priority rooms exist.
        # Check if there are equal priority rooms.
        equal_prio_rooms = [r for r in serving_rooms if Config.SPEED_PRIORITY.get(r.fan_speed, 0) == req_prio]
        
        if equal_prio_rooms:
            # 2.2.1 Time Slice Strategy
            # Add to wait queue with timeout
            print(f"[Scheduler] Time Slice Wait: {request_id} added to wait queue")
            self._add_to_waiting(request_id, timeout=Config.TIME_SLICE)
            return

        # 2.3 Lower Priority (Request < Serving)
        # Must wait.
        print(f"[Scheduler] Low Priority Wait: {request_id} added to wait queue (No Timeout)")
        self._add_to_waiting(request_id, timeout=999999) # Effectively infinite

    def _fill_free_slot(self):
        # 2.2.3: Slot freed. Pick best waiter.
        if not self.waiting_queue:
            return

        # Criteria:
        # 1. Highest Priority (Fan Speed)
        # 2. Smallest Wait Duration (wait_timeout). 
        #    (Smallest timeout means closest to expiration, i.e. waited longest in slice logic)
        
        candidates = []
        for rid in self.waiting_queue:
            r = self._get_room(rid)
            if r: candidates.append(r)
            
        if not candidates: return

        # Sort: Priority (Desc), Wait Timeout (Asc)
        candidates.sort(key=lambda r: (
            -Config.SPEED_PRIORITY.get(r.fan_speed, 0),
            r.wait_timeout
        ))
        
        best_waiter = candidates[0]
        print(f"[Scheduler] Slot Free: Assigning to {best_waiter.room_id}")
        
        self.waiting_queue.remove(best_waiter.room_id)
        self._add_to_serving(best_waiter.room_id)

    def _preempt(self, victim_id, new_id, victim_timeout):
        # Remove victim
        if victim_id in self.serving_queue:
            self.serving_queue.remove(victim_id)
        self._add_to_waiting(victim_id, timeout=victim_timeout) 
        
        # Add new
        if new_id in self.waiting_queue:
            self.waiting_queue.remove(new_id)
        self._add_to_serving(new_id)

    def _add_to_serving(self, room_id):
        self.serving_queue.append(room_id)
        self._update_room_status(room_id, 'SERVING', service_time=0)

    def _add_to_waiting(self, room_id, timeout):
        self.waiting_queue.append(room_id)
        self._update_room_status(room_id, 'WAITING', wait_timeout=timeout)

    def _find_longest_serving_victim(self, target_speed):
        # Find serving room with same speed and longest service time
        candidates = []
        target_prio = Config.SPEED_PRIORITY.get(target_speed, 0)
        
        for rid in self.serving_queue:
            r = self._get_room(rid)
            if r and Config.SPEED_PRIORITY.get(r.fan_speed, 0) == target_prio:
                candidates.append(r)
        
        if not candidates: return None
        
        # Sort by Service Time Desc
        candidates.sort(key=lambda r: -r.service_time)
        return candidates[0].room_id

    def _get_room(self, room_id):
        try:
            return Room.objects.get(room_id=room_id)
        except Room.DoesNotExist:
            return None

    def _update_room_status(self, room_id, status, service_time=None, wait_timeout=None):
        try:
            room = Room.objects.get(room_id=room_id)
            room.status = status
            update_fields = ['status']
            if service_time is not None:
                room.service_time = service_time
                update_fields.append('service_time')
            if wait_timeout is not None:
                room.wait_timeout = wait_timeout
                update_fields.append('wait_timeout')
            room.save(update_fields=update_fields)
        except Room.DoesNotExist:
            pass

    def _update_room_timer(self, room_id, service_delta=0, wait_delta=0):
        try:
            room = Room.objects.get(room_id=room_id)
            update_fields = []
            if service_delta:
                room.service_time += service_delta
                update_fields.append('service_time')
            if wait_delta:
                room.wait_timeout += wait_delta
                update_fields.append('wait_timeout')
            
            if update_fields:
                room.save(update_fields=update_fields)
        except Room.DoesNotExist:
            pass
