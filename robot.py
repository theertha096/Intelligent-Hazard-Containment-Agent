from state import RobotState


class Robot:
    def __init__(self, start_position):
        self.state = RobotState(position=start_position)

    def move_to(self, position, env, hazard_level):
        r, c = position
        if self.state.battery <= 0 or not env.is_walkable(r, c):
            return False
        self.state.position = position
        self.state.battery = max(0, self.state.battery - 1)
        exposure_gain = [0, 1, 3, 7, 12][min(hazard_level, 4)]
        self.state.exposure += exposure_gain
        self.state.steps += 1
        if self.state.battery <= 0:
            self.state.status = "BATTERY_DEPLETED"
        if self.state.exposure >= self.state.max_exposure:
            self.state.status = "RETREAT_REQUIRED"
        return True

    def use_resource(self):
        if self.state.resources <= 0:
            return False
        self.state.resources -= 1
        return True
