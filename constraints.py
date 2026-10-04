from hazard import CRITICAL


class ConstraintEngine:
    def filter_candidates(self, candidates, perception):
        allowed = []
        rejected = []
        for candidate in candidates:
            if perception["robot_resources"] <= 0:
                rejected.append((candidate, "No containment resources remain.")); continue
            r, c = candidate.position
            if perception["hazard_grid"][r][c] >= CRITICAL:
                rejected.append((candidate, "Target is in a critical hazard cell.")); continue
            if candidate.action_type == "CLOSE_VALVE":
                valve = perception["valves"].get(candidate.target_id)
                if not valve or valve["status"] != "OPEN" or valve["failed"]:
                    rejected.append((candidate, "Valve is unavailable.")); continue
            if candidate.action_type == "CLOSE_DOOR":
                door = perception["doors"].get(candidate.target_id)
                if not door or door["status"] != "OPEN":
                    rejected.append((candidate, "Door is unavailable.")); continue
            if perception["robot_battery"] <= 10:
                rejected.append((candidate, "Battery reserve is too low.")); continue
            allowed.append(candidate)
        return allowed, rejected
