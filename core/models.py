from django.db import models
from django.utils import timezone

class Room(models.Model):
    ROOM_TYPES = (
        ('STANDARD', 'Standard Room'),
        ('KING', 'King Size Room'),
    )

    room_id = models.CharField(max_length=10, primary_key=True)
    # Login credentials
    username = models.CharField(max_length=50, unique=True, null=True, blank=True)
    password = models.CharField(max_length=50, default='88888888')

    room_type = models.CharField(max_length=10, choices=ROOM_TYPES, default='STANDARD')
    daily_rate = models.FloatField(default=300.0)
    
    occupancy_status = models.CharField(max_length=10, default='EMPTY') # EMPTY, OCCUPIED
    guest_id = models.CharField(max_length=50, null=True, blank=True)
    check_in_time = models.DateTimeField(null=True, blank=True)
    
    # AC State
    is_on = models.BooleanField(default=False)
    current_temp = models.FloatField(default=28.0)
    target_temp = models.FloatField(default=25.0)
    fan_speed = models.CharField(max_length=10, default='MID') # LOW, MID, HIGH
    mode = models.CharField(max_length=10, default='COOL') # COOL, HEAT
    fee = models.FloatField(default=0.0)
    total_fee = models.FloatField(default=0.0)
    status = models.CharField(max_length=10, default='IDLE') # IDLE, SERVING, WAITING
    
    # Scheduler specific
    service_time = models.FloatField(default=0.0)
    wait_time = models.FloatField(default=0.0)
    wait_timeout = models.FloatField(default=0.0)

    def __str__(self):
        return f"Room {self.room_id}"

class Bill(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    guest_id = models.CharField(max_length=50)
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(auto_now_add=True)
    ac_fee = models.FloatField(default=0.0)
    accommodation_fee = models.FloatField(default=0.0)
    total_amount = models.FloatField(default=0.0)

class ACSession(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, null=True, blank=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    mode = models.CharField(max_length=10, default='COOL')
    fan_speed = models.CharField(max_length=10, default='MID')
    start_temp = models.FloatField(default=28.0)
    target_temp = models.FloatField(default=25.0)
    fee = models.FloatField(default=0.0)
    initial_fee = models.FloatField(default=0.0)

    def duration(self):
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0

