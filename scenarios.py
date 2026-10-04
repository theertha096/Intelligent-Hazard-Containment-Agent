from environment import Environment
from hazard import HazardModel, LOW, MEDIUM, HIGH, CRITICAL
from robot import Robot


SCENARIO_INFO = {
    "S1 - Nearby Leak": {
        "title": "Nearby Leak",
        "objective": "Detect a nearby high hazard and choose a containment point.",
        "concept": "Perception + rule-based reasoning + heuristic action selection",
        "situation": "A leak develops close to the robot. The agent must identify whether a nearby valve can reduce the hazard before moving to a safe area.",
        "expected": "The agent should detect the hazardous region, evaluate containment candidates and move toward a feasible valve.",
    },
    "S2 - Critical Facility Threat": {
        "title": "Critical Facility Threat",
        "objective": "Protect a high-priority plant facility from a nearby hazard.",
        "concept": "Rule-based reasoning + heuristic decision-making",
        "situation": "A high hazard develops around the control-room area. Protecting a critical facility should influence the action score.",
        "expected": "The reasoning layer should give additional importance to actions that reduce the threat near the critical facility.",
    },
    "S3 - Unsafe Shortest Route": {
        "title": "Unsafe Shortest Route",
        "objective": "Reach a target without crossing a critical hazard region.",
        "concept": "Constraint checking + hazard-aware A*",
        "situation": "A direct-looking route contains a dangerous region. The planner must trade a slightly longer route for a safer one.",
        "expected": "A* should avoid critical cells and use hazard cost when hazard-aware planning is enabled.",
    },
    "S4 - Route Becomes Blocked": {
        "title": "Route Becomes Blocked",
        "objective": "Recover when a previously planned route becomes unsafe.",
        "concept": "Dynamic replanning",
        "situation": "The robot begins with a valid route. During the simulation, a future path cell becomes highly hazardous.",
        "expected": "The agent should detect that the old plan is invalid, increment the replan count and generate a new route.",
    },
    "S5 - Failed Containment Point": {
        "title": "Failed Containment Point",
        "objective": "Reject an unavailable containment point and continue safely.",
        "concept": "Hard constraints + failure handling",
        "situation": "A valve near the hazard is marked as failed. The decision layer may consider it, but the constraint layer must reject it.",
        "expected": "The failed valve should appear as rejected rather than being used by the robot.",
    },
}


class ScenarioFactory:
    @staticmethod
    def create(scenario):
        env = Environment()
        env.add_standard_devices()
        hazard = HazardModel()

        if scenario == "S1 - Nearby Leak":
            robot = Robot((2, 2))
            hazard.add_source((5, 5), HIGH)
            hazard.grid[4][4] = HIGH
            hazard.grid[4][5] = HIGH
            hazard.grid[4][6] = HIGH
            hazard.grid[5][4] = HIGH
            hazard.grid[5][5] = CRITICAL
            hazard.grid[5][6] = HIGH
            hazard.grid[6][4] = HIGH
            hazard.grid[6][5] = HIGH
            hazard.grid[6][6] = HIGH

        elif scenario == "S2 - Critical Facility Threat":
            robot = Robot((15, 2))
            hazard.add_source((3, 14), HIGH)
            hazard.grid[2][13] = HIGH
            hazard.grid[2][14] = HIGH
            hazard.grid[2][15] = HIGH
            hazard.grid[3][13] = HIGH
            hazard.grid[3][14] = CRITICAL
            hazard.grid[3][15] = CRITICAL
            hazard.grid[3][16] = HIGH
            hazard.grid[4][13] = HIGH
            hazard.grid[4][14] = CRITICAL
            hazard.grid[4][15] = HIGH
            hazard.grid[4][16] = HIGH
            hazard.grid[5][14] = HIGH
            hazard.grid[5][15] = HIGH

        elif scenario == "S3 - Unsafe Shortest Route":
            robot = Robot((5, 2))
            for r in range(1, 14):
                env.grid[r][9] = env.WALL
            hazard.add_source((7, 9), CRITICAL)
            hazard.grid[5][8] = HIGH
            hazard.grid[5][9] = HIGH
            hazard.grid[5][10] = HIGH
            hazard.grid[6][8] = HIGH
            hazard.grid[6][9] = CRITICAL
            hazard.grid[6][10] = HIGH
            hazard.grid[7][8] = CRITICAL
            hazard.grid[7][9] = CRITICAL
            hazard.grid[7][10] = CRITICAL
            hazard.grid[8][8] = HIGH
            hazard.grid[8][9] = CRITICAL
            hazard.grid[8][10] = HIGH
            hazard.grid[9][8] = HIGH
            hazard.grid[9][9] = HIGH
            hazard.grid[9][10] = HIGH

        elif scenario == "S4 - Route Becomes Blocked":
            robot = Robot((2, 2))
            hazard.add_source((8, 8), LOW)

        elif scenario == "S5 - Failed Containment Point":
            robot = Robot((2, 12))
            env.valves["V2"].failed = True
            hazard.add_source((4, 15), HIGH)
            hazard.grid[3][14] = HIGH
            hazard.grid[3][15] = HIGH
            hazard.grid[3][16] = HIGH
            hazard.grid[4][14] = HIGH
            hazard.grid[4][15] = HIGH
            hazard.grid[4][16] = HIGH
            hazard.grid[5][14] = HIGH
            hazard.grid[5][15] = HIGH
            hazard.grid[5][16] = HIGH
            hazard.grid[6][14] = MEDIUM
            hazard.grid[6][15] = MEDIUM
            # A second, smaller hazard makes V1 a feasible fallback after V2 fails.
            hazard.grid[4][3] = MEDIUM
            hazard.grid[4][4] = MEDIUM
            hazard.grid[4][5] = MEDIUM
            hazard.grid[5][4] = MEDIUM

        else:
            robot = Robot((2, 2))
            hazard.add_source((10, 10), MEDIUM)

        return env, hazard, robot
