import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import login_required, error, get_user_name, get_category, get_questions, get_answers, upload_file, streak_day

# Config app
app = Flask(__name__)

# Config Session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Config CS50 library to use SQL database
db = SQL("sqlite:///bank.db")

# Create a decorator to run this function after each request is processed, but before the response is sent back to the client.
# To prevent caching of responses and always want the client to fetch the most up-to-date information from the server.
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET"])
@login_required
def index():
    # Get username
    username = get_user_name(session["user_id"])

    # Show list of question category to choose from
    categories = get_category()

    # User reached route via GET (as by clicking a link or via redirect)
    # Show number of questions answered and number of correct in user_progress database
    rows = db.execute("SELECT * FROM user_progress WHERE user_id = ?", session["user_id"])
    questions_answered = 0
    questions_correct = 0

    for row in rows:
        if row["is_answered"] == 1:
            questions_answered += 1
        if row["is_correct"] == 1:
            questions_correct += 1

    # Get number of streak day
    streak = streak_day(session["user_id"])

    # Get the longest streak from database, if today streak is longer, update database
    rows = db.execute("SELECT max_streak FROM users WHERE id = ?", session["user_id"])
    if streak > rows[0]["max_streak"]:
        db.execute("UPDATE users SET max_streak = ? WHERE id = ?", streak, session["user_id"])

    # Check if user had taken test today
    current_time = datetime.now().strftime("%Y-%m-%d")
    rows = db.execute("SELECT date_answered FROM user_progress WHERE user_id = ? ORDER BY date_answered DESC LIMIT 1", session["user_id"])
    if len(rows) != 0:
        latest = rows[0]["date_answered"]
        is_taken_test_today = (current_time == latest)
    else:
        is_taken_test_today = False

    return render_template("index.html", username=username, questions_answered=questions_answered, questions_correct=questions_correct,
                           categories=categories, streak=streak, is_taken_test_today=is_taken_test_today)


@app.route("/test", methods=["GET", "POST"])
@login_required
def test():
    if request.method == "POST":
        # Get username
        username = get_user_name(session["user_id"])

        # Retrieve last quiz from cookie (or session)
        quiz = session.get("quiz")

        # Get the submit data from the request.form
        """ request.form will return a dictionary with key is "name" atrribute and value is "value" atrribute in the HTML form """
        user_answers = request.form

        # Set variable to count questions answered
        correct_answers = 0
        total_questions = len(user_answers)

        # Get current time
        current_time = datetime.now().strftime("%Y-%m-%d")

        # Create a list of dictionary to store question, user answer, correct answer, and correctness
        results = []

        # Loop through each question in quiz
        for item in quiz:
            question_id = item["question"]["id"]
            question_text = item["question"]["question_text"]
            correct_answer_id = None

            # Find correct answer
            rows = db.execute("SELECT * FROM answers WHERE question_id = ? AND is_correct = 1", question_id)
            if rows:
                correct_answer_id = rows[0]["id"]

            # Find user answer
            user_answer_id = int(user_answers[str(question_id)])

            # Check if user answer is correct
            is_correct = (correct_answer_id == user_answer_id)

            # Record into user_progress database
            if is_correct:
                db.execute("INSERT INTO user_progress (user_id, question_id, is_answered, is_correct, date_answered) VALUES (?, ?, ?, ?, ?)",
                            session["user_id"], question_id, 1, 1, current_time)
                correct_answers += 1
            else:
                db.execute("INSERT INTO user_progress (user_id, question_id, is_answered, is_correct, date_answered) VALUES (?, ?, ?, ?, ?)",
                            session["user_id"], question_id, 1, 0, current_time)

            # Record into results dictionary
            results.append({
                "question_text": question_text,
                "answers": item["answers"],
                "user_answer_id": user_answer_id,
                "correct_answer_id": correct_answer_id
            })
        return render_template("result.html", username=username, correct_answers=correct_answers, total_questions=total_questions, results=results)
    else:
        # Show list of question category to choose from
        categories = get_category()

        if request.args.get("category") not in categories:
            return error("Please select a valid category", 400)

        quiz = []
        questions = get_questions(request.args.get("category"))
        for question in questions:
            answers = get_answers(question["id"])  # No need to use int() because id in questions SQL table already an integer
            quiz.append({
                "question": question,
                "answers": answers
            })
        # Store the quiz in session so that it can be used later in result.html
        session["quiz"] = quiz

        return render_template("test.html", quiz=quiz)

@app.route("/history")
@login_required
def history():
    # Get current user all the history
    rows = db.execute("""
                      SELECT date_answered,
                      SUM(is_answered) as total_questions, SUM(is_correct) as correct_answers
                      FROM user_progress WHERE user_id = ?
                      GROUP BY date_answered
                      ORDER BY date_answered DESC
                      """, session["user_id"])
    username = get_user_name(session["user_id"])

    return render_template("/history.html", username=username, history=rows)


@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        # Check if the user has selected a file before uploading
        if "file" not in request.files or request.files["file"].filename == "":
            return error("Please select a file", 400)

        # Get the uploaded file
        file = request.files["file"]

        # Start upload questions into database
        uploaded = upload_file(file)
        return render_template("upload_finish.html", uploaded=uploaded)

    else:
        return render_template("upload.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username, password & confirmation was submitted correctly
        if not request.form.get("username"):
            return error("Invalid username", 400)

        if not request.form.get("password"):
            return error("Invalid password", 400)

        if request.form.get("password") != request.form.get("confirmation"):
            return error("Password not matching")

        # Check if username is existed or not
        username = request.form.get("username")
        hash = generate_password_hash(request.form.get("password"))

        try:
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash)
            flash("Registration sucessfully", "success")
            return redirect("/")
        # Because username is an unique index, will raise ValueError if duplicate
        except ValueError:
            return error("Username already existed", 400)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    session.clear()

    if request.method == "POST":
        if not request.form.get("username"):
            return error("Must input username", 400)

        if not request.form.get("password"):
            return error("Must input password", 400)

        # Check if username existed and password is valid
        username = request.form.get("username")

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return error("Invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        return redirect("/")
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/change", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        if not (request.form.get("password") or request.form.get("new_password") or request.form.get("confirmation")):
            return error("Missing input", 400)

        # Check if old password is correct or not
        rows = db.execute("SELECT * FROM users WHERE username = ?", session["user_id"])
        if not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return error("Password not matching", 400)

        # Check new password is different from old password or not
        if request.form.get("new_password") == request.form.get("password"):
            return error("New password must be different", 400)

        # Confirm new password check
        if request.form.get("new_password") != request.form.get("confirmation"):
            return error("Password not matching", 400)
        else:
            # Update password into database
            hash = generate_password_hash(request.form.get("new_password"))
            db.execute("UPDATE users SET hash = ? WHERE id = ?", hash, session["user_id"])
            flash("Password changed successfully", "success")

        return redirect("/")
    else:
        return render_template("/change.html")


if __name__ == "__main__":
    app.run()
