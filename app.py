
from io import BytesIO
from datetime import datetime
from html import escape
import re
import unicodedata

from flask import (
    Flask, render_template, request, jsonify, send_file
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable
)

app = Flask(__name__)

GRADE_POINTS = {
    "H": 10,
    "S": 9,
    "A": 8,
    "B": 7,
    "C": 6,
    "F": 0
}

subjects = {
    "EML[EBAI22004]": 3,
    "UI&UX[EBAI22006]": 3,
    "MINI PROJECT[EBAI22I01]": 1,
    "UI&UX LAB[EBAI22L03]": 1,
    "SOFT SKILL[EBCC22I07]": 1,
    "OOSE[EBCS22009]": 3,
    "PROGRAM ELECTIVE[EBCS22E(08/09/11/14)]": 3,
    "TECHNICAL SKILL[EBCC22I03]": 1,
    "OOSE LAB[EBCS22L07]": 1,
    "OPEN ELECTIVE[EBXX22OEX]": 3
}

TOTAL_CREDITS = sum(subjects.values())


def validate_student_data():
    data = request.get_json(silent=True) or {}

    if not isinstance(data, dict):
        return None, "Invalid request data."

    name = str(data.get("name", "")).strip()
    register_no = str(data.get("register_no", "")).strip()
    grades = data.get("grades", {})

    if not name:
        return None, "Please enter the student's name."
    
    if not register_no:
        return None, "Please enter the student's register number."

    if len(register_no) > 30:
        return None, "Register number must be 30 characters or fewer."

    if not isinstance(grades, dict):
        return None, "Invalid grade data."

    rows = []
    weighted_total = 0

    for subject, credits in subjects.items():
        grade = grades.get(subject)

        if grade not in GRADE_POINTS:
            return None, f"Please select a valid grade for {subject}."

        grade_point = GRADE_POINTS[grade]
        weighted_points = grade_point * credits
        weighted_total += weighted_points

        # Split "SUBJECT TITLE[SUBJECT CODE]" into separate columns.
        if "[" in subject and subject.endswith("]"):
            title, code = subject.rsplit("[", 1)
            code = code[:-1]
        else:
            title, code = subject, ""

        rows.append({
            "title": title.strip(),
            "code": code,
            "credits": credits,
            "grade": grade,
            "grade_point": grade_point,
            "weighted_points": weighted_points
        })

    gpa = round(weighted_total / TOTAL_CREDITS, 2)

    return {
        "name": name,
        "register_no": register_no,
        "rows": rows,
        "total_credits": TOTAL_CREDITS,
        "weighted_total": weighted_total,
        "gpa": gpa
    }, None


def safe_filename(name):
    normalized = (
        unicodedata.normalize("NFKD", name)
        .encode("ascii", "ignore")
        .decode()
    )
    slug = re.sub(r"[^A-Za-z0-9]+", "-", normalized)
    slug = slug.strip("-").lower()
    return slug or "student"


def draw_footer(canvas, doc):
    canvas.saveState()

    page_width, _ = A4
    canvas.setStrokeColor(colors.HexColor("#CBD5E1"))
    canvas.setLineWidth(0.6)
    canvas.line(
        18 * mm, 15 * mm,
        page_width - 18 * mm, 15 * mm
    )

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#64748B"))
    canvas.drawString(
        18 * mm, 10 * mm,
        "Unofficial student-generated report"
    )
    canvas.drawRightString(
        page_width - 18 * mm, 10 * mm,
        f"Page {doc.page}"
    )

    canvas.restoreState()


def create_report_pdf(data):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=21 * mm,
        title="6th Semester GPA Report",
        author="6th Semester GPA Calculator"
    )

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="ReportTitleCustom",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#172554"),
        spaceAfter=3 * mm
    ))

    styles.add(ParagraphStyle(
        name="ReportSubtitleCustom",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#475569"),
        spaceAfter=2 * mm
    ))

    styles.add(ParagraphStyle(
        name="ReportSectionCustom",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#1E3A8A"),
        spaceBefore=4 * mm,
        spaceAfter=2 * mm
    ))

    styles.add(ParagraphStyle(
        name="ReportCellCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5
    ))

    styles.add(ParagraphStyle(
        name="ReportCellBoldCustom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5
    ))

    styles.add(ParagraphStyle(
        name="ReportLabelCustom",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#64748B")
    ))

    styles.add(ParagraphStyle(
        name="ReportValueCustom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#0F172A")
    ))

    story = []

    story.append(Paragraph(
        "6TH SEMESTER GPA REPORT",
        styles["ReportTitleCustom"]
    ))

    story.append(Paragraph(
        "B.Tech - Computer Science and Engineering "
        "(Artificial Intelligence)",
        styles["ReportSubtitleCustom"]
    ))

    story.append(Paragraph(
        "UNOFFICIAL STUDENT-GENERATED ACADEMIC SUMMARY",
        styles["ReportSubtitleCustom"]
    ))

    story.append(Spacer(1, 3 * mm))

    story.append(HRFlowable(
        width="100%",
        thickness=1.2,
        color=colors.HexColor("#334155")
    ))

    story.append(Paragraph(
        "STUDENT DETAILS",
        styles["ReportSectionCustom"]
    ))

    name = escape(data["name"])
    register_no = (
        escape(data["register_no"])
        if data["register_no"]
        else "Not provided"
    )
    report_date = datetime.now().strftime("%d %B %Y")

    metadata = [
        [
            Paragraph("Student Name", styles["ReportLabelCustom"]),
            Paragraph("Register Number", styles["ReportLabelCustom"]),
            Paragraph("Semester", styles["ReportLabelCustom"])
        ],
        [
            Paragraph(name, styles["ReportValueCustom"]),
            Paragraph(register_no, styles["ReportValueCustom"]),
            Paragraph("6th Semester", styles["ReportValueCustom"])
        ],
        [
            Paragraph("Degree / Branch", styles["ReportLabelCustom"]),
            Paragraph("Report Generated", styles["ReportLabelCustom"]),
            Paragraph("Calculation Method", styles["ReportLabelCustom"])
        ],
        [
            Paragraph("B.Tech CSE (AI)", styles["ReportValueCustom"]),
            Paragraph(report_date, styles["ReportValueCustom"]),
            Paragraph("Credit-weighted GPA", styles["ReportValueCustom"])
        ]
    ]

    metadata_table = Table(
        metadata,
        colWidths=[58 * mm, 58 * mm, 58 * mm]
    )

    metadata_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1),
         colors.HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 0.7,
         colors.HexColor("#CBD5E1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4,
         colors.HexColor("#E2E8F0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6)
    ]))

    story.append(metadata_table)

    story.append(Paragraph(
        "SUBJECT-WISE GRADE DETAILS",
        styles["ReportSectionCustom"]
    ))

    cell = styles["ReportCellCustom"]
    bold_cell = styles["ReportCellBoldCustom"]

    table_data = [[
        Paragraph("S.No.", bold_cell),
        Paragraph("Subject Title / Code", bold_cell),
        Paragraph("Credits", bold_cell),
        Paragraph("Grade", bold_cell),
        Paragraph("Grade Point", bold_cell),
        Paragraph("Credit x Point", bold_cell)
    ]]

    for index, row in enumerate(data["rows"], start=1):
        subject_text = escape(row["title"])

        if row["code"]:
            subject_text += (
                '<br/><font color="#64748B" size="7">'
                + escape(row["code"])
                + "</font>"
            )

        table_data.append([
            Paragraph(str(index), cell),
            Paragraph(subject_text, cell),
            Paragraph(str(row["credits"]), cell),
            Paragraph(row["grade"], bold_cell),
            Paragraph(str(row["grade_point"]), cell),
            Paragraph(str(row["weighted_points"]), cell)
        ])

    table_data.append([
        Paragraph("", cell),
        Paragraph("TOTAL", bold_cell),
        Paragraph(str(data["total_credits"]), bold_cell),
        Paragraph("", cell),
        Paragraph("", cell),
        Paragraph(str(data["weighted_total"]), bold_cell)
    ])

    grade_table = Table(
        table_data,
        colWidths=[
            12 * mm, 77 * mm, 19 * mm,
            17 * mm, 25 * mm, 24 * mm
        ],
        repeatRows=1,
        hAlign="LEFT"
    )

    grade_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0),
         colors.HexColor("#1E3A8A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.7,
         colors.HexColor("#94A3B8")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4,
         colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2),
         [colors.white, colors.HexColor("#F8FAFC")]),
        ("BACKGROUND", (0, -1), (-1, -1),
         colors.HexColor("#E2E8F0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 1), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6)
    ]))

    story.append(grade_table)

    story.append(Paragraph(
        "SEMESTER SUMMARY",
        styles["ReportSectionCustom"]
    ))

    summary_data = [
        [
            Paragraph("TOTAL CREDITS", styles["ReportLabelCustom"]),
            Paragraph("TOTAL CREDIT POINTS", styles["ReportLabelCustom"]),
            Paragraph("SEMESTER GPA", styles["ReportLabelCustom"])
        ],
        [
            Paragraph(
                str(data["total_credits"]),
                ParagraphStyle(
                    "TotalCreditsNumber",
                    parent=styles["ReportValueCustom"],
                    fontSize=14
                )
            ),
            Paragraph(
                str(data["weighted_total"]),
                ParagraphStyle(
                    "WeightedPointsNumber",
                    parent=styles["ReportValueCustom"],
                    fontSize=14
                )
            ),
            Paragraph(
                f'{data["gpa"]:.2f}',
                ParagraphStyle(
                    "SemesterGPANumber",
                    parent=styles["ReportValueCustom"],
                    fontSize=18,
                    textColor=colors.HexColor("#166534")
                )
            )
        ]
    ]

    summary_table = Table(
        summary_data,
        colWidths=[58 * mm, 58 * mm, 58 * mm]
    )

    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1),
         colors.HexColor("#F0FDF4")),
        ("BOX", (0, 0), (-1, -1), 0.8,
         colors.HexColor("#86EFAC")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5,
         colors.HexColor("#BBF7D0")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8)
    ]))

    story.append(summary_table)
    story.append(Spacer(1, 4 * mm))

    story.append(Paragraph(
        "GPA = sum of (grade point x subject credits) / total credits. "
        "This report is generated from the grades entered by the user. "
        "It is not an official university-issued grade card.",
        ParagraphStyle(
            "ReportDisclaimer",
            parent=styles["Normal"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#64748B"),
            alignment=TA_LEFT
        )
    ))

    doc.build(
        story,
        onFirstPage=draw_footer,
        onLaterPages=draw_footer
    )

    buffer.seek(0)
    return buffer


@app.route("/")
def home():
    return render_template("index.html", subjects=subjects)


@app.route("/calculate", methods=["POST"])
def calculate():
    data, error = validate_student_data()

    if error:
        return jsonify({
            "success": False,
            "message": error
        }), 400

    return jsonify({
        "success": True,
        "name": data["name"],
        "gpa": data["gpa"],
        "total_credits": data["total_credits"]
    })


@app.route("/download-report", methods=["POST"])
def download_report():
    data, error = validate_student_data()

    if error:
        return jsonify({
            "success": False,
            "message": error
        }), 400

    pdf_buffer = create_report_pdf(data)
    filename = (
        f'{safe_filename(data["name"])}_semester_gpa_report.pdf'
    )

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename
    )


if __name__ == "__main__":
    app.run(debug=True)
