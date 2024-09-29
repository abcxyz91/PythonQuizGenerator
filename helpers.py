import io
import random
import csv
from cs50 import SQL
from flask import redirect, render_template, session
from datetime import datetime
from functools import wraps

db = SQL("sqlite:///bank.db")

def error(message, code=400):
    # Render error message to user
    return render_template("error.html", top=code, bottom=message), code


def login_required(func):
    # Decorate routes to require login
    @wraps(func)
    # To accept any arguments that might be passed to the original function
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return func(*args, **kwargs)
    return decorated_function


def streak_day(id):
    # Return user progress
    rows = db.execute("SELECT date_answered FROM user_progress WHERE user_id = ? GROUP BY date_answered ORDER BY date_answered DESC", session["user_id"])

    # Change the date in text to date object and store in a list
    dates = []
    for row in rows:
        dates.append(datetime.strptime(row["date_answered"], '%Y-%m-%d'))

    if not dates:
        return 0

    # Counting number of consecutive day starting from the latest date
    streak = 1
    for i in range(len(dates) - 1):
        if (dates[i] - dates[i + 1]).days == 1:
            streak += 1
        else:
            break
    return streak


def get_user_name(id):
    # Return user_name from session id
    rows = db.execute("SELECT username FROM users WHERE id = ?", id)
    if len(rows) != 1:
        return error("User not exist", 403)
    else:
        username = rows[0]["username"]
        return username


def get_category():
    # Show list of question category to choose from and add 1 more category named All
    rows = db.execute("SELECT category FROM questions GROUP BY category")
    categories = []

    for row in rows:
        categories.append(row["category"])

    categories.append("All")
    return categories


def get_questions(category):
    # Show a list of randomize questions based on category user choose
    if category == "All":
        questions = db.execute("SELECT * FROM questions ORDER BY RANDOM() LIMIT 10")
    else:
        questions = db.execute("SELECT * FROM questions WHERE category = ? ORDER BY RANDOM() LIMIT 10", category)
    return questions


def get_answers(question_id):
    # Show a list of randomize answers based on questions_id
    """ shuffle() only change the order of the list, not changing the id """
    answers = db.execute("SELECT * FROM answers WHERE question_id = ?", question_id)
    random.shuffle(answers)
    return answers


def upload_file(csv_file):
    # Wrap the binary file stream as a text stream with UTF-8 encoding, and remove hidden characters in csv file
    """ Because open() only handle FilePath Object, while uploaded file is FileObject in binary, need to use TextIOWrapper to change back to text """
    stream = io.TextIOWrapper(csv_file.stream, encoding='utf-8-sig')
    reader = csv.DictReader(stream)

    total_questions = 0
    uploaded = 0

    for row in reader:
        total_questions += 1
        # Question id will be in the first column, next is question text & category, then next 4 columns are answers
        """ With DictReader, each row is a dict """
        id = row["id"]
        question = row["question_text"]
        category = row["category"]
        answers = [row["answer_1"], row["answer_2"], row["answer_3"], row["answer_4"]]
        correct = int(row["correct_answer"])

        # Validate the content:
        if question != "" and category != "" and len(answers) == 4 and 0 < correct < 5:

            # Insert question
            db.execute("INSERT OR IGNORE into questions (id, question_text, category) VALUES (?, ?, ?)", id, question, category)

            # Insert answers
            for i, answer in enumerate(answers):
                db.execute("INSERT OR IGNORE into answers (question_id, answer_text, is_correct) VALUES (?, ?, ?)",
                            id, answer, int(i + 1 == correct))

            # Update number of question uploaded succesfully:
            uploaded += 1
    uploaded_ratio = uploaded / total_questions * 100
    return f"{uploaded_ratio:.2f}"
