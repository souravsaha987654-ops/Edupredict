"""Prediction engine: loads the saved model and explains every prediction.

Works with ANY scikit-learn compatible pipeline (XGBoost, Random Forest, Linear...).
Explanations are model-agnostic "what-if" tests: change one factor, ask the model again.
"""
import numpy as np
import pandas as pd
import joblib
import config as cfg

UP = {"Low": "Medium", "Medium": "High", "High": "High"}
# (key, emoji, advice text, function giving the improved value, condition to suggest it)
SCENARIOS = [
    ("Hours_Studied", "⏱️", "Study 5 more hours a week", lambda v: min(v + 5, 44), lambda v: v < 40),
    ("Attendance", "🏫", "Raise attendance by 10%", lambda v: min(v + 10, 100), lambda v: v < 95),
    ("Tutoring_Sessions", "👩‍🏫", "Add 2 tutoring sessions a month", lambda v: min(v + 2, 8), lambda v: v < 7),
    ("Motivation_Level", "🔥", "Set weekly mini-goals to stay motivated", UP.get, lambda v: v != "High"),
    ("Access_to_Resources", "📖", "Get more notes, books and study material", UP.get, lambda v: v != "High"),
    ("Parental_Involvement", "👪", "Ask parents to check in on studies each week", UP.get, lambda v: v != "High"),
    ("Internet_Access", "🌐", "Arrange reliable internet for study", lambda v: "Yes", lambda v: v == "No"),
]


def status(score):
    if score >= 70:
        return dict(label="Excellent", sub="Doing really well", color="green")
    if score >= 65:
        return dict(label="On track", sub="Steady, healthy progress", color="violet")
    return dict(label="Needs support", sub="A little extra effort will help a lot", color="coral")


class Predictor:
    def __init__(self):
        df = pd.read_csv(cfg.DATA_PATH)
        df = df[df["Exam_Score"] <= 100]
        self.base_cols = [c for c in df.columns if c != "Exam_Score"]
        # typical value of every column: median (numbers) or most common (text)
        self.fill = {c: (df[c].median() if pd.api.types.is_numeric_dtype(df[c]) else df[c].mode()[0]) for c in self.base_cols}
        self.ref = {k: self.fill[k] for k in cfg.KEYS}
        self.model = self._load()
        self.cols = list(getattr(self.model, "feature_names_in_", self.base_cols))

    # -- model loading (auto-retrains if the saved file does not match this machine's library versions)
    def _load(self):
        try:
            m = joblib.load(cfg.MODEL_PATH)
            cols = list(getattr(m, "feature_names_in_", self.base_cols))
            m.predict(self._frame([self.ref], cols))
            print("[EduPredict] Loaded saved model:", type(m.steps[-1][1]).__name__ if hasattr(m, "steps") else type(m).__name__)
            return m
        except Exception as e:
            print(f"[EduPredict] Saved model could not be used ({e!r}). Training a fresh one...")
            from ml import train
            train.run()
            return joblib.load(cfg.MODEL_PATH)

    def _frame(self, rows, cols=None):
        cols = cols or self.cols
        # columns we never ask about (e.g. Gender) get a constant typical value -> they cannot influence a prediction
        return pd.DataFrame([{c: r.get(c, self.fill.get(c)) for c in cols} for r in rows], columns=cols)

    def predict(self, rows):
        return np.clip(self.model.predict(self._frame(rows)), 0, 100)

    # -- full analysis shown on the result page
    def analyse(self, ans, profile):
        base = float(self.predict([ans])[0])
        score = int(round(base))

        # 1) What is helping / hurting: reset one factor to "typical" and see how the prediction moves
        keys = [k for k in cfg.KEYS if ans[k] != self.ref[k]]
        impacts = []
        if keys:
            rows = [{**ans, k: self.ref[k]} for k in keys]
            for k, p in zip(keys, self.predict(rows)):
                impacts.append((k, base - float(p)))

        def card(k, d):
            name, emoji = cfg.NAMES[k]
            return dict(key=k, label=name, emoji=emoji, impact=round(d, 1), you=cfg.fmt(k, ans[k]), typical=cfg.fmt(k, self.ref[k]))

        impacts.sort(key=lambda t: t[1], reverse=True)
        strengths = [card(k, d) for k, d in impacts if d >= 0.25][:3]
        concerns = [card(k, d) for k, d in reversed(impacts) if d <= -0.25][:3]

        # 2) Action plan: test realistic improvements with the model and keep the biggest gains
        scen = [s for s in SCENARIOS if s[4](ans[s[0]])]
        plan = []
        if scen:
            rows = [{**ans, s[0]: s[3](ans[s[0]])} for s in scen]
            for s, p in zip(scen, self.predict(rows)):
                gain = float(p) - base
                if gain >= 0.2:
                    plan.append(dict(emoji=s[1], text=s[2], gain=round(gain, 1)))
        plan = sorted(plan, key=lambda x: x["gain"], reverse=True)[:3]

        st = status(score)
        first = profile.get("name", "The student").split()[0]
        parts = [f"{first} is predicted to score about {score}% ({st['label'].lower()})."]
        parts.append(f"The biggest area to support is {concerns[0]['label'].lower()}." if concerns else "There are no major concerns right now.")
        if plan:
            parts.append(f"The easiest improvement: {plan[0]['text'].lower()}.")
        target = int(profile.get("target", 80))
        return dict(score=score, status=st, strengths=strengths, concerns=concerns, plan=plan,
                    target=target, gap=target - score, parent_summary=" ".join(parts), answers=ans)
