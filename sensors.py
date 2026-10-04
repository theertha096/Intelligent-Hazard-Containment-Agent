from hazard import HazardModel
from environment import Environment
from robot import Robot


class SensorSystem:
    def perceive(self, env: Environment, hazard: HazardModel, robot: Robot):
        return {
            "robot_pos": robot.state.position,
            "robot_battery": robot.state.battery,
            "robot_exposure": robot.state.exposure,
            "robot_resources": robot.state.resources,
            "hazard_grid": [row[:] for row in hazard.grid],
            "valves": {k: {"position": v.position, "status": v.status, "effectiveness": v.effectiveness, "risk": v.risk, "failed": v.failed} for k,v in env.valves.items()},
            "doors": {k: {"position": d.position, "status": d.status, "effectiveness": d.effectiveness, "risk": d.risk} for k,d in env.doors.items()},
            "critical_facilities": {k: {"position": f.position, "priority": f.priority, "status": f.status} for k,f in env.critical_facilities.items()},
        }
