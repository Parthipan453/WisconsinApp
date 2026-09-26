import json


class ChartService:

    def build_donut_segments(self, counts_dict, total_count=None):
        labels_colors = [
            ("Present", "#16a34a"),
            ("Absent", "#dc2626"),
            ("Late", "#d97706"),
            ("On Leave", "#7c3aed"),
            ("Half Day", "#2563eb"),
        ]
        if total_count is None:
            status_keys = ["PRESENT", "ABSENT", "LATE", "ON_LEAVE", "HALF_DAY"]
            total_count = sum(counts_dict.get(s, 0) for s in status_keys)
        if total_count == 0:
            return []

        segments = []
        offset = 0.0
        for label, color in labels_colors:
            key = label.upper().replace(" ", "_") if label != "On Leave" else "ON_LEAVE"
            key = key if key == "ON_LEAVE" else label.upper().replace(" ", "_")
            # Fix key mapping
            key_map = {"PRESENT": "PRESENT", "ABSENT": "ABSENT", "LATE": "LATE",
                       "ON_LEAVE": "ON_LEAVE", "HALF_DAY": "HALF_DAY"}
            display_map = {"Present": "PRESENT", "Absent": "ABSENT", "Late": "LATE",
                          "On Leave": "ON_LEAVE", "Half Day": "HALF_DAY"}
            db_key = display_map[label]
            count = counts_dict.get(db_key, 0)
            pct = (count / total_count) * 100
            segments.append({
                "label": label, "count": count, "pct": round(pct, 1),
                "color": color, "offset": round(-offset, 1),
                "dash": round(pct, 1),
            })
            offset += pct
        return segments

    def build_donut_json(self, counts_dict):
        display_map = [
            ("Present", "PRESENT", "#16a34a"),
            ("Absent", "ABSENT", "#dc2626"),
            ("Late", "LATE", "#d97706"),
            ("On Leave", "ON_LEAVE", "#7c3aed"),
            ("Half Day", "HALF_DAY", "#2563eb"),
        ]
        return [
            {"l": label, "v": counts_dict.get(key, 0), "c": color}
            for label, key, color in display_map
        ]

    def build_chart_data_json(self, donut_data, trend_data, marked_count, pending_count):
        return json.dumps({
            "donut": donut_data,
            "trend": trend_data,
            "marked": [
                {"l": "Marked", "v": marked_count, "c": "#6366f1"},
                {"l": "Unmarked", "v": pending_count, "c": "#d1d5db"},
            ],
        })

    def build_calendar_data_json(self, popups, selected_date, selected_month, selected_year,
                                  department, today):
        return json.dumps({
            "popups": popups,
            "selected_date": selected_date.strftime("%Y-%m-%d"),
            "selected_month": selected_month - 1,
            "selected_year": selected_year,
            "department": int(department) if department else None,
            "today": today.strftime("%Y-%m-%d"),
        })

    def build_monthly_data_json(self, donut_data, daily_list, year, month):
        return json.dumps({
            "donut": donut_data,
            "daily": daily_list,
            "year": year,
            "month": month,
            "legend": [
                {"color": "#16a34a", "label": "Present", "count": 0},
                {"color": "#dc2626", "label": "Absent", "count": 0},
                {"color": "#d97706", "label": "Late", "count": 0},
                {"color": "#7c3aed", "label": "Leave", "count": 0},
                {"color": "#2563eb", "label": "Half", "count": 0},
            ]
        })
