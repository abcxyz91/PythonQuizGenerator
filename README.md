# **PYTHON QUIZ GENERATOR MADE IN PYTHON**

## Web Demo: [Link](https://abcxyz91.pythonanywhere.com/)

## Purpose:
As a total beginner, the amount of knowledge I received by taking this course in my spare time while maintaining my full time job is enormous. I feel like I forget something if I don't practice coding even for just one day. Therefore, I want to write a small webapp that's like Duolingo, but for an amateur programmer like me to review what I have learned.

## Tools that I used:
In this small webapp, I use mainly Python with Flask framework and SQLite (still with the help of cs50 library) for backend.
For frontend, I use HTML, CSS (bootstrap) and a tiny bit of JavaScript (still not confident about JS).

## Functions:
### database
First and foremost, I designed a database with several tables that are suitable for my project. Planning is the most important, right?

In users table, it contains id, username, hash and number of streak day. id is an primary autoincrement integer value, while username is an unique text value.

In questions table, I have id, question_text and category.

In answers table, I have id, question_id, answer_text and is_correct column. question_id is a foreign key that link to id in questions table, and is_correct is a boolean value to know which answer is the correct one.

Finally, user_progress that track user progress (obviously!) including which questions already answered and correct or not.

### helpers.py
In this, I prepare some functions that I use repeatedly in my main app (@login_required, get_username, get_category)
Also, some complicated functions I also wrote in here to improve readability and maintenance later.

For get_questions() and get_answers(), I use ORDER BY RANDOM query and random.shuffle method to randomize the order of questions and order of answers inside, without changing the id associated to them.

For upload_file() function, I realized that open() only works with FilePath object, while uploaded file is a File object, which is in binary, and need to use TextIOWrapper() from io library to convert into text. I made my questionaire in excel and saved in CSV file, and it causes a huge error that only with the help of ChatGPT, I can fix it. It is due to Excel inserted some hidden characters onto the header and with encoding='utf-8-sig', problem solved. Amazing AI! After that, using DictReader to read and loop through each key and insert value into questions and answers database.

I also use datatime library to get actual date, convert it between date format and text format, as well as calculating number of consecutive testing day.

### index.html (or Home)
Show user performance and number of streak day.

Because questions database has column for category, I can extract them, and let user choose which kind of test category they want to take, or they can test regardless of category.

For now, only registered user can take test. I don't know why I thought this is good idea at the beginning. For next version, I will maybe slightly modify my code to allow guest to take test.

### test.html & result.html
This is the proud of my project. I helped me learn a lot abour data structures.

First, with GET method, based on user chosen category, it will show the questions and answers accordingly. They are stored in a list called "quiz". "quiz" is a list of dictionary. Each of its elements included 2 key-value pairs, "question" and "answers". The value of key "questions" is another dictionary with key-value pairs of id, question_text. On the other hands, the value of key "answers" is actually a list of 4 dictionaries containing the id, answer_text, is_correct key-value pairs of 4 options.

Below is an example of quiz data structure:
```
quiz = [
    {
        "question": {"id": 1, "question_text": "What is a function in Python?"},
        "answers": [
            {"id": 1, "answer_text": "A block of reusable code", "is_correct": True},
            {"id": 2, "answer_text": "A data structure", "is_correct": False},
            {"id": 3, "answer_text": "A control flow structure", "is_correct": False},
            {"id": 4, "answer_text": "A debugging tool", "is_correct": False}
        ]
    },
    {
        "question": {"id": 2, "question_text": "What is a list in Python?"},
        "answers": [
            {"id": 5, "answer_text": "An ordered collection", "is_correct": True},
            {"id": 6, "answer_text": "A debugging tool", "is_correct": False},
            {"id": 7, "answer_text": "A control flow structure", "is_correct": False},
            {"id": 8, "answer_text": "A function", "is_correct": False}
        ]
    }
]
```

"quiz" then, is shown on test.html with a basic for loop in Jinja2 syntax. Each answer is a radio option for user to choose.

And then, "quiz" will be stored in session, in order to reuse again in "POST" method. The reason because each time user start a quiz, it will create another randomized quiz, so I have to store the quiz content of the last test.

Next, about "POST" method. The idea is when user select all the answers and submit, the request.form will record the question_id (in "name" attribute) and answer_id (in "value" attribute) in a dictionary. With that data, I can loop through each question, get the user answer, check if it is correct or not by compare the id with the database. Whether the answer is right or wrong, I update it in the user_progress table.

Below is the data structure of request.form:
```
request.form = {
    '1': '3',  # The user selected answer with ID 3 for question with ID 1
    '2': '5'   # The user selected answer with ID 6 for question with ID 2
}
```

In order to prompt user to answer all questions before submit, or warn user when they are trying to navigate outside of test.html, I use a few lines of JavaScript in test.html. I use addEventListener and unloadWarning to do this. I have to say I need to use Google and a lot of ChatGpt to write this function down. After all, JavaScript is barely mentioned in CS50 Week 8 though.

In result.html, originally, I only show number of questions answered and how many is correct. However, it is kind of useless when you dont know which question you answered wrong, right? So I create another list of dictionary, called "results". In the above for loop, after each question, I will record the question_test, answer_text, user_answer_id, correct_answer_id.

The data structure of results will be like:
```
results = [
    {
        "question_text": "What is a function in Python?",  # The question
        "answers": [  # A list of possible answers
            {"id": 1, "answer_text": "A block of reusable code"},       # Answer 1
            {"id": 2, "answer_text": "A data structure"},               # Answer 2
            {"id": 3, "answer_text": "A control flow structure"},       # Answer 3
            {"id": 4, "answer_text": "A debugging tool"},               # Answer 4
        ],
        "user_answer_id": 3,
        "correct_answer_id": 1
    },
    {
        "question_text": "What is a list in Python?",
        "answers": [
            {"id": 5, "answer_text": "An ordered collection"},           # Answer 1
            {"id": 6, "answer_text": "A debugging tool"},                # Answer 2
            {"id": 7, "answer_text": "A control flow structure"},        # Answer 3
            {"id": 8, "answer_text": "A function"},                      # Answer 4
        ],
        "user_answer_id": 5,
        "correct_answer_id": 5
    }
]
```

Again, the results list is shown on result.html, almost similar like test.html but with a little twist. I want to print out the quiz again, but highlight answer the user has chosen for each question. If the user's answer is correct, highlight in blue, but if user's answer is incorrect, highlight in red, and highlight the correct answer in blue. I learnt that I can create a jinja2 conditional check within a html tag (in this case is within <li></li>). Maybe with just color is not enough, I add another small badge to shout out "correct" or "incorrect" next to it.

### upload.html
I use request.files to check user input, then using upload_file() function in helpers.py to register data on the database
upload_file() function also validate data in the csv file before insert into the database, and show how many successfully inserts.

The structure of the csv is quite strict, so for now, it is mainly for me to bulk upload questions and answers.

However, the validating check I feel like it is not good enough though...

### Login, Register, Change password, History
Almost same as the Finance pset in week 9, nothing special. Username and password (in hash form) will be stored in users database. I use SQL to insert, compare and update username and password (in hash form) for login, register or change password.

For history, I use a SQL query to group the data in day, count total questions answered and total corrects

I still use the login_required and after_request decorator of the Finance pset in my project. Honestly, I still dont really understand what does the after_request do. Moreover, I still use cs50 training wheels for SQL queries...

### CSS
Very basic bootstrap layout with additinal styling in styles.css for button, progress bar, table, list of questions and answers...

I found this online source very helpful to learn: https://www.w3schools.com/css/default.asp

### Question bank
I use NotebookLM to summarize and generate quizzes, based on the content of Python Crash Course by Eric Matthes.

## To Do Next:
Here is a list of things I would like to implement further:
* Allow guest or unregistered user to take test.
* Allow user to select how many questions they would like to take. Now I hard code 10 questions.
* Review and improve the uploaded csv data validating.
* Show all questions and answers in the bank and allow user to edit.
* Counting user quiz time.
* (Maybe) Rewrite all SQL queries without relying on cs50 library.

## Summary
This Python Quiz Generator is a web-based application built to help beginner programmers, like me, reinforce their learning through randomized, self-paced quizzes. It uses Flask, SQLite, and Bootstrap for an interactive experience that tracks user performance and streaks. The app's features include a dynamic quiz system, user history, and CSV uploads for adding new questions. While it already offers a solid review tool, the next version will expand its flexibility by allowing guest access, customizable quiz lengths, and better data validation.
