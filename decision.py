from state import ActionCandidate


class DecisionEngine:
    def __init__(self):
        self.weights = {
            "hazard_reduction": 5.0,
            "criticality": 4.0,
            "distance": 2.0,
            "robot_risk": 4.0,
            "resource_cost": 3.0,
        }

    def generate_candidates(self, perception):
        candidates = []
        grid = perception["hazard_grid"]

        for name, valve in perception["valves"].items():
            if valve["status"] == "OPEN":
                r, c = valve["position"]
                local = max(grid[r][c], max((grid[rr][cc] for rr,cc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)) if 0<=rr<len(grid) and 0<=cc<len(grid[0])), default=0))
                if local >= 2 or valve["failed"]:
                    candidates.append(ActionCandidate("CLOSE_VALVE", name, valve["position"]))

        for name, door in perception["doors"].items():
            if door["status"] == "OPEN":
                r, c = door["position"]
                local = max(grid[r][c], max((grid[rr][cc] for rr,cc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)) if 0<=rr<len(grid) and 0<=cc<len(grid[0])), default=0))
                if local >= 2:
                    candidates.append(ActionCandidate("CLOSE_DOOR", name, door["position"]))
        return candidates

    def score(self, candidates, perception, rules):
        robot = perception["robot_pos"]
        grid = perception["hazard_grid"]
        scored = []
        for cand in candidates:
            r, c = cand.position
            dist = abs(robot[0]-r) + abs(robot[1]-c)
            if cand.action_type == "CLOSE_VALVE":
                obj = perception["valves"][cand.target_id]
            else:
                obj = perception["doors"][cand.target_id]
            local = grid[r][c]
            hazard_reduction = obj["effectiveness"] * max(1, local)
            criticality = 0
            for facility in perception["critical_facilities"].values():
                fd = abs(facility["position"][0]-r) + abs(facility["position"][1]-c)
                if fd <= 5:
                    criticality += facility["priority"] * (6-fd)
            robot_risk = local + obj["risk"]
            resource_cost = 1
            boost = 0
            for rule in rules:
                if rule["rule"] != "CRITICAL_FACILITY_THREATENED":
                    continue
                facility = perception["critical_facilities"].get(rule["target"])
                if facility:
                    fd = abs(facility["position"][0] - r) + abs(facility["position"][1] - c)
                    if fd <= 5:
                        boost += rule.get("boost", 0)

            score = (
                self.weights["hazard_reduction"] * hazard_reduction
                + self.weights["criticality"] * criticality
                + boost
                - self.weights["distance"] * dist
                - self.weights["robot_risk"] * robot_risk
                - self.weights["resource_cost"] * resource_cost
            )
            cand.score = round(score,2)
            cand.breakdown = {"hazard_reduction":round(hazard_reduction,2),"criticality":round(criticality,2),"distance_penalty":round(-self.weights["distance"]*dist,2),"risk_penalty":round(-self.weights["robot_risk"]*robot_risk,2),"resource_penalty":-self.weights["resource_cost"]}
            scored.append(cand)
        return sorted(scored, key=lambda x:x.score, reverse=True)
