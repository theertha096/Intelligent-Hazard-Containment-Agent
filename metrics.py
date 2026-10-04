import time
import pandas as pd


class PerformanceTracker:
    def __init__(self):
        self.rows=[]
        self.replan_events=0
        self.successful_replans=0
        self.containment_tick=None
        self.start_time=time.perf_counter()

    def record(self,tick,hazard,robot,target,astar_ms,action):
        self.rows.append({
            "tick":tick,
            "action":action,
            "affected_area":hazard.affected_area(),
            "max_hazard":hazard.maximum_level(),
            "robot_position":str(robot.state.position),
            "battery":round(robot.state.battery,2),
            "exposure":round(robot.state.exposure,2),
            "resources_left":robot.state.resources,
            "target":str(target),
            "replans":self.replan_events,
            "successful_replans":self.successful_replans,
            "astar_execution_ms":round(astar_ms,3),
        })

    def dataframe(self):
        return pd.DataFrame(self.rows)

    def summary(self, env, robot):
        df=self.dataframe()
        return {
            "containment_time_ticks": self.containment_tick if self.containment_tick is not None else "Not completed",
            "affected_area": int(df["affected_area"].iloc[-1]) if not df.empty else 0,
            "final_exposure": round(robot.state.exposure,2),
            "resources_used": 3-robot.state.resources,
            "replans": self.replan_events,
            "successful_replans": self.successful_replans,
            "critical_facilities": sum(f.status=="PROTECTED" for f in env.critical_facilities.values()),
            "steps": robot.state.steps,
        }

    def export(self,path="results/metrics.csv"):
        from pathlib import Path
        df=self.dataframe()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path,index=False)
        return df
