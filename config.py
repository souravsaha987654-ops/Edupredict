"""Central configuration: paths, questionnaire, profile options."""
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA_PATH = BASE / "data" / "StudentPerformance.csv"
MODEL_PATH = BASE / "models" / "best_algo.joblib"
METRICS_PATH = BASE / "models" / "metrics.json"

LMH = ["Low", "Medium", "High"]
YN = ["No", "Yes"]


def S(k, label, mn, mx, default, unit="", hint=""):
    return dict(k=k, label=label, t="slider", min=mn, max=mx, default=default, unit=unit, hint=hint)


def C(k, label, options, default):
    return dict(k=k, label=label, t="choice", options=options, default=default)


# The guided questionnaire (4 short steps). Keys match the dataset columns.
STEPS = [
    dict(id="habits", title="Study habits", emoji="📚", color="violet", sub="How you study every week", q=[
        S("Hours_Studied", "How many hours do you study each week?", 1, 44, 20, " hrs", "Include homework and self-study"),
        S("Attendance", "What is your class attendance?", 60, 100, 80, "%", "Roughly, across all subjects"),
        S("Previous_Scores", "What did you score in your last exams?", 50, 100, 75, "%", "Your most recent result"),
        S("Sleep_Hours", "How many hours do you sleep each night?", 4, 10, 7, " hrs"),
    ]),
    dict(id="support", title="Support & motivation", emoji="💪", color="coral", sub="The people and tools behind you", q=[
        C("Motivation_Level", "How motivated do you feel about studies?", LMH, "Medium"),
        C("Parental_Involvement", "How involved are your parents in your studies?", LMH, "Medium"),
        C("Access_to_Resources", "Do you have books, notes and study material?", LMH, "Medium"),
        S("Tutoring_Sessions", "Extra tutoring classes per month", 0, 8, 1, "", "0 if you do not take any"),
    ]),
    dict(id="home", title="Home & school", emoji="🏠", color="teal", sub="Your surroundings", q=[
        C("Internet_Access", "Do you have internet at home?", YN, "Yes"),
        C("Family_Income", "Family income level", LMH, "Medium"),
        C("Parental_Education_Level", "Highest education of your parents", ["High School", "College", "Postgraduate"], "High School"),
        C("Distance_from_Home", "How far is your college / school?", ["Near", "Moderate", "Far"], "Near"),
        C("Teacher_Quality", "How would you rate your teachers?", LMH, "Medium"),
        C("Peer_Influence", "Influence of your friends", ["Negative", "Neutral", "Positive"], "Positive"),
    ]),
    dict(id="life", title="Lifestyle", emoji="🌱", color="amber", sub="Balance outside the classroom", q=[
        S("Physical_Activity", "Exercise or sports each week", 0, 6, 3, " hrs"),
        C("Extracurricular_Activities", "Do you take part in clubs or activities?", YN, "Yes"),
        C("Learning_Disabilities", "Any learning difficulty (for example dyslexia)?", YN, "No"),
        C("School_Type", "Type of institution", ["Public", "Private"], "Public"),
    ]),
]

QUESTIONS = {q["k"]: q for s in STEPS for q in s["q"]}
KEYS = list(QUESTIONS)

NAMES = {
    "Hours_Studied": ("Study hours", "⏱️"), "Attendance": ("Attendance", "🏫"), "Previous_Scores": ("Past scores", "🏆"),
    "Sleep_Hours": ("Sleep", "😴"), "Motivation_Level": ("Motivation", "🔥"), "Parental_Involvement": ("Parent involvement", "👪"),
    "Access_to_Resources": ("Study resources", "📖"), "Tutoring_Sessions": ("Tutoring", "👩‍🏫"), "Internet_Access": ("Internet access", "🌐"),
    "Family_Income": ("Family income", "🏡"), "Parental_Education_Level": ("Parents' education", "🎓"),
    "Distance_from_Home": ("Travel distance", "🚌"), "Teacher_Quality": ("Teaching quality", "🍎"), "Peer_Influence": ("Friends' influence", "🤝"),
    "Physical_Activity": ("Physical activity", "⚽"), "Extracurricular_Activities": ("Activities & clubs", "🎭"),
    "Learning_Disabilities": ("Learning difficulty", "🧩"), "School_Type": ("Institution type", "🏫"),
}

LEVELS = {
    "School": dict(years=["Class 8", "Class 9", "Class 10", "Class 11", "Class 12"], streams=["Science", "Commerce", "Arts"]),
    "College": dict(years=["1st year", "2nd year", "3rd year", "4th year"],
                    streams=["Engineering", "Medical", "Commerce / Management", "Arts & Science"]),
}

SYLLABUS = {
    "Engineering": "Normalization in DBMS\nProcess scheduling in operating systems\nDecision trees and random forests\nTCP vs UDP",
    "Medical": "Cell division\nHuman circulatory system\nEnzymes and metabolism",
    "Commerce / Management": "Demand and supply\nBalance sheet basics\nMarketing mix",
    "Arts & Science": "Scientific method\nSocial structures\nStatistics basics",
    "Science": "Newton's laws of motion\nChemical bonding\nPhotosynthesis",
    "Commerce": "Demand and supply\nAccounting equation\nBanking basics",
    "Arts": "French Revolution\nThe Indian Constitution\nGlobalisation",
}


def parse_answers(form):
    """Turn submitted form data into a clean dict (always valid, falls back to defaults)."""
    out = {}
    for k, q in QUESTIONS.items():
        raw = form.get(k)
        if q["t"] == "slider":
            try:
                v = int(float(raw))
            except (TypeError, ValueError):
                v = q["default"]
            out[k] = max(q["min"], min(q["max"], v))
        else:
            out[k] = raw if raw in q["options"] else q["default"]
    return out


def fmt(k, v):
    q = QUESTIONS[k]
    return f"{int(round(float(v)))}{q['unit']}" if q["t"] == "slider" else str(v)
