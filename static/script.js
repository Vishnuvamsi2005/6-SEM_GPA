
const calculateButton = document.getElementById("calculateBtn");
const resetButton = document.getElementById("resetBtn");
const downloadButton = document.getElementById("downloadBtn");

const nameInput = document.getElementById("name");
const registerInput = document.getElementById("registerNo");
const resultSection = document.getElementById("result");
const messageElement = document.getElementById("message");
const gpaElement = document.getElementById("gpaValue");

calculateButton.addEventListener("click", calculateGPA);
resetButton.addEventListener("click", resetCalculator);
downloadButton.addEventListener("click", downloadReport);

// Hide an old result when the student changes any input.
nameInput.addEventListener("input", invalidateResult);
registerInput.addEventListener("input", invalidateResult);

document.querySelectorAll(".grade").forEach((element) => {
    element.addEventListener("change", invalidateResult);
});

function invalidateResult() {
    resultSection.classList.add("hidden");
    downloadButton.classList.add("hidden");
}

function collectFormData() {
    const name = nameInput.value.trim();
    const registerNo = registerInput.value.trim();
    const grades = {};

    if (!name) {
        alert("Please enter the student's name.");
        nameInput.focus();
        return null;
    }

    const gradeElements = document.querySelectorAll(".grade");

    for (const element of gradeElements) {
        const subject = element.dataset.subject;
        const grade = element.value;

        if (!grade) {
            alert(`Please select a grade for ${subject}.`);
            element.focus();
            return null;
        }

        grades[subject] = grade;
    }

    return {
        name: name,
        register_no: registerNo,
        grades: grades
    };
}

async function calculateGPA() {
    const payload = collectFormData();

    if (!payload) {
        return;
    }

    calculateButton.disabled = true;
    calculateButton.textContent = "Calculating...";

    try {
        const response = await fetch("/calculate", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (!response.ok || !result.success) {
            alert(result.message || "Unable to calculate GPA.");
            return;
        }

        messageElement.textContent =
            `Semester result prepared for ${result.name}.`;

        gpaElement.textContent = Number(result.gpa).toFixed(2);

        resultSection.classList.remove("hidden");
        downloadButton.classList.remove("hidden");

    } catch (error) {
        console.error("GPA calculation error:", error);

        alert(
            "Unable to connect to the server. Please try again."
        );

    } finally {
        calculateButton.disabled = false;
        calculateButton.textContent = "Calculate GPA";
    }
}

async function downloadReport() {
    const payload = collectFormData();

    if (!payload) {
        return;
    }

    downloadButton.disabled = true;
    downloadButton.textContent = "Preparing PDF...";

    try {
        const response = await fetch("/download-report", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            let message = "Unable to generate the PDF report.";

            try {
                const errorData = await response.json();
                message = errorData.message || message;
            } catch (error) {
                console.error("Could not read server error:", error);
            }

            alert(message);
            return;
        }

        const pdfBlob = await response.blob();

        // Confirm that the server returned a PDF.
        if (pdfBlob.type !== "application/pdf") {
            alert("The server did not return a valid PDF file.");
            return;
        }

        const url = URL.createObjectURL(pdfBlob);
        const link = document.createElement("a");

        const safeName = payload.name
            .replace(/[^a-z0-9]+/gi, "-")
            .replace(/^-+|-+$/g, "")
            .toLowerCase() || "student";

        link.href = url;
        link.download = `${safeName}_semester_grade_report.pdf`;

        document.body.appendChild(link);
        link.click();
        link.remove();

        // Release the temporary download URL after the browser uses it.
        setTimeout(() => URL.revokeObjectURL(url), 1000);

    } catch (error) {
        console.error("PDF download error:", error);

        alert(
            "Could not download the PDF. Please check your connection and try again."
        );

    } finally {
        downloadButton.disabled = false;
        downloadButton.textContent = "Download PDF Report";
    }
}

function resetCalculator() {
    nameInput.value = "";
    registerInput.value = "";

    document.querySelectorAll(".grade").forEach((element) => {
        element.value = "";
    });

    resultSection.classList.add("hidden");
    downloadButton.classList.add("hidden");

    gpaElement.textContent = "0.00";
    messageElement.textContent = "";

    calculateButton.disabled = false;
    calculateButton.textContent = "Calculate GPA";

    nameInput.focus();
}
