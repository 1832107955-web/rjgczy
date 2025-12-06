from django.contrib import admin
from .models import Room, Bill

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("room_id", "occupancy_status", "is_on", "current_temp", "target_temp", "fan_speed", "mode", "status", "fee")
    list_filter = ("occupancy_status", "is_on", "fan_speed", "mode", "status")
    search_fields = ("room_id", "guest_id")

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ("room", "guest_id", "check_in_time", "check_out_time", "ac_fee", "accommodation_fee", "total_amount")
    list_filter = ("check_in_time", "check_out_time")
    search_fields = ("guest_id", "room__room_id")
