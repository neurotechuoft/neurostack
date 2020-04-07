import uuid


def generate_uuid():
    """Generates a universally unique ID"""
    # Completely random UUID; use uuid1() for a UUID based on host MAC address
    # and current time
    return str(uuid.uuid4())
