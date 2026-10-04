from hazard import HIGH, CRITICAL


class RuleEngine:
    def evaluate(self, perception):
        rules = []
        grid = perception["hazard_grid"]

        for name, facility in perception["critical_facilities"].items():
            r, c = facility["position"]
            nearby = []
            for rr in range(max(0,r-1), min(len(grid),r+2)):
                for cc in range(max(0,c-1), min(len(grid[0]),c+2)):
                    nearby.append(grid[rr][cc])
            if max(nearby, default=0) >= HIGH:
                rules.append({"rule":"CRITICAL_FACILITY_THREATENED", "target":name, "boost":15, "reason":f"High hazard is near {name}."})

        if perception["robot_exposure"] >= 50:
            rules.append({"rule":"HIGH_EXPOSURE", "target":"ROBOT", "boost":0, "reason":"Robot exposure is high; prefer safer routes."})

        if perception["robot_resources"] <= 1:
            rules.append({"rule":"LOW_RESOURCES", "target":"ROBOT", "boost":0, "reason":"Only one resource remains; avoid unnecessary containment actions."})

        max_hazard = max(max(row) for row in grid)
        if max_hazard >= CRITICAL:
            rules.append({"rule":"CRITICAL_HAZARD", "target":"HAZARD", "boost":20, "reason":"Critical hazard detected; immediate containment has priority."})
        return rules
