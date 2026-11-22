"""Unit tests for the pure logic (no database / web server needed)."""
from datetime import date, datetime, timedelta

from app.services import alert_rules, analysis, ml_service, report_service


def test_normal_reading_has_no_alerts():
    assert alert_rules.evaluate_record({"systolic": 118, "diastolic": 76, "glucose": 95, "sleep_hours": 7.5}) == []


def test_critical_blood_pressure():
    a = alert_rules.evaluate_record({"systolic": 190, "diastolic": 100})
    assert a and a[0]["severity"] == "critical"


def test_high_glucose_warning_and_critical_low():
    assert alert_rules.evaluate_record({"glucose": 200})[0]["severity"] == "warning"
    assert alert_rules.evaluate_record({"glucose": 45})[0]["severity"] == "critical"


def test_bmi_and_age():
    assert analysis.bmi(70, 175) == 22.9
    assert analysis.bmi(None, 175) is None
    assert analysis.age_from_dob(date(2000, 6, 1), today=date(2025, 5, 31)) == 24


def test_summary_trend_and_series():
    now = datetime(2025, 1, 10)
    recs = [{"recorded_at": now + timedelta(days=i), "glucose": 90 + i * 5, "systolic": None, "diastolic": None,
             "weight_kg": None, "sleep_hours": None, "exercise_minutes": None, "stress_level": None} for i in range(6)]
    s = analysis.summarize(recs)
    assert s["metrics"]["glucose"]["trend"] == "rising" and s["metrics"]["glucose"]["latest"] == 115
    assert len(analysis.build_series(recs, "weekly")["glucose"]["x"]) == 6


def test_ml_estimate_handles_missing_and_valid_input():
    assert ml_service.estimate_diabetes_risk(None, 80, 25, 30)["available"] is False
    if ml_service.is_available():
        low = ml_service.estimate_diabetes_risk(85, 66, 22, 25)
        high = ml_service.estimate_diabetes_risk(190, 90, 40, 55)
        assert high["probability"] > low["probability"]


def test_pdf_is_generated():
    pdf = report_service.build_pdf({"full_name": "Test User", "age": 30, "height_cm": 170, "bmi": 23, "health_goal": None},
                                   30, {"metrics": {}}, [], [], {"available": False, "reason": "n/a"})
    assert pdf.startswith(b"%PDF")
