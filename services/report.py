"""Builds the downloadable PDF report for parents/students (reportlab)."""
import io, datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

INK, VIOLET, MUTED = colors.HexColor("#1d1a3b"), colors.HexColor("#6d4aff"), colors.HexColor("#6b6b8d")
STATUS = {"green": "#16a34a", "violet": "#6d4aff", "coral": "#ff6b4a"}


def build_pdf(profile, r):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.6 * cm, bottomMargin=1.6 * cm,
                            title="EduPredict AI Performance Report")
    st = lambda **k: ParagraphStyle("x", fontName=k.pop("font", "Helvetica"), textColor=k.pop("color", INK), **k)
    H1, H2 = st(font="Helvetica-Bold", fontSize=22, leading=26), st(font="Helvetica-Bold", fontSize=13, leading=17, spaceBefore=14, spaceAfter=6, color=VIOLET)
    P, SM = st(fontSize=10.5, leading=15), st(fontSize=8.5, leading=12, color=MUTED)
    col = colors.HexColor(STATUS.get(r["status"]["color"], "#6d4aff"))
    e = []
    e += [Paragraph("EduPredict AI", st(font="Helvetica-Bold", fontSize=11, color=VIOLET)),
          Paragraph("Student Performance Report", H1),
          Paragraph(f"Generated on {datetime.date.today():%d %B %Y}", SM), Spacer(1, 10)]

    info = [["Name", profile.get("name", "")], ["Profile", f"{profile.get('role', '')} | {profile.get('level', '')} - {profile.get('year', '')}"],
            ["Field of study", profile.get("stream", "")], ["Target score", f"{r['target']}%"]]
    t = Table(info, colWidths=[4 * cm, 13 * cm])
    t.setStyle(TableStyle([("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 10),
                           ("TEXTCOLOR", (0, 0), (0, -1), MUTED), ("LINEBELOW", (0, 0), (-1, -1), .4, colors.HexColor("#e6e8f2")),
                           ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    e += [t, Spacer(1, 14)]

    gap = r["gap"]
    msg = f"{gap} marks to reach the {r['target']}% goal" if gap > 0 else "Goal reached or exceeded"
    box = Table([[Paragraph(f"<font size=40 color='{col.hexval()}'><b>{r['score']}</b></font><font size=14 color='#6b6b8d'> / 100</font>", P),
                  [Paragraph(f"<b>{r['status']['label']}</b>", st(font="Helvetica-Bold", fontSize=16, leading=20, color=col)),
                   Paragraph(r["status"]["sub"] + ". " + msg + ".", P)]]], colWidths=[6 * cm, 11 * cm])
    box.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f4f2ff")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                             ("LEFTPADDING", (0, 0), (-1, -1), 16), ("TOPPADDING", (0, 0), (-1, -1), 14), ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
                             ("LINEBEFORE", (0, 0), (0, -1), 4, col)]))
    e += [Paragraph("Predicted exam score", H2), box]

    def block(title, rows, fmt):
        e.append(Paragraph(title, H2))
        e.extend(Paragraph("&bull; " + fmt(x), P) for x in rows) if rows else e.append(Paragraph("Nothing significant here.", P))

    block("What is working well", r["strengths"], lambda x: f"<b>{x['label']}</b> (you: {x['you']}, typical: {x['typical']}) adds about +{x['impact']} marks")
    block("Needs attention", r["concerns"], lambda x: f"<b>{x['label']}</b> (you: {x['you']}, typical: {x['typical']}) costs about {x['impact']} marks")
    block("Action plan", r["plan"], lambda x: f"<b>{x['text']}</b> - estimated +{x['gain']} marks")
    e.append(Paragraph("Summary for parents", H2))
    e.append(Paragraph(r["parent_summary"], P))
    e += [Spacer(1, 18), Paragraph("This report is an AI estimate based on patterns in 6,606 student records. It is a guide for improvement, not a guarantee of results.", SM)]
    doc.build(e)
    buf.seek(0)
    return buf
