from flask import Flask, render_template, request, send_file
from resume_ranker import rank_resumes
import csv
import io


app = Flask(__name__)


# Store the latest ranking results
latest_results = []


@app.route("/", methods=["GET", "POST"])
def home():

    global latest_results

    if request.method == "POST":

        # Get job description
        job_description = request.form.get(
            "job_description",
            ""
        ).strip()

        # Get uploaded resumes
        uploaded_files = request.files.getlist(
            "resumes"
        )

        # Check job description
        if not job_description:
            return render_template(
                "index.html",
                error="Please enter a job description."
            )

        # Remove empty file selections
        valid_files = []

        for file in uploaded_files:

            if file and file.filename:
                valid_files.append(file)

        # Check resumes
        if not valid_files:
            return render_template(
                "index.html",
                error="Please upload at least one PDF resume."
            )

        # Prepare files for ranking
        resume_data = []

        for file in valid_files:

            if not file.filename.lower().endswith(".pdf"):
                continue

            file_bytes = file.read()

            resume_data.append(
                (file.filename, file_bytes)
            )

        if not resume_data:
            return render_template(
                "index.html",
                error="Please upload PDF resume files only."
            )

        # Rank resumes
        latest_results = rank_resumes(
            job_description,
            resume_data
        )

        if not latest_results:
            return render_template(
                "index.html",
                error="Could not extract text from the uploaded resumes."
            )

        return render_template(
            "result.html",
            results=latest_results
        )

    return render_template("index.html")


@app.route("/download")
def download():

    global latest_results

    if not latest_results:
        return "No ranking results available."

    # Create CSV in memory
    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "Rank",
        "Resume",
        "Score",
        "Status"
    ])

    for rank, item in enumerate(
        latest_results,
        start=1
    ):

        writer.writerow([
            rank,
            item["name"],
            item["score"],
            item["status"]
        ])

    # Convert CSV text to bytes
    csv_data = io.BytesIO(
        output.getvalue().encode("utf-8")
    )

    csv_data.seek(0)

    return send_file(
        csv_data,
        mimetype="text/csv",
        as_attachment=True,
        download_name="resume_ranking_report.csv"
    )


if __name__ == "__main__":
    app.run(debug=True)