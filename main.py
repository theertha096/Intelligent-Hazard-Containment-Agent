import time
import pandas as pd
import streamlit as st
from scenarios import ScenarioFactory, SCENARIO_INFO
from sensors import SensorSystem
from rules import RuleEngine
from constraints import ConstraintEngine
from decision import DecisionEngine
from astar import AStarPlanner
from planner import IntegratedPlanner
from metrics import PerformanceTracker
from dashboard import DashboardRenderer
from hazard import HIGH
from state import StateSpaceModel
from position_validation import restricted_position_reason

st.set_page_config(page_title="Intelligent Hazard Containment Agent", layout="wide")
SCENARIOS=list(SCENARIO_INFO)


def apply_custom_positions(start_position, safe_position):
    """Validate and apply user-selected robot start and safe-zone positions."""
    env, hazard = st.session_state.env, st.session_state.hazard
    start_error = restricted_position_reason(env, hazard, start_position, "Robot start")
    safe_error = restricted_position_reason(env, hazard, safe_position, "Safe-zone target")
    if start_error or safe_error:
        if start_error:
            st.error(start_error)
        if safe_error:
            st.error(safe_error)
        return False
    if start_position == safe_position:
        st.error("Robot start and safe-zone target cannot be the same cell. Please choose another position.")
        return False

    scenario = st.session_state.scenario
    env, hazard, robot = ScenarioFactory.create(scenario)
    start_error = restricted_position_reason(env, hazard, start_position, "Robot start")
    safe_error = restricted_position_reason(env, hazard, safe_position, "Safe-zone target")
    if start_error or safe_error:
        if start_error:
            st.error(start_error)
        if safe_error:
            st.error(safe_error)
        return False

    env.set_safe_zone(safe_position)
    robot.state.position = start_position
    st.session_state.update(
        env=env, hazard=hazard, robot=robot, tick=0,
        tracker=PerformanceTracker(), state_model=StateSpaceModel(),
        logs=["System initialized with custom robot start and safe-zone target."],
        candidates=[], rejected=[], rules=[], action="MONITOR",
        reason="Waiting for first step.", step_techniques=[], containment_complete=False,
        explanation={
            "step": "Waiting for Step 1",
            "perceive": "Run one step to begin.",
            "reason": "No rules have been checked yet.",
            "candidate": "No containment target selected.",
            "constraints": "No constraints checked yet.",
            "act": "No action taken yet.",
            "result": "Waiting for the first simulation step.",
            "changes": [],
        },
    )
    return True

def reset(name):
    env,hazard,robot=ScenarioFactory.create(name)
    # Do not modify the number_input widget state here. Streamlit does not allow
    # changing a widget's session_state key after that widget has been created
    # during the current run. The widgets are input controls only; the actual
    # robot/safe-zone positions are stored in env and robot state.
    st.session_state.update(env=env,hazard=hazard,robot=robot,scenario=name,tick=0,
        tracker=PerformanceTracker(),state_model=StateSpaceModel(),logs=["System initialized."],
        candidates=[],rejected=[],rules=[],action="MONITOR",reason="Waiting for first step.",
        step_techniques=[],containment_complete=False,explanation={"step":"Waiting for Step 1",
        "perceive":"Run one step to begin.","reason":"No rules have been checked yet.",
        "candidate":"No containment target selected.","constraints":"No constraints checked yet.",
        "act":"No action taken yet.","result":"Waiting for the first simulation step.","changes":[]})

def facility_status(env,hazard):
    for f in env.critical_facilities.values():
        r,c=f.position
        cells=[hazard.grid[x][y] for x in range(max(0,r-1),min(env.rows,r+2))
               for y in range(max(0,c-1),min(env.cols,c+2))]
        f.status="THREATENED" if max(cells,default=0)>=HIGH else "PROTECTED"

def plan(planner,start,goal,env,hazard,aware):
    path=planner.make_plan(start,goal,env,hazard.grid,aware)
    try: ex=AStarPlanner().explain_neighbors(start,goal,env,hazard.grid,aware)
    except Exception: ex=[]
    return path,ex[0] if ex else None

def step(aware=True):
    env,hazard,robot=st.session_state.env,st.session_state.hazard,st.session_state.robot
    st.session_state.tick+=1; tick=st.session_state.tick
    old=(robot.state.position,robot.state.battery,robot.state.exposure,robot.state.resources,list(robot.state.current_path))
    area,maximum=hazard.affected_area(),hazard.maximum_level()
    hazard.update(env,tick)
    if st.session_state.scenario=="S4 - Route Becomes Blocked" and tick==4 and len(robot.state.current_path)>3:
        r,c=robot.state.current_path[2]; hazard.grid[r][c]=4
    facility_status(env,hazard)
    perception=SensorSystem().perceive(env,hazard,robot)
    rules=RuleEngine().evaluate(perception)
    raw=DecisionEngine().generate_candidates(perception)
    allowed,rejected=ConstraintEngine().filter_candidates(raw,perception)
    candidates=DecisionEngine().score(allowed,perception,rules)
    st.session_state.rules,st.session_state.candidates,st.session_state.rejected=rules,candidates,rejected
    planner=IntegratedPlanner(AStarPlanner())
    target=next((c for c in candidates if c.target_id==robot.state.current_target),None) or (candidates[0] if candidates else None)
    if st.session_state.scenario=="S3 - Unsafe Shortest Route" and st.session_state.containment_complete: target=None
    emergency_retreat=robot.state.exposure>=70 and not (st.session_state.scenario=="S3 - Unsafe Shortest Route" and target)
    if emergency_retreat: target=None; robot.state.current_target=None
    action,reason="MONITOR","No urgent containment action selected."
    start_time=time.perf_counter()
    goal=target.position if target else env.safe_zone
    valid=planner.validate_path(robot.state.current_path,env,hazard.grid)
    invalid=bool(robot.state.current_path) and not valid
    astar=False; astart=agoal=aexample=None
    if emergency_retreat:
        robot.state.current_path=[]
        astart,agoal=robot.state.position,env.safe_zone
        path,aexample=plan(planner,astart,agoal,env,hazard,aware); astar=True
        needed=max(0,len(path)-1) if path else None
        if astart==agoal:
            action,reason="RETREAT","Robot reached the safe zone after the exposure threshold was reached."
            robot.state.status="SAFE"
        elif robot.state.battery<=0:
            action,reason="BATTERY_DEPLETED","Battery reached 0% before the robot reached the safe zone."
            robot.state.status="BATTERY_DEPLETED"
        elif path and len(path)>1 and needed<=robot.state.battery:
            robot.state.current_target_position=goal; robot.state.current_path=path
            if robot.move_to(path[1],env,hazard.grid[path[1][0]][path[1][1]]):
                robot.state.current_path.pop(0)
            action,reason="RETREAT","Exposure threshold reached; retreat route is feasible with the remaining battery."
            robot.state.status="RETREAT_REQUIRED"
        elif path and len(path)>1:
            action,reason="INSUFFICIENT_BATTERY",f"Safe-zone route needs {needed} battery units, but only {robot.state.battery:.0f}% remain."
            robot.state.status="BATTERY_INSUFFICIENT"
        else:
            action,reason="NO_SAFE_PATH","Exposure threshold reached, but no safe retreat route is available."
            robot.state.status="RETREAT_REQUIRED"
    elif target:
        reroute=robot.state.current_target!=target.target_id or not valid
        if reroute:
            if robot.state.current_path:
                robot.state.replan_count+=1; st.session_state.tracker.replan_events+=1
                reason="Current route became invalid; replanning."
            astart,agoal=robot.state.position,goal
            path,aexample=plan(planner,astart,goal,env,hazard,aware); astar=True
            if path:
                robot.state.current_path=path; robot.state.current_target=target.target_id; robot.state.current_target_position=goal
                action="REPLAN" if reason.startswith("Current") else "PLAN_CONTAINMENT"
                if action=="REPLAN": robot.state.successful_replans+=1; st.session_state.tracker.successful_replans+=1
            else: action,reason="NO_SAFE_PATH","No safe path is currently available."
        else: action="MOVE_TO_TARGET"
        if len(robot.state.current_path)>1:
            p=robot.state.current_path[1]
            if robot.move_to(p,env,hazard.grid[p[0]][p[1]]): robot.state.current_path.pop(0)
        if robot.state.current_target and robot.state.position==robot.state.current_target_position:
            if target.action_type=="CLOSE_VALVE":
                v=env.valves[target.target_id]
                if robot.use_resource(): v.status="CLOSED"; hazard.apply_containment(v.position,v.effectiveness); action,reason="CLOSE_VALVE",f"Valve {v.id} closed and containment applied."
            else:
                d=env.doors[target.target_id]
                if robot.use_resource(): d.status="CLOSED"; action,reason="CLOSE_DOOR",f"Door {d.id} closed to limit spread."
            robot.state.current_target=robot.state.current_target_position=None; robot.state.current_path=[]
            if st.session_state.scenario=="S3 - Unsafe Shortest Route" and action=="CLOSE_DOOR": st.session_state.containment_complete=True
            facility_status(env,hazard)
            if hazard.maximum_level()<HIGH: st.session_state.tracker.containment_tick=tick
    elif invalid:
        astart,agoal=robot.state.position,goal; path,aexample=plan(planner,astart,goal,env,hazard,aware); astar=True
        robot.state.replan_count+=1; st.session_state.tracker.replan_events+=1
        if path:
            robot.state.current_path=path; robot.state.current_target_position=goal; action,reason="REPLAN","The existing route became unsafe, so A* planned a new route."; robot.state.successful_replans+=1; st.session_state.tracker.successful_replans+=1
        else: robot.state.current_path=[]; action,reason="NO_SAFE_PATH","The previous route is unsafe and no replacement route is available."
    else:
        astart,agoal=robot.state.position,env.safe_zone; path,aexample=plan(planner,astart,agoal,env,hazard,aware); astar=True
        if path and len(path)>1:
            robot.state.current_path=path; robot.move_to(path[1],env,hazard.grid[path[1][0]][path[1][1]]); robot.state.current_path.pop(0); action,reason="MOVE_TO_SAFE_ZONE","No urgent containment target; moving toward safe zone."
    new=(robot.state.position,robot.state.battery,robot.state.exposure,robot.state.resources,robot.state.current_path)
    changes=[]
    if old[0]!=new[0]: changes.append(f"Robot moved from {old[0]} to {new[0]}.")
    if area!=hazard.affected_area(): changes.append(f"Affected area changed from {area} to {hazard.affected_area()} cells.")
    if maximum!=hazard.maximum_level(): changes.append(f"Maximum hazard changed from {maximum} to {hazard.maximum_level()}.")
    if not changes: changes=["No major state change occurred."]
    st.session_state.action,st.session_state.reason=action,reason
    st.session_state.step_techniques=techniques(st.session_state.scenario,rules,candidates,rejected,action,target,astar,astart,agoal,aexample,aware,old,new)
    st.session_state.explanation={"step":f"Step {tick}: {action}","perceive":f"Position {new[0]}, battery {new[1]:.0f}%, exposure {new[2]:.1f}, maximum hazard {hazard.maximum_level()}.","reason":" ".join(r["reason"] for r in rules) or "No special rule was triggered.","candidate":f"{target.target_id} at {target.position} (score {target.score})." if target else "No containment target selected.","constraints":f"{len(rejected)} candidate action(s) rejected." if rejected else "No candidate actions rejected.","act":{"REPLAN":"The old route became unsafe, so A* generated a new route.","PLAN_CONTAINMENT":"The decision layer selected a containment target and A* planned a route.","MOVE_TO_TARGET":"The robot followed the existing route to its target.","CLOSE_VALVE":"The robot reached a valve and applied containment.","CLOSE_DOOR":"The robot reached a door and closed it.","MOVE_TO_SAFE_ZONE":"The robot moved toward the safe zone.","RETREAT":"The robot switched to a retreat state.","INSUFFICIENT_BATTERY":"The safe-zone route is longer than the remaining battery, so the robot stopped.","BATTERY_DEPLETED":"The robot stopped because the battery reached zero.","NO_SAFE_PATH":"No safe route was available."}.get(action,action),"result":reason,"changes":changes}
    st.session_state.state_model.transition(env,hazard,robot,action,reason)
    ms=(time.perf_counter()-start_time)*1000
    st.session_state.tracker.record(tick,hazard,robot,robot.state.current_target,ms,action)
    st.session_state.logs.insert(0,f"Step {tick} — {action} — Position {robot.state.position} — {reason}")

def techniques(scenario,rules,candidates,rejected,action,target,astar,start,goal,ex,aware,old,new):
    rt=" | ".join(r["rule"]+": "+r["reason"] for r in rules[:2]) if rules else "No rule triggered in this step."
    if candidates:
        c=candidates[0]; b=c.breakdown
        dt=f"Selected {c.action_type} → {c.target_id}; score = {c.score} (hazard +{b.get('hazard_reduction',0)}, criticality +{b.get('criticality',0)}, distance {b.get('distance_penalty',0)}, risk {b.get('risk_penalty',0)}, resources {b.get('resource_penalty',0)})."
    else: dt="No feasible containment candidate was scored in this step."
    ct="; ".join(f"{c.target_id}: {why}" for c,why in rejected[:2]) if rejected else "No candidate was rejected by a hard constraint in this step."
    if astar and start is not None:
        at=f"A* planned from {start} → {goal}; representative node: g(n)={ex.get('g(n)','?')}, h(n)={ex.get('h(n)','?')}, f(n)=g+h={ex.get('f(n)','?')}." if ex else f"A* was executed from {start} → {goal}; no neighbour example was available."
        if aware: at+=" Hazard-aware cost is enabled."
    elif action=="MOVE_TO_TARGET": at="A* was not rerun; the robot followed the route calculated in an earlier step."
    else: at="A* was not executed in this click."
    names={"S1 - Nearby Leak":["Rule-based reasoning","Heuristic action selection","A* search + Manhattan heuristic","State-space planning"],"S2 - Critical Facility Threat":["Rule-based reasoning","Heuristic action selection","Constraint-based decision-making","A* search + Manhattan heuristic","State-space planning"],"S3 - Unsafe Shortest Route":["Constraint-based decision-making","A* search + Manhattan heuristic","Hazard-aware path cost","State-space planning"],"S4 - Route Becomes Blocked":["State-space planning","Dynamic replanning","A* search + Manhattan heuristic","Constraint-based decision-making"]}.get(scenario,["Rule-based reasoning","Constraint-based decision-making","Heuristic action selection","A* search + Manhattan heuristic","State-space planning"])
    d={"Rule-based reasoning":rt,"Heuristic action selection":dt,"Constraint-based decision-making":ct,"A* search + Manhattan heuristic":at,"Hazard-aware path cost":"Hazard penalties are included in the A* path cost for this click; safer cells receive lower route cost." if astar and aware else "No new hazard-aware A* calculation was needed in this click.","State-space planning":f"State transition: robot {old[0]} → {new[0]}; battery {old[1]:.0f}% → {new[1]:.0f}%; exposure {old[2]:.1f} → {new[2]:.1f}; resources {old[3]} → {new[3]}.","Dynamic replanning":f"Old route was invalidated; A* generated a replacement route of {max(0,len(new[4])-1)} move(s)." if action=="REPLAN" else "No dynamic replanning was triggered in this click."}
    return [(n,"✓",d[n]) for n in names]

def sidebar():
    with st.sidebar:
        st.subheader("Simulation Setup")
        scenario=st.selectbox("Scenario",SCENARIOS,index=SCENARIOS.index(st.session_state.scenario))
        aware=st.checkbox("Hazard-aware A*",True,key="astar_aware")

        if st.button("Load Scenario",use_container_width=True):
            reset(scenario)
            st.rerun()

        st.divider()
        st.subheader("Custom Robot & Safe-Zone Positions")
        st.caption("Choose row and column values from 1 to 18. Walls, devices, critical facilities, and critical-hazard cells are rejected.")

        start_col1, start_col2 = st.columns(2)
        with start_col1:
            start_row=st.number_input("Robot start row",min_value=1,max_value=18,step=1,key="custom_start_row")
        with start_col2:
            start_col=st.number_input("Robot start column",min_value=1,max_value=18,step=1,key="custom_start_col")

        safe_col1, safe_col2 = st.columns(2)
        with safe_col1:
            safe_row=st.number_input("Safe-zone row",min_value=1,max_value=18,step=1,key="custom_safe_row")
        with safe_col2:
            safe_col=st.number_input("Safe-zone column",min_value=1,max_value=18,step=1,key="custom_safe_col")

        if st.button("Apply Custom Positions",use_container_width=True):
            if apply_custom_positions((int(start_row),int(start_col)),(int(safe_row),int(safe_col))):
                st.success("Custom positions applied. The simulation was reset for the selected scenario.")
                st.rerun()

        st.caption("If an alert appears, no change is applied. Choose another position and try again.")

        st.divider()
        if st.button("Run One Step",use_container_width=True):
            step(aware)
            st.rerun()
        if st.button("Reset Current Scenario",use_container_width=True):
            reset(st.session_state.scenario)
            st.rerun()
        st.divider()
        st.caption("Perceive → Reason → Select → Constrain → Plan → Act → Replan")

def ui():
    info=SCENARIO_INFO[st.session_state.scenario]
    st.title("Intelligent Hazard Containment Agent"); st.caption("Classical AI: PERCEIVE → REASON → PLAN → ACT → REPLAN"); st.subheader(info["title"])
    a,b,c=st.columns(3)
    for col,key in zip((a,b,c),("objective","concept","expected")): col.info(f"**{key.title()}**\n\n{info[key]}")
    st.write(f"**Current situation:** {info['situation']}")
    st.info(f"**Selected robot start:** {st.session_state.robot.state.position}  |  **Selected safe-zone target:** {st.session_state.env.safe_zone}")
    st.subheader("Techniques Applied — This Step")
    rows=st.session_state.step_techniques
    if rows:
        df = pd.DataFrame(rows, columns=["Technique", "Active", "What happened in this step"])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Run One Step to see the techniques and actual evidence.")
    left,right=st.columns([3,2])
    with left:
        st.subheader("Plant Map"); r=st.session_state.robot; DashboardRenderer.map(st.session_state.env,st.session_state.hazard,r,r.state.current_path); DashboardRenderer.legend(); DashboardRenderer.hazard_legend()
    with right:
        s=st.session_state.robot.state; st.subheader("Agent Status")
        cols = st.columns(3)
        values = [("Position", str(s.position)), ("Battery", f"{s.battery:.0f}%"),
                  ("Exposure", f"{s.exposure:.1f}"), ("Resources", str(s.resources)),
                  ("Steps", str(s.steps)), ("Replans", str(s.replan_count))]
        for i, (key, value) in enumerate(values):
            cols[i % 3].metric(key, value)
        st.write(f"**Action:** {st.session_state.action}"); st.caption(st.session_state.reason); st.write(f"**Target:** {s.current_target or 'None'}"); st.write(f"**Status:** {s.status}")
    st.subheader("A* Path Planning")
    s=st.session_state.robot.state; goal=s.current_target_position or st.session_state.env.safe_zone; aware=st.session_state.get("astar_aware",True); rows=AStarPlanner().explain_neighbors(s.position,goal,st.session_state.env,st.session_state.hazard.grid,aware)
    a,b,c=st.columns(3); a.metric("Start",str(s.position)); b.metric("Target",str(goal)); c.metric("Path length",str(max(0,len(s.current_path)-1)))
    st.markdown("**Heuristic:** `h(n) = |row - target_row| + |column - target_column|`")
    st.markdown("**A* cost:** `f(n) = g(n) + h(n)` — `g(n)` is cumulative path cost from the current planning start; hazard adds to `g(n)`. ")
    if rows: st.dataframe(pd.DataFrame(rows[:4]),use_container_width=True,hide_index=True)
    else: st.info("No safe neighbouring cells are available from the robot's current position.")
    if st.session_state.action=="REPLAN": st.success("The previous route became unsafe, so A* planned a new route.")
    e=st.session_state.explanation; st.subheader("Step-by-Step Explanation"); st.write(f"**{e['step']}**")
    for col,items in zip(st.columns(2),[[("1. PERCEIVE",e["perceive"]),("3. CANDIDATE / SELECT",e["candidate"]),("5. PLAN / ACT",e["act"])],[("2. REASON",e["reason"]),("4. CONSTRAINTS",e["constraints"]),("6. RESULT",e["result"])]]):
        with col:
            for title,text in items: st.markdown(f"**{title}**"); st.write(text)
    st.write("**What changed?**")
    for change in e["changes"]:
        st.write("•", change)
    st.subheader("Decision")
    if st.session_state.candidates:
        best=st.session_state.candidates[0]; st.write(f"**Selected action:** {best.action_type} → {best.target_id}")
        with st.expander("Decision Details"):
            decision_rows = [{"Action": f"{c.action_type} → {c.target_id}", "Score": c.score}
                            for c in st.session_state.candidates]
            st.dataframe(pd.DataFrame(decision_rows), use_container_width=True, hide_index=True)
    else: st.write("No containment candidates are currently active.")
    if st.session_state.rejected:
        with st.expander("Rejected Actions — Hard Constraints"):
            for c,why in st.session_state.rejected: st.write(f"**{c.action_type} → {c.target_id}:** {why}")
    st.subheader("Performance Metrics")
    summary = st.session_state.tracker.summary(st.session_state.env, st.session_state.robot)
    cols = st.columns(4)
    for i, (key, value) in enumerate(summary.items()):
        cols[i % 4].metric(key.replace("_", " ").title(), str(value))
    with st.expander("Event Log"):
        for x in st.session_state.logs[:6]: st.write(x)
    with st.expander("Ablation / Comparison"):
        st.write("Run the same scenario with hazard-aware A* enabled and disabled, then compare the metrics.")
        if st.button("Export Metrics CSV"): st.dataframe(st.session_state.tracker.export().tail(10),use_container_width=True,hide_index=True)

if "env" not in st.session_state: reset(SCENARIOS[0])
sidebar(); ui()
