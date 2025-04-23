import random
import json
import re
from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key'


with open('paintings_data.json') as f:
    paintings = json.load(f)

@app.route('/')
def home():
    return render_template('homepage.html')

@app.route('/learn')
def learn():
    return render_template('learn.html')

@app.route('/learn/<int:lesson_num>')
def learn_lesson(lesson_num):
    if 1 <= lesson_num <= len(paintings):
        data = paintings[lesson_num - 1]
        # Store entry time in session
        entry_times = session.get('learn_entry_times', {})
        entry_times[str(lesson_num)] = datetime.now().isoformat()
        session['learn_entry_times'] = entry_times

        time_visited = session.get('learn_entry_times', {}).get('2')
        if time_visited:
            print("Visited lesson 2 at:", time_visited)

        return render_template('learn_lesson.html', data=data, lesson_num=lesson_num)

@app.route('/quiz')
def quiz_intro():
    session.pop('answers', None)  # ✅ clears selected answers
    return render_template('quiz.html', question_num=0)

@app.route('/quiz/<int:question_num>', methods=['GET', 'POST'])
def quiz_question(question_num):
    if 'answers' not in session:
        session['answers'] = {}

    if request.method == 'POST':
        selected = request.form.get('answer')
        answers = session['answers']
        answers[str(question_num)] = selected
        session['answers'] = answers

        # If this is the last question, go to results
        if question_num == 5:
            return redirect(url_for('quiz_results'))
        else:
            return redirect(url_for('quiz_question', question_num=question_num + 1))

    selected_answer = session['answers'].get(str(question_num))
    return render_template('quiz.html', question_num=question_num, selected=selected_answer)


@app.route('/quiz/results', methods=['GET', 'POST'])
def quiz_results():
    correct_answers = {
        "1": "yellow",
        "2": "orange",
        "3": "a",
        "4": "b",
        "5": "a"
    }
    answers = session.get('answers', {})
    score = 0
    incorrect = []

    for qnum_str, correct in correct_answers.items():
        selected = answers.get(qnum_str)
        if selected == correct:
            score += 1
        else:
            incorrect.append({
                "question": int(qnum_str),
                "your_answer": selected or "No answer",
                "correct_answer": correct
            })

    total_questions = len(correct_answers)

    rendered = render_template(
        "quiz_results.html",
        score=score,
        total=total_questions,
        incorrect=incorrect,
        answers=answers,
        correct_answers=correct_answers
    )

    # Clear after rendering so you don't have leftover data
    session.pop('answers', None)

    return rendered

@app.route('/show_entry_times')
def show_entry_times():
    entry_times = session.get('learn_entry_times', {})
    return f"<pre>{entry_times}</pre>"

@app.route('/my_activity')
def my_activity():
    entry_times = session.get('learn_entry_times', {})
    return render_template('my_activity.html', entry_times=entry_times)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
