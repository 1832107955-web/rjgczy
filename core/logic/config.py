class Config:
    # System Configuration
    DEFAULT_TARGET_TEMP = 25.0
    DEFAULT_FAN_SPEED = 'MID'
    DEFAULT_INITIAL_TEMP = 28.0

    # Temperature Limits
    MIN_TEMP_COOL = 18.0
    MAX_TEMP_COOL = 25.0
    MIN_TEMP_HEAT = 25.0
    MAX_TEMP_HEAT = 30.0
    
    # Fee Rates (Cost per minute)
    FEE_RATE = {
        'HIGH': 1.0,
        'MID': 0.5,
        'LOW': 1.0 / 3.0
    }
    
    # Temperature Change Rates (Degrees per minute)
    TEMP_CHANGE_RATE = {
        'HIGH': 0.6,
        'MID': 0.5,
        'LOW': 0.4
    }
    
    # Scheduler Configuration
    TIME_SLICE = 10  # 10 seconds
    MAX_SERVING_ROOMS = 3

    # Ambient Temperature
    AMBIENT_TEMP = 28.0
    
    # Fan Speed Priority (Higher is better)
    SPEED_PRIORITY = {
        'HIGH': 3,
        'MID': 2,
        'LOW': 1
    }
