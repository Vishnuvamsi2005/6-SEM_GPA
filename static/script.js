const calculateButton = document.getElementById("calculateBtn");
const resetButton = document.getElementById("resetBtn");

calculateButton.addEventListener("click", calculateGPA);
resetButton.addEventListener("click", resetCalculator);

async function calculateGPA() {
    const name = document.getElementById("name").value.trim();

    if (name === "") {
        alert("Please enter your name.");
        return;
    }

    const gradeElements = document.querySelectorAll(".grade");
    const grades = {};

    for (const element of gradeElements) {
        const subject = element.dataset.subject;
        const grade = element.value;

        if (grade === "") {
            alert("Please select a grade for all subjects.");
            return;
        }

        grades[subject] = grade;
    }

    try {
        const response = await fetch("/calculate", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                name: name,
                grades: grades
            })
        });

        const result = await response.json();

        if (!result.success) {
            alert(result.message);
            return;
        }

        document.getElementById("message").textContent =
            `Congratulations "${result.name}"!`;

        document.getElementById("gpaValue").textContent =
            result.gpa.toFixed(2);

        document.getElementById("result").classList.remove("hidden");

    } catch (error) {
        alert("Unable to connect to the server. Make sure Flask is running.");
        console.error(error);
    }
}

function resetCalculator() {
    document.getElementById("name").value = "";

    document.querySelectorAll(".grade").forEach(grade => {
        grade.value = "";
    });

    document.getElementById("result").classList.add("hidden");
}
