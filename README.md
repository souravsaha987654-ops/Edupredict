# EduPredict AI
**AI-Driven Student Performance Prediction & Academic Analytics System**

A Flask web app that guides a student (or parent) step by step: sign in -> profile -> short questionnaire ->
AI-predicted exam score with plain-language explanations -> PDF report -> Gemini-powered mock interviews.

---
## 1. Folder structure
```
edupredict/
├── app.py                  Flask app: all pages and API routes
├── config.py               Questionnaire, profile options, paths
├── requirements.txt        Python packages
├── .env.example            Copy to .env and add your Gemini key
├── data/StudentPerformance.csv     Your dataset (CSV)
├── models/best_algo.joblib         Your saved model (kept as-is)
├── ml/
│   ├── train.py            Trains & compares algorithms, saves the best
│   └── predictor.py        Loads the model, predicts, explains, builds action plan
├── services/
│   ├── gemini.py           Gemini API: interview questions + answer evaluation
│   └── report.py           PDF report (reportlab)
├── templates/              HTML pages (Jinja2)
└── static/css, static/js   Design system and small scripts
```

## 2. Set up in VS Code (step by step)
1. Install **Python 3.10 or newer** (python.org) and **VS Code** with the *Python* extension.
2. VS Code -> **File > Open Folder** -> choose the `edupredict` folder.
3. Open the terminal: **Terminal > New Terminal**.
4. Create and activate a virtual environment:
   - Windows: `python -m venv venv` then `venv\Scripts\activate`
   - Mac/Linux: `python3 -m venv venv` then `source venv/bin/activate`
5. In VS Code press **Ctrl+Shift+P** -> *Python: Select Interpreter* -> pick the one inside `venv`.
6. Install packages: `pip install -r requirements.txt`
7. Get a free Gemini key at https://aistudio.google.com/apikey . Copy `.env.example` to `.env` and paste the key:
   ```
   GEMINI_API_KEY=your-real-key
   GEMINI_MODEL=gemini-2.5-flash
   SECRET_KEY=any-long-random-text
   ```
   If Google has retired that model name, open AI Studio, pick a current Flash model and put its name in `GEMINI_MODEL`.
8. **(Recommended) Train and compare the algorithms:** `python ml/train.py`
   This prints a comparison table, saves the best algorithm to `models/best_algo.joblib`
   (your original file is backed up as `best_algo_original.joblib`) and fills the table on the *How it works* page.
9. Run the app: `python app.py` and open **http://127.0.0.1:5000**

> Without a Gemini key the app still works: the mock interview switches to "practice mode" with template questions.
> If your saved model was made with different library versions, the app automatically trains a fresh one on first start.

## 3. How the project works (use this to explain to teachers)
1. **Sign in & profile** - role (student/parent), class or year, field of study and a target score.
2. **Guided questionnaire** - 4 colourful steps collect the 18 factors from the dataset (study hours, attendance, previous scores, motivation, parental involvement, resources, tutoring, internet, family income, teacher quality and more).
3. **Data preparation** (`ml/train.py`) - missing values imputed, numbers scaled, text categories one-hot encoded, all inside one scikit-learn `Pipeline`, so the exact same steps run in training and prediction.
4. **Algorithm comparison** - Linear Regression, Ridge, Decision Tree, Random Forest, Gradient Boosting and XGBoost are trained on 80% of the data and tested on the unseen 20% (R², MAE, RMSE and 5-fold cross-validation). The best one is saved as `best_algo.joblib`.
5. **Prediction and explanation** (`ml/predictor.py`) - the model predicts the exam score. To explain it, each factor is reset to the *typical* student value and the model is asked again: the difference is that factor's impact (what-if analysis, works with any algorithm). The action plan tests realistic improvements the same way (e.g. +5 study hours, +10% attendance).
6. **Report** - score ring, what is working, what needs attention, action plan, parent summary and a downloadable **PDF**.
7. **AI mock interview** (`services/gemini.py`) - the student pastes syllabus topics; Gemini writes one exam-style question per topic, then scores each answer out of 10 with feedback and key points. A summary shows the weakest topic.
8. **Fairness & privacy** - gender is never used by the model (training drops it; prediction uses one fixed value). Data is kept only in server memory for the session.

## 4. Likely questions from teachers
- **Why regression, not classification?** Exam score is a continuous number.
- **Why is the best algorithm chosen on unseen data?** To avoid overfitting; cross-validation confirms the result.
- **How can you trust the explanation?** It uses the model itself with what-if tests; gains are estimates, not guarantees.
- **What are the limits?** The dataset is public and generalised; predictions are guidance, not guarantees.
- **Future scope:** database for history, teacher dashboard, regional languages, voice interviews.

## 5. Troubleshooting
| Problem | Fix |
|---|---|
| `ModuleNotFoundError` | Virtual environment not active, or `pip install -r requirements.txt` not run |
| Saved model error / version warnings | Harmless. The app retrains automatically, or run `python ml/train.py` |
| `xgboost` fails to install | Remove it from requirements.txt; everything else still works |
| Interview says "practice mode" | `.env` missing/incorrect, or restart the app after editing it |
| Port already in use | Change the last line of `app.py` to `app.run(debug=True, port=5001)` |
