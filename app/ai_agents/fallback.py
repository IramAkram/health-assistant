"""Offline 'demo mode' assistant used when no OPENAI_API_KEY is configured (or the API call fails).

It mimics the coordinator -> specialist routing with simple keyword rules, so the whole application
can be demonstrated without internet access or API costs.
"""
from sqlalchemy.orm import Session

from ..services import analysis, tools

LABELS = {"systolic": "Systolic BP", "diastolic": "Diastolic BP", "glucose": "Glucose", "weight_kg": "Weight",
          "sleep_hours": "Sleep (h)", "exercise_minutes": "Exercise (min)", "stress_level": "Stress"}


def _route(msg: str) -> str:
    m = msg.lower()
    if any(k in m for k in ["report", "pdf", "download", "riport"]):
        return "report"
    if any(k in m for k in ["remind", "yaad", "yad dila"]):
        return "reminder"
    if any(k in m for k in ["alert", "warning", "danger", "khatra"]):
        return "alerts"
    if any(k in m for k in ["risk", "diabetes", "sugar risk"]):
        return "risk"
    if any(k in m for k in ["advice", "tip", "suggest", "improve", "diet", "sleep better", "exercise", "mashwara", "healthy"]):
        return "coach"
    return "analysis"


def _summary_text(summary: dict) -> str:
    if not summary.get("record_count"):
        return "You have no records in this period yet. Add a measurement and I can summarise your trends."
    lines = [f"Here is your summary for the last {summary['days']} days ({summary['record_count']} records):"]
    for k, m in summary["metrics"].items():
        lines.append(f"- {LABELS.get(k, k)}: average {m['mean']}, latest {m['latest']}, trend {m['trend']}")
    return "\n".join(lines)


def _coach_text(summary: dict, profile: dict) -> str:
    tips: list[str] = []
    m = summary.get("metrics", {})
    if "sleep_hours" in m and m["sleep_hours"]["mean"] < 7:
        tips.append(f"Your average sleep is {m['sleep_hours']['mean']} h. Try a fixed bedtime and no screens 30 minutes before sleep.")
    if "exercise_minutes" in m and m["exercise_minutes"]["mean"] < 30:
        tips.append(f"Your average activity is {m['exercise_minutes']['mean']} min/day. A brisk 30-minute walk on most days is a good start.")
    if "stress_level" in m and m["stress_level"]["mean"] >= 6:
        tips.append("Stress looks elevated. Short breathing exercises or a walk outdoors can help.")
    if "glucose" in m and m["glucose"]["trend"] == "rising":
        tips.append("Your glucose readings are trending upward. Consider limiting sugary drinks and discuss the trend with your doctor.")
    if "systolic" in m and m["systolic"]["trend"] == "rising":
        tips.append("Your blood pressure is trending upward. Reducing salt and keeping active may help; please mention it to your doctor.")
    if not tips:
        tips.append("Your recent numbers look steady. Keep up regular sleep, movement and hydration.")
    if profile.get("health_goal"):
        tips.append(f"Your stated goal is: {profile['health_goal']}. Set one small weekly target towards it.")
    return "General wellness suggestions:\n" + "\n".join(f"- {t}" for t in tips)


def run_demo(db: Session, user_id: int, message: str) -> str:
    route = _route(message)
    if route == "report":
        link = tools.report_link(30)
        text = "I can prepare your report. Open the Report tab and press 'Download PDF' (last 30 days).\n" \
               + _summary_text(tools.health_summary(db, user_id, 30))
    elif route == "reminder":
        items = tools.reminders(db, user_id)
        text = ("Your reminders:\n" + "\n".join(f"- {r['time_of_day']} ({r['frequency']}): {r['title']}" for r in items)
                if items else "You have no reminders yet. Add one in the Alerts & reminders tab.")
    elif route == "alerts":
        items = tools.alerts(db, user_id, limit=5)
        text = ("Recent alerts (from fixed safety rules):\n" + "\n".join(f"- [{a['severity']}] {a['message']}" for a in items)
                if items else "No alerts so far. Your recorded values have not crossed any configured threshold.")
    elif route == "risk":
        r = tools.diabetes_risk(db, user_id)
        text = (f"Model estimate (informational): diabetes-risk level is {r['band']} "
                f"(about {r['probability'] * 100:.0f}%). {r['disclaimer']}" if r.get("available") else r["reason"])
    elif route == "coach":
        text = _coach_text(tools.health_summary(db, user_id, 30), tools.user_profile(db, user_id))
    else:
        text = _summary_text(tools.health_summary(db, user_id, 30))
    return text
