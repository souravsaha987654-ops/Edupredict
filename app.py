"""EduPredict AI - Flask application."""
import os, json, uuid
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify
from dotenv import load_dotenv

load_dotenv()
import config as cfg
from ml.predictor import Predictor
from services import gemini, report

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")
predictor = Predictor()
STORE = {}   # in-memory data per signed-in session (a database can replace this later)


def me():
    sid = session.get("sid")
    return STORE.setdefault(sid, {}) if sid else {}


def signed_in(f):
    @wraps(f)
    def w(*a, **k):
        if "sid" not in session:
            return redirect(url_for("welcome"))
        return f(*a, **k)
    return w


def has_profile(f):
    @wraps(f)
    @signed_in
    def w(*a, **k):
        if "profile" not in me():
            return redirect(url_for("onboarding"))
        return f(*a, **k)
    return w


@app.context_processor
def inject():
    return dict(profile=me().get("profile"), signed=("sid" in session))


@app.route("/")
def welcome():
    if "sid" in session and "profile" in me():
        return redirect(url_for("home"))
    return render_template("welcome.html")


@app.post("/login")
def login():
    session["sid"] = uuid.uuid4().hex
    STORE[session["sid"]] = dict(email=request.form.get("email", "guest"))
    return redirect(url_for("onboarding"))


@app.route("/onboarding", methods=["GET", "POST"])
@signed_in
def onboarding():
    if request.method == "POST":
        f = request.form
        level = f.get("level") if f.get("level") in cfg.LEVELS else "College"
        L = cfg.LEVELS[level]
        year = f.get("year") if f.get("year") in L["years"] else L["years"][2]
        stream = f.get("stream") if f.get("stream") in L["streams"] else L["streams"][0]
        try:
            target = max(50, min(100, int(f.get("target", 80))))
        except ValueError:
            target = 80
        me()["profile"] = dict(role="Parent" if f.get("role") == "Parent" else "Student", name=(f.get("name") or "Student").strip()[:40],
                               level=level, year=year, stream=stream, target=target)
        return redirect(url_for("home"))
    return render_template("onboarding.html", levels=cfg.LEVELS, p=me().get("profile"))


@app.route("/home")
@has_profile
def home():
    return render_template("home.html", result=me().get("result"))


@app.route("/check", methods=["GET", "POST"])
@has_profile
def check():
    if request.method == "POST":
        ans = cfg.parse_answers(request.form)
        me()["result"] = predictor.analyse(ans, me()["profile"])
        return redirect(url_for("result"))
    return render_template("check.html", steps=cfg.STEPS, last=(me().get("result") or {}).get("answers"))


@app.route("/result")
@has_profile
def result():
    r = me().get("result")
    return render_template("result.html", r=r) if r else redirect(url_for("check"))


@app.route("/report.pdf")
@has_profile
def report_pdf():
    r = me().get("result")
    if not r:
        return redirect(url_for("check"))
    name = me()["profile"]["name"].replace(" ", "_")
    return send_file(report.build_pdf(me()["profile"], r), mimetype="application/pdf", download_name=f"EduPredict_Report_{name}.pdf")


@app.route("/interview")
@has_profile
def interview():
    p = me()["profile"]
    ai = bool(os.getenv("GEMINI_API_KEY", "").strip()) and not os.getenv("GEMINI_API_KEY", "").startswith("paste")
    return render_template("interview.html", syllabus=cfg.SYLLABUS.get(p["stream"], ""), ai=ai)


@app.post("/api/interview/questions")
@has_profile
def api_questions():
    d = request.get_json(silent=True) or {}
    topics = [str(t).strip()[:120] for t in d.get("topics", []) if str(t).strip()][:6]
    if not topics:
        return jsonify(error="Please add at least one topic."), 400
    p = me()["profile"]
    diff = d.get("difficulty") if d.get("difficulty") in ("Easy", "Medium", "Hard") else "Medium"
    qs, src = gemini.make_questions(topics, p["level"], p["year"], p["stream"], diff)
    return jsonify(questions=qs, source=src)


@app.post("/api/interview/evaluate")
@has_profile
def api_evaluate():
    d = request.get_json(silent=True) or {}
    answer = str(d.get("answer", "")).strip()
    if not answer:
        return jsonify(error="Please type an answer."), 400
    return jsonify(gemini.evaluate(str(d.get("topic", ""))[:120], str(d.get("question", ""))[:500], answer))


@app.route("/how")
@signed_in
def how():
    m = json.loads(cfg.METRICS_PATH.read_text()) if cfg.METRICS_PATH.exists() else None
    return render_template("how.html", m=m, model_name=type(predictor.model.steps[-1][1]).__name__ if hasattr(predictor.model, "steps") else "Model")


@app.route("/logout")
def logout():
    STORE.pop(session.get("sid"), None)
    session.clear()
    return redirect(url_for("welcome"))


if __name__ == "__main__":
    app.run(debug=True)
