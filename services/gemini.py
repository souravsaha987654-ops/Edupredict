"""Gemini integration for the AI mock interview.

Uses Google's REST API directly (only the 'requests' library is needed).
If no API key is set, or a call fails, a built-in practice mode keeps the app working.
"""
import os, re, json
import requests

URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _call(prompt):
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key or key.startswith("paste"):
        raise RuntimeError("GEMINI_API_KEY is not set")
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.6, "responseMimeType": "application/json"}}
    r = requests.post(URL.format(model=model), json=body, timeout=45,
                      headers={"x-goog-api-key": key, "Content-Type": "application/json"})
    r.raise_for_status()
    text = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    text = re.sub(r"^```(?:json)?|```$", "", text).strip()
    return json.loads(text)


def make_questions(topics, level, year, stream, difficulty):
    prompt = (
        f"You are a friendly, expert examiner. A {level} student ({year}, field: {stream}) is preparing for exams.\n"
        f"Difficulty: {difficulty}. For EACH topic below write exactly ONE clear exam-style interview question "
        "that tests understanding, in simple English.\n"
        f"Topics: {json.dumps(topics)}\n"
        'Return ONLY a JSON array like [{"topic": "...", "question": "..."}] in the same order as the topics.')
    try:
        data = _call(prompt)
        qs = [dict(topic=str(d["topic"])[:120], question=str(d["question"])[:500]) for d in data][:len(topics)]
        if qs:
            return qs, "gemini"
    except Exception as e:
        print("[Gemini] question generation failed:", e)
    templates = [
        'Explain "{t}" in your own words, as if teaching a friend.',
        'What are the key points you must remember about "{t}"?',
        'Give a real-life example of "{t}".',
        'What mistakes do students often make in "{t}"?',
    ]
    return [dict(topic=t, question=templates[i % 4].format(t=t)) for i, t in enumerate(topics)], "practice"


def evaluate(topic, question, answer):
    prompt = (
        "You are a kind but honest examiner marking a student's spoken-style answer.\n"
        f"Topic: {topic}\nQuestion: {question}\nStudent answer: {answer[:2000]}\n"
        'Return ONLY JSON: {"score": <integer 0-10>, "feedback": "<two short encouraging sentences>", '
        '"tip": "<one concrete way to improve>", "key_points": ["<up to 3 points a full answer should include>"]}')
    try:
        d = _call(prompt)
        return dict(score=max(0, min(10, int(d.get("score", 5)))), feedback=str(d.get("feedback", ""))[:400],
                    tip=str(d.get("tip", ""))[:300], key_points=[str(x)[:160] for x in d.get("key_points", [])][:3],
                    source="gemini")
    except Exception as e:
        print("[Gemini] evaluation failed:", e)
    words = len(answer.split())
    kws = [w for w in re.split(r"\W+", topic.lower()) if len(w) > 3]
    hit = sum(1 for w in kws if w in answer.lower())
    score = min(10, round(min(words, 60) / 12 + (hit / len(kws) * 3 if kws else 2) + 1))
    return dict(score=score, source="practice", key_points=[],
                feedback="Your answer is short. Add a definition and one example." if words < 25 else "Good depth! Tie it to an example to make it exam-ready.",
                tip="Add your Gemini API key to get detailed, topic-specific feedback.")
