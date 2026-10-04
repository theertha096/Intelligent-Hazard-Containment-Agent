import heapq

from hazard import CRITICAL


class AStarPlanner:
    """A* route planner with an optional hazard penalty."""

    def __init__(self):
        # These are design choices for the simulation, not real chemical values.
        self.hazard_cost = [1, 3, 6, 15, float("inf")]

    @staticmethod
    def heuristic(a, b):
        """Manhattan distance for four-direction movement."""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def explain_neighbors(self, current, goal, env, hazard_grid, hazard_aware=True, current_g=0):
        """Return a small, readable A* example for the dashboard.

        ``current_g`` is the cumulative cost from the current A* planning
        start to ``current``. The dashboard normally calls this with 0 because
        the robot's current position is the start node for the displayed
        planning step.
        """
        r, c = current
        rows = []
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if not env.is_walkable(nr, nc):
                continue

            hazard = hazard_grid[nr][nc]
            if hazard >= CRITICAL:
                continue

            step_cost = 1 + self.hazard_cost[hazard] if hazard_aware else 1
            h = self.heuristic((nr, nc), goal)
            g = current_g + step_cost
            rows.append({
                "Cell": (nr, nc),
                "Hazard": hazard,
                "g(n)": g,
                "h(n)": h,
                "f(n)": g + h,
            })

        return sorted(rows, key=lambda x: (x["f(n)"], x["h(n)"]))

    def plan(self, start, goal, env, hazard_grid, hazard_aware=True):
        if not env.is_walkable(*goal) or hazard_grid[goal[0]][goal[1]] >= CRITICAL:
            return None

        open_set = [(self.heuristic(start, goal), 0, start)]
        came_from = {start: None}
        g_score = {start: 0}
        visited = set()

        while open_set:
            _, current_g, current = heapq.heappop(open_set)
            if current in visited:
                continue
            visited.add(current)

            if current == goal:
                path = []
                while current is not None:
                    path.append(current)
                    current = came_from[current]
                return list(reversed(path))

            r, c = current
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if not env.is_walkable(nr, nc):
                    continue

                hazard = hazard_grid[nr][nc]
                if hazard >= CRITICAL:
                    continue

                step_cost = 1 + self.hazard_cost[hazard] if hazard_aware else 1
                new_g = current_g + step_cost

                if new_g < g_score.get((nr, nc), float("inf")):
                    g_score[(nr, nc)] = new_g
                    came_from[(nr, nc)] = current
                    h = self.heuristic((nr, nc), goal)
                    heapq.heappush(open_set, (new_g + h, new_g, (nr, nc)))

        return None
