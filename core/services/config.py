class Config:
    # System Configuration
    DEFAULT_TARGET_TEMP = 25.0
    DEFAULT_FAN_SPEED = 'MID'
    # Default initial temp is ambient temp
    DEFAULT_INITIAL_TEMP = 20.0

    # Temperature Limits
    MIN_TEMP_COOL = 18.0
    MAX_TEMP_COOL = 25.0
    MIN_TEMP_HEAT = 25.0
    MAX_TEMP_HEAT = 30.0
    
    # Fee Rates (Cost per minute)
    # Rate: 1 Yuan / 1 Degree
    # High: 1 deg/min -> 1.0 Yuan/min
    # Mid: 0.5 deg/min -> 0.5 Yuan/min
    # Low: 1/3 deg/min -> 0.333 Yuan/min
    FEE_RATE = {
        'HIGH': 1.0,
        'MID': 0.5,
        'LOW': 1.0 / 3.0
    }
    
    # Temperature Change Rates (Degrees per minute)
    # High: 1 min / 1 deg -> 1.0 deg/min
    # Mid: 2 min / 1 deg -> 0.5 deg/min
    # Low: 3 min / 1 deg -> 0.333 deg/min
    TEMP_CHANGE_RATE = {
        'HIGH': 1.0,
        'MID': 0.5,
        'LOW': 1.0 / 3.0
    }
    
    # Scheduler Configuration
    TIME_SLICE = 120  # Time slice duration in seconds (2 minutes)
    SCHEDULER_TICK = 1 # Scheduler loop interval
    MAX_SERVING_ROOMS = 3

    # Ambient Temperature
    AMBIENT_TEMP = 20.0
    
    # Fan Speed Priority (Higher is better)
    SPEED_PRIORITY = {
        'HIGH': 3,
        'MID': 2,
        'LOW': 1
    }
