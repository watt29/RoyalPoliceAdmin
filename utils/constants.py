from enum import IntEnum, auto

class BotState(IntEnum):
    # Contact Flow
    CONTACT_NAME = auto()
    CONTACT_RANK = auto()
    CONTACT_PHONE = auto()
    CONTACT_NOTE = auto()
    
    # Order Flow
    ORDER_DETAIL = auto()
    ORDER_COMMANDER = auto()
    ORDER_DEADLINE = auto()
    
    # AI Flow
    AI_QUESTION = auto()
    
    # Reminder Flow
    REMINDER_TOPIC = auto()
    REMINDER_CONTENT = auto()
    REMINDER_TIME = auto()
    
    # Vehicle Flow
    VEHICLE_PLATE = auto()
    VEHICLE_BRAND = auto()
    VEHICLE_SHIELD = auto()
    VEHICLE_AGENCY = auto()
    VEHICLE_STATUS = auto()
