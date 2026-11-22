"""Coordinator + 4 specialised agents built with the OpenAI Agents SDK.

Agents only use the permission-checked functions in app/services/tools.py.
They have NO direct database access.
"""
from agents import Agent, RunContextWrapper, function_tool

from ..config import settings
from ..services import tools
from .context import AgentContext

SAFETY = (
    "You are part of a personal wellness-tracking assistant. You must NEVER diagnose diseases, prescribe "
    "medication, or make emergency-care decisions. Present information as general and informational, and "
    "encourage consulting a qualified healthcare professional for concerns. Clearly separate (a) measured "
    "values, (b) model estimates and (c) general guidance. Only use data returned by your tools; never invent "
    "readings. If the user writes in Urdu or Roman Urdu, reply in the same language. Keep answers short and clear."
)


# ---- tool wrappers (the LLM can only pass harmless arguments, never a user id) ----
@function_tool
def get_health_summary(ctx: RunContextWrapper[AgentContext], days: int = 30) -> dict:
    """Averages, min/max, latest value and trend for each recorded measurement over the last `days` days."""
    return tools.health_summary(ctx.context.db, ctx.context.user_id, days)


@function_tool
def get_recent_records(ctx: RunContextWrapper[AgentContext], limit: int = 10) -> list[dict]:
    """The user's most recent individual health records."""
    return tools.recent_records(ctx.context.db, ctx.context.user_id, limit)


@function_tool
def get_diabetes_risk_estimate(ctx: RunContextWrapper[AgentContext]) -> dict:
    """Machine-learning diabetes-risk estimate (informational only) from the user's latest data."""
    return tools.diabetes_risk(ctx.context.db, ctx.context.user_id)


@function_tool
def get_user_profile(ctx: RunContextWrapper[AgentContext]) -> dict:
    """Age, gender, height, BMI and the user's stated health goal."""
    return tools.user_profile(ctx.context.db, ctx.context.user_id)


@function_tool
def get_alerts(ctx: RunContextWrapper[AgentContext], unread_only: bool = False) -> list[dict]:
    """Alerts raised by the deterministic rule engine."""
    return tools.alerts(ctx.context.db, ctx.context.user_id, unread_only)


@function_tool
def get_reminders(ctx: RunContextWrapper[AgentContext]) -> list[dict]:
    """The user's configured reminders."""
    return tools.reminders(ctx.context.db, ctx.context.user_id)


@function_tool
def create_reminder(ctx: RunContextWrapper[AgentContext], title: str, time_of_day: str, frequency: str = "daily") -> dict:
    """Create a reminder. time_of_day is 24-hour HH:MM (e.g. 07:30); frequency is 'daily' or 'weekly'."""
    return tools.create_reminder(ctx.context.db, ctx.context.user_id, title, time_of_day, frequency)


@function_tool
def get_report_download_link(ctx: RunContextWrapper[AgentContext], days: int = 30) -> dict:
    """Where the user can download the PDF report for the last `days` days."""
    return tools.report_link(days)


def build_coordinator() -> Agent:
    model = settings.OPENAI_MODEL

    health_analysis = Agent[AgentContext](
        name="Health Analysis Agent", model=model,
        instructions=SAFETY + " Your job: retrieve the user's records, summarise trends in plain language, and "
                     "request a risk estimate when relevant. Mention missing data honestly.",
        tools=[get_health_summary, get_recent_records, get_diabetes_risk_estimate])

    wellness_coach = Agent[AgentContext](
        name="Wellness Coach Agent", model=model,
        instructions=SAFETY + " Your job: give general, non-diagnostic lifestyle suggestions (sleep, activity, "
                     "stress, nutrition habits) based on the user's data and stated goal. Max 4 practical tips.",
        tools=[get_health_summary, get_user_profile])

    alert_reminder = Agent[AgentContext](
        name="Alert and Reminder Agent", model=model,
        instructions=SAFETY + " Your job: explain existing rule-based alerts calmly, list reminders, and create "
                     "reminders when asked. You cannot create, edit or dismiss alerts - they come from fixed rules.",
        tools=[get_alerts, get_reminders, create_reminder])

    report_agent = Agent[AgentContext](
        name="Health Report Agent", model=model,
        instructions=SAFETY + " Your job: prepare a short written summary of selected records and tell the user "
                     "how to download the PDF report.",
        tools=[get_health_summary, get_report_download_link])

    return Agent[AgentContext](
        name="Coordinator Agent", model=model,
        instructions=SAFETY + " You are the coordinator. Decide which specialist(s) to call for the user's request, "
                     "then combine their results into ONE clear final answer. Do not answer health-data questions "
                     "from memory - always call a specialist.",
        tools=[
            health_analysis.as_tool("health_analysis", "Analyse the user's health data, trends and risk estimate."),
            wellness_coach.as_tool("wellness_coach", "General lifestyle and wellness suggestions."),
            alert_reminder.as_tool("alerts_and_reminders", "Explain alerts; list or create reminders."),
            report_agent.as_tool("health_report", "Summarise records and explain how to get the PDF report."),
        ])
