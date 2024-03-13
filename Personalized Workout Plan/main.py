from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
import logging
from flasgger import Swagger

app = Flask(__name__)
Swagger(app)

app.secret_key = 'your_secret_key'

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Define User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)


# Define Note model
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)


# Define Rating model
class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)

    def __repr__(self):
        return f"Rating(user_id={self.user_id}, rating={self.rating})"


# Routes
@app.route('/')
def index():
    """
    Home page
    ---
    responses:
      200:
        description: A welcome message
    """
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Register endpoint
    ---
    post:
      parameters:
        - in: formData
          name: username
          type: string
          required: true
          description: The username of the user
        - in: formData
          name: email
          type: string
          required: true
          description: The email address of the user
        - in: formData
          name: password
          type: string
          required: true
          description: The password of the user
      responses:
        200:
          description: Redirects to login page if registration is successful
        409:
          description: Error message if username or email already exists
    """
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        try:
            user = User(username=username, email=email, password=password)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('login'))
        except IntegrityError:
            return render_template('register.html', error='Username or email already exists')
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login endpoint
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')


@app.route('/logout')
def logout():
    """
    Logout endpoint
    """
    session.clear()
    return redirect(url_for('index'))


@app.route('/dashboard')
def dashboard():
    """
    Dashboard endpoint
    """
    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)
        if user:
            return render_template('home.html', username=user.username)
    return redirect(url_for('login'))


@app.route('/button', methods=['POST'])
def button():
    """
    Button endpoint
    """
    if request.method == 'POST':
        gender = request.form['gender']
        age = request.form['age']
        session['age'] = age  # Store age in session
        session['gender'] = gender  # Store gender in session
        if request.form.get('personalExercise'):
            return redirect(url_for('personal'))
        elif request.form.get('challenge'):
            return redirect(url_for('challenge'))
        else:
            return redirect(url_for('show_button', gender=gender, age=age))
    else:
        return redirect(url_for('index'))


@app.route('/show_button/<gender>/<age>')
def show_button(gender, age):
    """
    Show button endpoint
    """
    return render_template('button.html', gender=gender, age=age)


@app.route('/personal', methods=['GET', 'POST'])
def personal():
    """
    Personal endpoint
    """
    if request.method == 'POST':
        weight = float(request.form['weight'])
        height = float(request.form['height']) / 100  # Convert height to meters
        bmi = weight / (height * height)
        if bmi < 18.5:
            result = 'Underweight'
            advice = (
                "It seems you are underweight. It's important to maintain a balanced diet rich in nutrients and consider consulting with a healthcare professional for personalized advice.\n"
                "Underweight:\n"
                "Strength training: Focus on building muscle mass with exercises like squats, lunges, and push-ups.\n"
                "Resistance training: Use resistance bands or weights to increase muscle strength and endurance.\n"
                "Aerobic exercises: Incorporate cardio activities such as brisk walking, cycling, or swimming to improve overall fitness levels.")
        elif 18.5 <= bmi < 25:
            result = 'Normal'
            advice = (
                "Congratulations! Your BMI falls within the normal range. Maintain a healthy lifestyle by eating a balanced diet and exercising regularly.\n"
                "Cardiovascular exercises: Continue with aerobic activities like running, jogging, or dancing to maintain cardiovascular health.\n"
                "Strength training: Include weightlifting or bodyweight exercises to maintain muscle tone and strength.\n"
                "Flexibility exercises: Practice yoga or stretching routines to enhance flexibility and reduce the risk of injury.")
        elif 25 <= bmi < 30:
            result = 'Overweight'
            advice = (
                "It seems you are overweight. Consider adopting healthier eating habits, incorporating regular physical activity, and consulting with a healthcare professional for guidance.\n"
                "Low-impact cardio: Opt for activities like walking, cycling, or using an elliptical machine to minimize stress on the joints while still burning calories.\n"
                "Water aerobics: Try swimming or water aerobics, which provide a full-body workout with less impact on the joints.\n"
                "Interval training: Incorporate high-intensity interval training (HIIT) to boost metabolism and burn fat effectively in shorter workout sessions.")
        else:
            result = 'Obesity'
            advice = (
                "It appears you have obesity. It's essential to focus on lifestyle changes such as improving your diet, increasing physical activity, and seeking guidance from a healthcare provider for personalized support.")
        return render_template('personal.html', age=session.get('age', '25'), gender=session.get('gender', 'male'),
                               result=result, advice=advice)

    age_str = session.get('age', '25')  # Default value if not found in session
    gender = session.get('gender', 'male')  # Default value if not found in session
    age = int(age_str)  # Convert age to integer

    special_message = None

    # Special message logic based on age and gender
    if gender == 'male':
        if 18 <= age <= 35:
            special_message = "You are a young male adult."
        elif age > 35:
            special_message = "You are an older male adult."
        # Add more conditions as needed for different age ranges and genders

    return render_template('personal.html', age=age, gender=gender, special_message=special_message)


@app.route('/note', methods=['GET', 'POST'])
def note():
    """
    Note endpoint
    ---
    get:
      responses:
        200:
          description: Returns all notes
    post:
      parameters:
        - in: formData
          name: note
          type: string
          required: true
          description: The content of the note
      responses:
        200:
          description: Note added successfully
    """
    if request.method == 'POST':
        content = request.form['note']
        note = Note(content=content)
        db.session.add(note)
        db.session.commit()
        logging.info(f"New note inserted: {content}")

    # Fetch all notes from the database
    notes = Note.query.all()

    # Render the home.html template with the notes
    return render_template('note.html', notes=notes)


@app.route('/delete_note/<int:note_id>', methods=['GET'])
def delete_note(note_id):
    """
    Delete note endpoint
    ---
    parameters:
      - in: path
        name: note_id
        type: integer
        required: true
        description: The ID of the note to be deleted
    responses:
      200:
        description: Note deleted successfully
      404:
        description: Note not found
    """
    note = Note.query.get_or_404(note_id)
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for('note'))


@app.route('/challenge')
def challenge():
    """
    Challenge endpoint
    """
    return render_template('challenge.html')


@app.route('/save_rating', methods=['POST'])
def save_rating():
    """
    Save rating endpoint
    ---
    post:
      parameters:
        - in: formData
          name: rating
          type: integer
          required: true
          description: The rating given by the user
        - in: formData
          name: comment
          type: string
          description: Optional comment provided by the user
      responses:
        200:
          description: Rating and comment saved successfully
        401:
          description: User not logged in
    """
    data = request.form  # Use request.form to access form data
    user_id = session.get('user_id')
    rating = data.get('rating')
    comment = data.get('comment')

    if user_id:
        new_rating = Rating(user_id=user_id, rating=rating, comment=comment)
        db.session.add(new_rating)
        db.session.commit()
        logging.info(f"New rating inserted: Rating={rating}, Comment={comment}")
        return jsonify({'message': 'Rating and comment saved successfully', 'comment': comment}), 200
    else:
        return jsonify({'error': 'User not logged in'}), 401


@app.route('/comments')
def comments():
    """
    Comments endpoint
    ---
    responses:
      200:
        description: Returns all comments with ratings
    """
    # Fetch comments from the database
    comments = Rating.query.filter(Rating.comment.isnot(None)).all()
    return render_template('comments.html', comments=comments)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
