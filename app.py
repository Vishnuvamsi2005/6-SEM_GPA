from flask import Flask, render_template, request, jsonify

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

total_credits = sum(subjects.values())

@app.route("/")
def home():
    return render_template("index.html", subjects=subjects)

@app.route("/calculate", methods=["POST"])
def calculate():
    data = request.get_json()
    name = data.get("name", "").strip()
    grades = data.get("grades", {})

    if not name:
        return jsonify({"success": False, "message": "Please enter your name."})

    subjects_sum = 0

    for subject, credits in subjects.items():
        grade = grades.get(subject)

        if grade not in GRADE_POINTS:
            return jsonify({
                "success": False,
                "message": f"Invalid grade for {subject}."
            })

        subjects_sum += GRADE_POINTS[grade] * credits

    gpa = subjects_sum / total_credits

    return jsonify({
        "success": True,
        "name": name,
        "gpa": round(gpa, 2)
    })

if __name__ == "__main__":
    app.run(debug=True)
