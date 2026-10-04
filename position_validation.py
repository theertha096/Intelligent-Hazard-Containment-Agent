def restricted_position_reason(env, hazard, position, role):
    """Explain why a user-selected robot/safe-zone position is invalid."""
    r, c = position
    if not env.is_valid(r, c):
        return f"{role} {position} is outside the 20 × 20 plant grid. Please choose another position."
    if env.grid[r][c] == env.WALL:
        return f"{role} {position} is a WALL and cannot be entered. Please choose another position."

    for name, valve in env.valves.items():
        if valve.position == position:
            return f"{role} {position} is the restricted device position of {name}. Please choose another position."

    for name, door in env.doors.items():
        if door.position == position:
            return f"{role} {position} is the door position of {name}. Please choose another position."

    for name, facility in env.critical_facilities.items():
        if facility.position == position:
            return f"{role} {position} is the critical-facility position of {name}. Please choose another position."

    if hazard.grid[r][c] >= 4:
        return f"{role} {position} is inside a CRITICAL hazard cell. Please choose another position."

    return None
