class IntegratedPlanner:
    def __init__(self, astar):
        self.astar = astar

    def validate_path(self, path, env, hazard_grid):
        if not path:
            return False
        for position in path:
            r,c=position
            if not env.is_walkable(r,c) or hazard_grid[r][c] >= 4:
                return False
        return True

    def make_plan(self, start, goal, env, hazard_grid, hazard_aware=True):
        return self.astar.plan(start, goal, env, hazard_grid, hazard_aware)
