import streamlit as st
from hazard import SAFE, LOW, MEDIUM, HIGH, CRITICAL


class DashboardRenderer:
    COLORS = {
        SAFE: "#f8fafc",
        LOW: "#fff7b2",
        MEDIUM: "#ffd166",
        HIGH: "#f8961e",
        CRITICAL: "#d62828",
    }

    @staticmethod
    def map(env, hazard, robot, path):
        path = set(path or [])
        cells = []

        for r in range(env.rows):
            for c in range(env.cols):
                p = (r, c)
                label = ""
                bg = DashboardRenderer.COLORS.get(
                    hazard.grid[r][c], "#f8fafc"
                )
                fg = "#111827"
                border = "#d1d5db"

                if env.grid[r][c] == env.WALL:
                    label = "W"
                    bg = "#374151"
                    fg = "#ffffff"
                    border = "#374151"

                if p in path:
                    # Keep the hazard colour visible even when the planned path crosses it.
                    if hazard.grid[r][c] == CRITICAL:
                        bg = DashboardRenderer.COLORS[CRITICAL]
                        fg = "#ffffff"
                        border = "#7f1d1d"
                        label = "!"
                    elif hazard.grid[r][c] == HIGH:
                        bg = DashboardRenderer.COLORS[HIGH]
                        fg = "#ffffff"
                        border = "#c2410c"
                        label = "!"
                    else:
                        label = "•"
                        bg = "#bfdbfe"
                        fg = "#1e3a8a"

                for name, valve in env.valves.items():
                    if p == valve.position:
                        label = name
                        if hazard.grid[r][c] == CRITICAL:
                            bg = DashboardRenderer.COLORS[CRITICAL]
                            border = "#7f1d1d"
                        elif hazard.grid[r][c] == HIGH:
                            bg = DashboardRenderer.COLORS[HIGH]
                            border = "#c2410c"
                        else:
                            bg = "#2563eb" if valve.status == "OPEN" else "#64748b"
                        fg = "#ffffff"

                for name, door in env.doors.items():
                    if p == door.position:
                        label = name
                        if hazard.grid[r][c] == CRITICAL:
                            bg = DashboardRenderer.COLORS[CRITICAL]
                            border = "#7f1d1d"
                        elif hazard.grid[r][c] == HIGH:
                            bg = DashboardRenderer.COLORS[HIGH]
                            border = "#c2410c"
                        else:
                            bg = "#7c3aed" if door.status == "OPEN" else "#64748b"
                        fg = "#ffffff"

                for name, facility in env.critical_facilities.items():
                    if p == facility.position:
                        label = "C"
                        if hazard.grid[r][c] == CRITICAL:
                            bg = DashboardRenderer.COLORS[CRITICAL]
                            border = "#7f1d1d"
                        elif hazard.grid[r][c] == HIGH:
                            bg = DashboardRenderer.COLORS[HIGH]
                            border = "#c2410c"
                        else:
                            bg = "#111827"
                            border = "#dc2626"
                        fg = "#ffffff"

                if p == env.safe_zone:
                    label = "S"
                    bg = "#22c55e"
                    fg = "#ffffff"

                if p == robot.state.position:
                    label = "R"
                    bg = "#0f766e"
                    fg = "#ffffff"
                    border = "#134e4a"

                title = f"Cell ({r}, {c}) | Hazard level: {hazard.grid[r][c]}"

                cells.append(
                    f'<div title="{title}" style="'
                    f'width:27px;height:27px;'
                    f'background:{bg};color:{fg};'
                    f'display:flex;align-items:center;justify-content:center;'
                    f'font-size:9px;font-weight:700;'
                    f'border:1px solid {border};box-sizing:border-box;">'
                    f'{label}</div>'
                )

        st.markdown(
            '<div style="display:flex;justify-content:center;overflow:auto;'
            'padding:8px 0 4px;">'
            '<div style="display:grid;grid-template-columns:repeat(20,27px);'
            'gap:2px;padding:8px;border-radius:12px;background:#e5e7eb;'
            'box-shadow:0 2px 8px rgba(0,0,0,.08);">'
            + "".join(cells)
            + "</div></div>",
            unsafe_allow_html=True,
        )

    @staticmethod
    def legend():
        items = [
            ("R", "Robot", "#0f766e"),
            ("•", "Planned path", "#bfdbfe"),
            ("V", "Valve", "#2563eb"),
            ("D", "Door", "#7c3aed"),
            ("C", "Critical facility", "#111827"),
            ("S", "Safe zone", "#22c55e"),
            ("W", "Wall", "#374151"),
        ]

        html = '<div style="display:flex;flex-wrap:wrap;gap:7px;margin:6px 0 14px;">'
        for symbol, label, color in items:
            html += (
                '<span style="display:inline-flex;align-items:center;gap:5px;'
                'padding:4px 8px;border:1px solid #e5e7eb;border-radius:999px;'
                'font-size:12px;background:#ffffff;">'
                f'<b style="width:20px;height:20px;border-radius:5px;'
                f'display:inline-flex;align-items:center;justify-content:center;'
                f'background:{color};color:#fff;">{symbol}</b>{label}</span>'
            )
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

    @staticmethod
    def hazard_legend():
        items = [
            ("Safe", "#f8fafc"),
            ("Low", "#fff7b2"),
            ("Medium", "#ffd166"),
            ("High", "#f8961e"),
            ("Critical", "#d62828"),
        ]
        html = '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px;">'
        for label, color in items:
            text = "#ffffff" if label in ("High", "Critical") else "#111827"
            html += (
                f'<span style="padding:4px 9px;border-radius:999px;'
                f'background:{color};color:{text};font-size:11px;">{label}</span>'
            )
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)
