from typing import Dict, Tuple
from state import Valve, Door, CriticalFacility


class Environment:
    FREE = 0
    WALL = 1
    VALVE = 2
    DOOR = 3
    SAFE = 4
    CRITICAL = 5

    def __init__(self, rows=20, cols=20):
        self.rows = rows
        self.cols = cols
        self.grid = [[self.FREE for _ in range(cols)] for _ in range(rows)]
        self.valves: Dict[str, Valve] = {}
        self.doors: Dict[str, Door] = {}
        self.critical_facilities: Dict[str, CriticalFacility] = {}
        self.safe_zone: Tuple[int, int] = (18, 18)
        self._build_walls()

    def _build_walls(self):
        for r in range(self.rows):
            self.grid[r][0] = self.WALL
            self.grid[r][self.cols - 1] = self.WALL
        for c in range(self.cols):
            self.grid[0][c] = self.WALL
            self.grid[self.rows - 1][c] = self.WALL

        for c in range(2, 10):
            self.grid[6][c] = self.WALL
        for c in range(11, 18):
            self.grid[6][c] = self.WALL
        for c in range(2, 8):
            self.grid[13][c] = self.WALL
        for c in range(10, 18):
            self.grid[13][c] = self.WALL

    def set_safe_zone(self, position):
        """Move the safe-zone marker to a validated free cell."""
        old_r, old_c = self.safe_zone
        if self.grid[old_r][old_c] == self.SAFE:
            self.grid[old_r][old_c] = self.FREE
        self.safe_zone = position
        r, c = position
        self.grid[r][c] = self.SAFE

    def is_valid(self, r, c):
        return 0 <= r < self.rows and 0 <= c < self.cols

    def is_walkable(self, r, c):
        if not self.is_valid(r, c) or self.grid[r][c] == self.WALL:
            return False
        for door in self.doors.values():
            if door.position == (r, c) and door.status == "CLOSED":
                return False
        return True

    def reset_devices(self):
        for valve in self.valves.values():
            valve.status = "OPEN"
        for door in self.doors.values():
            door.status = "OPEN"

    def add_standard_devices(self):
        self.valves = {
            "V1": Valve("V1", (4, 4), 0.85, 2),
            "V2": Valve("V2", (4, 15), 0.90, 3),
            "V3": Valve("V3", (16, 10), 0.75, 2),
        }
        self.doors = {
            "D1": Door("D1", (6, 10), 0.50, 1),
            "D2": Door("D2", (13, 8), 0.60, 1),
        }
        self.critical_facilities = {
            "CONTROL_ROOM": CriticalFacility("CONTROL_ROOM", (3, 15), 3),
            "POWER_ROOM": CriticalFacility("POWER_ROOM", (16, 4), 2),
        }
        self._mark_devices()

    def _mark_devices(self):
        for valve in self.valves.values():
            r, c = valve.position
            self.grid[r][c] = self.VALVE
        for door in self.doors.values():
            r, c = door.position
            self.grid[r][c] = self.DOOR
        for facility in self.critical_facilities.values():
            r, c = facility.position
            self.grid[r][c] = self.CRITICAL
        r, c = self.safe_zone
        self.grid[r][c] = self.SAFE
