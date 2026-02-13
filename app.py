import os
from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from datetime import datetime

# ------------------ APP SETUP ------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'

# Ensure instance folder exists for SQLite DB
if not os.path.exists('instance'):
    os.makedirs('instance')

# Database & Uploads
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/forum.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Ensure uploads folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db = SQLAlchemy(app)

# ------------------ LOGIN ------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ------------------ MODELS ------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))  # ⚠️ Hash passwords in production!

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    image = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ------------------ CREATE TABLES ------------------
with app.app_context():
    db.create_all()

# ------------------ ROUTES ------------------
@app.route('/')
def index():
    posts = Post.query.order_by(Post.date.desc()).all()
    return render_template("index.html", posts=posts)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        if username and password:
            existing = User.query.filter_by(username=username).first()
            if not existing:
                new_user = User(username=username, password=password)
                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for('login'))
    return render_template("register.html")

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('index'))
    return render_template("login.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/create', methods=['GET','POST'])
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title'].strip()
        content = request.form['content'].strip()
        file = request.files.get('image')

        filename = None
        if file and file.filename != "":
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_post = Post(
            title=title,
            content=content,
            image=filename,
            user_id=current_user.id
        )
        db.session.add(new_post)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template("create.html")

# ------------------ RUN ------------------
if __name__ == '__main__':
    app.run(debug=True)
