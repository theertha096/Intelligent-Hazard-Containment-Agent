from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

Position = Tuple[int, int]


@dataclass
class Valve:
    id: str
    position: Position
    effectiveness: float
    risk: float
    status: str = "OPEN"
    failed: bool = False


@dataclass
class Door:
    id: str
    position: Position
    effectiveness: float
    risk: float
    status: str = "OPEN"


@dataclass
class CriticalFacility:
    id: str
    position: Position
    priority: int
    status: str = "PROTECTED"


@dataclass
class RobotState:
    position: Position
    battery: float = 100.0
    exposure: float = 0.0
    max_exposure: float = 100.0
    resources: int = 3
    status: str = "ACTIVE"
    current_target: Optional[str] = None
    current_target_position: Optional[Position] = None
    current_path: List[Position] = field(default_factory=list)
    replan_count: int = 0
    successful_replans: int = 0
    steps: int = 0


@dataclass
class ActionCandidate:
    action_type: str
    target_id: str
    position: Position
    score: float = 0.0
    feasible: bool = True
    reason: str = ""
    breakdown: Dict[str, float] = field(default_factory=dict)


@dataclass
class PlantState:
    tick: int
    scenario: str
    last_action: str = "MONITOR"
    last_reason: str = "System initialized"
    containment_time: Optional[int] = None
    containment_completed: bool = False
    protected_facilities: int = 0


class StateSpaceModel:
    """Simple state-space representation used by the simulation.

    A state contains the robot, hazard map, device states and critical-facility
    status. Each MOVE, CLOSE_VALVE, CLOSE_DOOR or RETREAT changes that state.
    """

    def __init__(self):
        self.current = {}
        self.last_action = "MONITOR"
        self.last_transition = "Initial state"

    def snapshot(self, env, hazard, robot):
        return {
            "robot_position": robot.state.position,
            "battery": robot.state.battery,
            "exposure": robot.state.exposure,
            "resources": robot.state.resources,
            "hazard_map": tuple(tuple(row) for row in hazard.grid),
            "valves": tuple(sorted((k, v.status) for k, v in env.valves.items())),
            "doors": tuple(sorted((k, v.status) for k, v in env.doors.items())),
            "critical_facilities": tuple(sorted((k, v.status) for k, v in env.critical_facilities.items())),
        }

    def capture(self, env, hazard, robot, action="MONITOR", reason="Initial state"):
        self.current = self.snapshot(env, hazard, robot)
        self.last_action = action
        self.last_transition = reason
        return self.current

    def transition(self, env, hazard, robot, action, reason):
        before = self.current
        after = self.snapshot(env, hazard, robot)
        self.current = after
        self.last_action = action
        self.last_transition = reason
        return before, after
