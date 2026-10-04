# Intelligent Hazard Containment Agent

A college-level classical-AI simulation for a chemical plant. The project demonstrates:

- Perception of a changing plant state
- Rule-based reasoning
- Candidate action generation
- Hard safety constraints
- Heuristic action scoring
- Hazard-aware A* path planning
- Dynamic replanning when a route becomes unsafe
- Robot battery, exposure and resource limits
- Valve and door containment actions
- Critical-facility protection
- Five deterministic test scenarios
- Performance metrics and CSV logging
- Hazard-aware vs ordinary A* comparison
- Streamlit visualization
- Compact A* heuristic display showing h(n), g(n), f(n)=g(n)+h(n) and a few neighbouring-cell evaluations

## Required AI techniques

- A* Search and Manhattan-distance heuristic — `astar.py`
- Rule-based reasoning — `rules.py`
- Heuristic action evaluation — `decision.py`
- Constraint-based decision-making — `constraints.py`
- State-space representation and action transitions — `state.py` + simulation state
- Dynamic monitoring and replanning — `planner.py` + `main.py`, demonstrated by S4

## AI loop

`PERCEIVE -> REASON -> PLAN -> ACT -> ENVIRONMENT CHANGES -> PERCEIVE -> REPLAN`

## New dashboard features

- Scenario objective and expected behaviour shown before running
- AI concept demonstrated for each scenario
- Step-by-step explanation of every simulation step
- Compact interface table showing where each required classical-AI technique is implemented and demonstrated
- Explanation of perception, reasoning, candidate selection, constraints, planning, action and result
- Automatic description of what changed in the environment after each step
- Clear indication when a route is replanned
- Rejected-action panel showing why safety constraints removed an option
- Improved plant map with legends, hazard levels, target/path information and clearer device labels
- Cleaner agent status panel
- Existing candidate scores and performance metrics retained

## Files

- `main.py` - Streamlit application and orchestration
- `environment.py` - plant layout, walls, devices and critical areas
- `hazard.py` - dynamic hazard map, spread and containment
- `robot.py` - movement, battery, exposure and resources
- `sensors.py` - perception layer
- `rules.py` - rule-based reasoning
- `decision.py` - candidate generation and heuristic evaluation
- `constraints.py` - hard safety/resource checks
- `astar.py` - hazard-aware A* search
- `planner.py` - plan validation and replanning
- `state.py` - project state representation
- `scenarios.py` - S1-S5 evaluation scenarios and scenario explanations
- `metrics.py` - evaluation metrics and CSV export
- `dashboard.py` - Streamlit map rendering and visualization

## Run without a virtual environment

```text
py -3.13 -m pip install -r requirements.txt
py -3.13 -m streamlit run main.py
```

## Scenarios

### S1 - Nearby Leak
Demonstrates perception, rule-based reasoning and heuristic action selection.

### S2 - Critical Facility Threat
Demonstrates priority-based reasoning when a high-priority facility is threatened.

### S3 - Unsafe Shortest Route
Demonstrates constraints and hazard-aware A* route selection.

### S4 - Route Becomes Blocked
Demonstrates dynamic replanning when an already planned route becomes unsafe.

### S5 - Failed Containment Point
Demonstrates hard constraints and failure handling when a containment valve is unavailable.

## Evaluation

The project records affected area, maximum hazard, battery, exposure, resource usage, replans, successful replans, containment time, robot steps and A* execution time. Run the same scenario with hazard-aware A* enabled and disabled to demonstrate an ablation comparison.

## Final validation notes

The five scenarios are deterministic. The final version also checks that:
- S1 has a reachable nearby containment point.
- S2 contains a visible critical-facility threat.
- S3 demonstrates ordinary versus hazard-aware A* behavior.
- S4 invalidates a route during movement and replans from the current position.
- S5 rejects the failed V2 valve and retains V1 as a feasible alternative.

The dashboard keeps the detailed candidate table and event log available without making them the main focus. The A* panel is intentionally compact: it shows the start, target, path length, Manhattan heuristic, `f(n)=g(n)+h(n)`, and a few neighboring-cell examples.


## Custom robot start and safe-zone positions

The Streamlit sidebar now allows the user to choose:
- Robot start row and column
- Safe-zone target row and column

The default scenario positions are still available, so the five scenarios remain reproducible. The user can load a scenario and then apply different valid positions without changing the scenario's hazard/device setup.

### Position validation

A selected position is rejected if it is:
- outside the usable 1–18 row/column range
- a wall
- a valve position
- a door position
- a critical-facility position
- a CRITICAL hazard cell
- the same cell as the other selected position

When an invalid position is entered, Streamlit displays an alert explaining the reason and tells the user to choose another position. The invalid selection is not applied.

The safe-zone marker is moved to the selected valid cell and A* uses that cell as the safe-zone target whenever the robot needs to move to safety.

### How to use the new feature

1. Select a scenario.
2. Click **Load Scenario**.
3. Enter the robot start row/column.
4. Enter the safe-zone row/column.
5. Click **Apply Custom Positions**.
6. If a position is restricted, read the alert and enter another position.
7. After a valid selection, the simulation resets for that scenario using the chosen positions.
8. Click **Run One Step** to begin.

The scenario-specific containment targets and hazard setups are not removed. Customization changes only the robot's starting cell and the safe-zone target.

## Custom-position Streamlit fix

The custom Robot start / Safe-zone number inputs use Streamlit widget keys. The reset logic intentionally does not overwrite those widget keys after the widgets have been instantiated. This prevents `StreamlitWidgetAlreadyInstantiatedError` when **Reset Current Scenario** is clicked.

Resetting a scenario resets the actual simulation state to the scenario defaults. The number-input boxes remain user input controls and are not modified programmatically. The user can enter new coordinates and click **Apply Custom Positions**.

Invalid custom positions show only the specific validation error; no redundant second alert is displayed.


A* display clarification
------------------------
The A* dashboard now explicitly treats the robot's current position as the start node for the displayed neighbor calculation. Therefore, for each immediate neighbor, g(n) is the cumulative cost from that planning start (current_g + step cost). The default dashboard uses current_g=0 because the displayed neighbors are the first expansion from the current planning start. h(n) is Manhattan distance and f(n)=g(n)+h(n). Additional tests verify the heuristic and g/h/f calculations.
