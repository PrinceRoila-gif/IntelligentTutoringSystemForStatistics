from flask import Flask, request, render_template, redirect, url_for, session
from owlready2 import get_ontology, Thing, DatatypeProperty
import statistics
import random

app = Flask(__name__)
app.secret_key = "secret_key"  # Required for session management

# Load the ontology
ontology_path = "student_ontology.owl"
onto = get_ontology(ontology_path).load()

# Define the Student and User classes
with onto:
    class Student(Thing):
        pass

    class User(Student):  # User is now a subclass of Student
        pass

    class name(DatatypeProperty):
        domain = [Student]
        range = [str]

    class answered_questions(DatatypeProperty):
        domain = [User]
        range = [int]

# Function to check for duplicate names
def is_duplicate_name(student_name):
    existing_students = onto.User.instances()  # Fetch instances from the User subclass
    for student in existing_students:
        if student.name.lower() == student_name.lower():
            return True
    return False

# Home Page (Start Here)
@app.route("/")
def home():
    return render_template("home.html")

# Register Page
@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        student_name = request.form.get("student_name").strip()
        if not student_name:
            error = "Please enter a valid name!"
        elif is_duplicate_name(student_name):
            error = f"The name '{student_name}' already exists. Please use a different name."
        else:
            with onto:
                new_user = onto.User()  # Create an instance of the User class
                new_user.name = student_name
            onto.save(file=ontology_path, format="rdfxml")
            return redirect(url_for("login"))
    return render_template("register.html", error=error)

# Login Page
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        student_name = request.form.get("student_name").strip()
        if not student_name:
            error = "Please enter your name!"
        elif not is_duplicate_name(student_name):
            error = f"The name '{student_name}' is not registered. Please register first."
        else:
            session['student_name'] = student_name
            return redirect(url_for("statistics_input"))
    return render_template("login.html", error=error)

# Statistics Calculation Page
@app.route("/statistics", methods=["GET", "POST"])
def statistics_input():
    student_name = session.get('student_name', 'Student')
    result = None
    if request.method == "POST":
        try:
            numbers = request.form.get("numbers")
            number_list = [float(x) for x in numbers.split(",")]

            mean = statistics.mean(number_list)
            median = statistics.median(number_list)
            mode = statistics.mode(number_list)

            result = {
                "mean": mean,
                "median": median,
                "mode": mode,
                "numbers": number_list
            }
        except ValueError:
            result = {"error": "Invalid input. Please enter numbers separated by commas."}
        except statistics.StatisticsError:
            result = {"error": "No unique mode found for the given numbers."}

    return render_template("statistics_input.html", student_name=student_name, result=result)

# Practice Quiz Page
@app.route("/practice", methods=["GET", "POST"])
def practice():
    student_name = session.get('student_name', 'Student')

    # Store the question and answer in session to persist data between requests
    if 'question_data' not in session or request.method == "GET":
        session['question_data'] = generate_question()

    question_data = session['question_data']
    feedback = None
    selected_answer = None

    if request.method == "POST":
        # Get the user's selected answer
        selected_answer = request.form.get("answer")
        correct_answer = question_data['answer']

        # Check if the selected answer is correct
        if selected_answer is not None:
            try:
                selected_answer = float(selected_answer)
                if selected_answer == correct_answer:
                    feedback = "Correct! 🎉"
                else:
                    feedback = f"Incorrect. 😞 The correct answer is {correct_answer}."
            except ValueError:
                feedback = f"Invalid input. The correct answer is {correct_answer}."

          

        # Generate a new question when 'Next Question' is clicked
        if "next_question" in request.form:
            session['question_data'] = generate_question()
            return redirect(url_for("practice"))

    return render_template("practice.html", student_name=student_name, question=question_data, feedback=feedback, selected_answer=selected_answer)

def generate_question():
    nums = [random.randint(1, 20) for _ in range(5)]
    mean = round(statistics.mean(nums), 2)
    median = statistics.median(nums)
    try:
        mode = statistics.mode(nums)
    except statistics.StatisticsError:
        mode = "No mode"

    question_type = random.choice(["mean", "median", "mode"])
    if question_type == "mean":
        correct_answer = mean
        question_text = f"What is the mean of the numbers: {nums}?"
    elif question_type == "median":
        correct_answer = median
        question_text = f"What is the median of the numbers: {nums}?"
    else:
        correct_answer = mode
        question_text = f"What is the mode of the numbers: {nums}?"

    options = [correct_answer, correct_answer + 1, correct_answer - 1, random.randint(1, 20)]
    random.shuffle(options)

    return {
        "question": question_text,
        "options": options,
        "answer": correct_answer
    }

# Theory Page
@app.route("/theory")
def theory():
    return render_template("theory.html")

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=9090)
