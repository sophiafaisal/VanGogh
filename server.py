import random
import json
import re
from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your-secret-key'

cleared_session = False

with open('paintings_data.json') as f:
    paintings = json.load(f)

# @app.route('/')
# def home():
#     return render_template('homepage.html')

@app.route('/learn')
def learn():
    visited = session.get('learn_entry_times', {})
    return render_template('learn.html', visited=visited)

@app.route('/learn/<int:lesson_num>', methods=['GET', 'POST'])
def learn_lesson(lesson_num):
    if 1 <= lesson_num <= len(paintings):
        data = paintings[lesson_num - 1]
        title = data["title"]
        now = datetime.now()

        entry_times = session.get('learn_entry_times', {})
        exit_times = session.get('learn_exit_times', {})
        titles = session.get('learn_titles', {})
        reflections = session.get('reflections', {})
        last_lesson = session.get('last_lesson')

        current_key = str(lesson_num)

        #Set exit time only if previous entry time exists and is BEFORE now
        if last_lesson and last_lesson != current_key:
            if last_lesson in entry_times and last_lesson not in exit_times:
                prev_entry = datetime.fromisoformat(entry_times[last_lesson])
                if now > prev_entry:
                    exit_times[last_lesson] = now.isoformat()
                    session['learn_exit_times'] = exit_times

        #Set current entry time only if not already stored
        entry_times[current_key] = now.isoformat()
        session['learn_entry_times'] = entry_times

        #Update title and last lesson pointer
        titles[current_key] = title
        session['learn_titles'] = titles
        session['last_lesson'] = current_key

        #Handle reflection
        if request.method == 'POST':
            user_input = request.form.get('reflection', '').strip()
            reflections[current_key] = user_input
            session['reflections'] = reflections

        reflection = reflections.get(current_key, "")
        return render_template('learn_lesson.html', data=data, lesson_num=lesson_num, reflection=reflection)

@app.route('/quiz')
def quiz_intro():
    session.pop('answers', None)  #clears selected answers
    return render_template('quiz.html', question_num=0)

@app.route('/quiz/<int:question_num>', methods=['GET', 'POST'])
def quiz_question(question_num):
    correct_answers = {
        1: "Yellow",
        2: "Orange",
        3: "It reflected the colours used by major Dutch artists at this period of time.",
        4: "The Irises",
        5: "He felt the night was so much more alive than the daytime."
    }

    correct_answer_text = {
        1: "Yellow",
        2: "Orange",
        3: "It reflected the colours used by major Dutch artists at this period of time.",
        4: "The Irises",
        5: "He felt the night was so much more alive than the daytime."
    }

    feedback = None
    show_modal = False
    correct = correct_answer_text.get(question_num, "")

    answers = session.get('answers', {})

    if request.method == 'POST':
        selected = request.form.get('answer')
        answers[str(question_num)] = selected
        session['answers'] = answers
        session.modified = True

        correct_expected = correct_answers.get(question_num)
        if selected and selected.lower() == correct_expected.lower():
            feedback = "Correct!"
            show_modal = False
        else:
            feedback = "Incorrect!"
            show_modal = True

    selected = answers.get(str(question_num))
    return render_template(
        'quiz.html',
        question_num=question_num,
        selected=selected,
        feedback=feedback,
        show_modal=show_modal,
        correct=correct
    )


@app.route('/quiz/results', methods=['GET', 'POST'])
def quiz_results():
    correct_answers = {
        1: "Yellow",
        2: "Orange",
        3: "It reflected the colours used by major Dutch artists at this period of time.",
        4: "The Irises",
        5: "He felt the night was so much more alive than the daytime."
    }
    answers = session.get('answers', {})
    score = 0
    incorrect = []

    for qnum, correct in correct_answers.items():
        selected = answers.get(str(qnum))
        if selected and selected.lower() == correct.lower():
            score += 1
        else:
            incorrect.append({
                "question": qnum,
                "your_answer": selected or "No answer",
                "correct_answer": correct
            })



    total_questions = len(correct_answers)

    correct_answers_str_keys = {str(k): v for k, v in correct_answers.items()}
    return render_template(
        "quiz_results.html",
        score=score,
        total=total_questions,
        incorrect=incorrect,
        answers=answers,
        correct_answers=correct_answers_str_keys
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
    exit_times = session.get('learn_exit_times', {})
    titles = session.get('learn_titles', {})
    reflections = session.get('reflections', {})

    lesson_data = []
    for lesson, entry_time_str in entry_times.items():
        entry_dt = datetime.fromisoformat(entry_time_str)
        # ✅ Use fallback if no exit time exists
        exit_dt = datetime.fromisoformat(exit_times.get(lesson)) if lesson in exit_times else entry_dt
        duration = exit_dt - entry_dt
        if duration.total_seconds() < 0:
            duration = timedelta(0)

        formatted_entry = entry_dt.strftime("%B %d, %Y at %I:%M %p")
        lesson_data.append({
            "lesson": lesson,
            "title": titles.get(lesson, "Unknown"),
            "entry": formatted_entry,
            "duration": str(duration).split('.')[0],  # remove microseconds
            "reflection": reflections.get(lesson, "")
        })

    return render_template('my_activity.html', lesson_data=lesson_data)

@app.route('/')
def home():
    return render_template('homepage.html')

@app.route('/record_exit', methods=['POST'])
def record_exit():
    data = request.get_json()
    lesson = str(data.get('lesson'))

    if not lesson:
        return '', 400

    exit_times = session.get('learn_exit_times', {})
    exit_times[lesson] = datetime.now().isoformat()
    session['learn_exit_times'] = exit_times

    print(f"Recorded exit time for lesson {lesson} at {exit_times[lesson]}")
    return '', 204


if __name__ == '__main__':
    app.run(debug=True, port=5001)
