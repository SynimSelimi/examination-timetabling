def room2supervisors(enum):
    if not enum: return None
    return {
        "Small": 1,
        "Medium": 2,
        "Large": 3
    }[enum]

def exams(enum):
    if not enum: return None
    return {
        "Written": 1,
        "Oral": 2,
        "WrittenAndOral": 3
    }[enum]