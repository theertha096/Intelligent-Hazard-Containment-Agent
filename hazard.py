from typing import List, Tuple

SAFE, LOW, MEDIUM, HIGH, CRITICAL = range(5)


class HazardModel:
    def __init__(self, rows=20, cols=20):
        self.rows = rows
        self.cols = cols
        self.grid = [[SAFE for _ in range(cols)] for _ in range(rows)]
        self.sources: List[Tuple[int, int]] = []

    def reset(self):
        self.grid = [[SAFE for _ in range(self.cols)] for _ in range(self.rows)]
        self.sources = []

    def add_source(self, position, level=HIGH):
        self.sources.append(position)
        r, c = position
        self.grid[r][c] = level

    def update(self, env, tick):
        # Hazard spreads every second tick. Closed doors stop propagation.
        if tick % 2 != 0:
            return
        new_grid = [row[:] for row in self.grid]
        for r in range(self.rows):
            for c in range(self.cols):
                level = self.grid[r][c]
                if level <= SAFE:
                    continue
                for nr, nc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                    if not env.is_valid(nr, nc) or not env.is_walkable(nr, nc):
                        continue
                    blocked = any(d.position == (nr,nc) and d.status == "CLOSED" for d in env.doors.values())
                    if blocked:
                        continue
                    new_level = max(LOW, level - 1)
                    new_grid[nr][nc] = max(new_grid[nr][nc], new_level)
        self.grid = new_grid

    def apply_containment(self, position, effectiveness):
        r, c = position
        cells = [(r,c),(r-1,c),(r+1,c),(r,c-1),(r,c+1)]
        for rr, cc in cells:
            if 0 <= rr < self.rows and 0 <= cc < self.cols:
                old = self.grid[rr][cc]
                self.grid[rr][cc] = max(SAFE, int(round(old * (1-effectiveness))))

    def affected_area(self):
        return sum(cell > SAFE for row in self.grid for cell in row)

    def maximum_level(self):
        return max(max(row) for row in self.grid)
