from datetime import datetime, date
from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import random

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///language_bank.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

LANGUAGES = {
    "İngilizce": [
        ("Hello", "Merhaba", "A1"), ("Good morning", "Günaydın", "A1"),
        ("Thank you", "Teşekkür ederim", "A1"), ("Book", "Kitap", "A1"),
        ("Water", "Su", "A1"), ("Friend", "Arkadaş", "A1"),
        ("Beautiful", "Güzel", "A1"), ("Food", "Yemek", "A1"),
        ("House", "Ev", "A1"), ("School", "Okul", "A1"),
        ("I am learning", "Öğreniyorum", "A2"), ("Where are you?", "Neredesin?", "A2")
    ],
    "Almanca": [
        ("Hallo", "Merhaba", "A1"), ("Danke", "Teşekkürler", "A1"),
        ("Bitte", "Lütfen", "A1"), ("Wasser", "Su", "A1"),
        ("Buch", "Kitap", "A1"), ("Freund", "Arkadaş", "A1"),
        ("Guten Morgen", "Günaydın", "A1"), ("Schule", "Okul", "A1")
    ],
    "Fransızca": [
        ("Bonjour", "Merhaba", "A1"), ("Merci", "Teşekkürler", "A1"),
        ("Eau", "Su", "A1"), ("Livre", "Kitap", "A1"),
        ("Ami", "Arkadaş", "A1"), ("École", "Okul", "A1"),
        ("Bonsoir", "İyi akşamlar", "A1"), ("Maison", "Ev", "A1")
    ],
    "İspanyolca": [
        ("Hola", "Merhaba", "A1"), ("Gracias", "Teşekkürler", "A1"),
        ("Agua", "Su", "A1"), ("Libro", "Kitap", "A1"),
        ("Amigo", "Arkadaş", "A1"), ("Escuela", "Okul", "A1"),
        ("Buenos días", "Günaydın", "A1"), ("Casa", "Ev", "A1")
    ],
    "İtalyanca": [
        ("Ciao", "Merhaba", "A1"), ("Grazie", "Teşekkürler", "A1"),
        ("Acqua", "Su", "A1"), ("Libro", "Kitap", "A1"),
        ("Amico", "Arkadaş", "A1"), ("Scuola", "Okul", "A1")
    ],
    "Japonca": [
        ("こんにちは", "Merhaba", "A1"), ("ありがとう", "Teşekkürler", "A1"),
        ("水", "Su", "A1"), ("本", "Kitap", "A1"),
        ("友達", "Arkadaş", "A1"), ("学校", "Okul", "A1")
    ],
    "Korece": [
        ("안녕하세요", "Merhaba", "A1"), ("감사합니다", "Teşekkürler", "A1"),
        ("물", "Su", "A1"), ("책", "Kitap", "A1"),
        ("친구", "Arkadaş", "A1"), ("학교", "Okul", "A1")
    ]
}

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    language = db.Column(db.String(40), default="İngilizce")
    xp = db.Column(db.Integer, default=0)
    lessons_done = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)
    streak = db.Column(db.Integer, default=0)
    last_study = db.Column(db.String(10), default="")

class LearnedWord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    word = db.Column(db.String(100), nullable=False)
    meaning = db.Column(db.String(100), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("home.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if len(username) < 3 or len(password) < 6 or "@" not in email:
            flash("Kullanıcı adı en az 3, şifre en az 6 karakter olmalı. Geçerli e-posta gir.", "error")
        elif User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Bu kullanıcı adı veya e-posta zaten kayıtlı.", "error")
        else:
            user = User(username=username, email=email, password=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Hesabın hazır! İlk dersine başlayabilirsin.", "success")
            return redirect(url_for("dashboard"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form.get("email", "").strip().lower()).first()
        if user and check_password_hash(user.password, request.form.get("password", "")):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("E-posta veya şifre hatalı.", "error")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

@app.route("/dashboard")
@login_required
def dashboard():
    words = LearnedWord.query.filter_by(user_id=current_user.id).count()
    lessons = [
        {"name": "Temel kelimeler", "desc": "Günlük hayatta kullanılan ilk kelimeler", "number": 1, "level": "A1"},
        {"name": "Selamlaşma", "desc": "Merhaba demeyi ve tanışmayı öğren", "number": 2, "level": "A1"},
        {"name": "Günlük yaşam", "desc": "Ev, okul ve arkadaşlar hakkında konuş", "number": 3, "level": "A1"},
        {"name": "Biraz daha zor", "desc": "Yeni ifadelerle kendini geliştir", "number": 4, "level": "A2"},
    ]
    return render_template("dashboard.html", words=words, lessons=lessons)

@app.route("/language", methods=["POST"])
@login_required
def choose_language():
    language = request.form.get("language")
    if language in LANGUAGES:
        current_user.language = language
        db.session.commit()
        flash("Öğrenme dilin başarıyla kaydedildi!", "success")
    return redirect(url_for("dashboard"))

@app.route("/lesson/<int:lesson_id>", methods=["GET", "POST"])
@login_required
def lesson(lesson_id):
    vocab = LANGUAGES.get(current_user.language, LANGUAGES["İngilizce"])
    if lesson_id < 1 or lesson_id > 4:
        return redirect(url_for("dashboard"))
    pool = vocab[:]
    random.shuffle(pool)
    questions = pool[:min(5, len(pool))]
    index = int(request.args.get("q", 0))
    if index >= len(questions):
        return redirect(url_for("lesson_result"))
    word, meaning, level = questions[index]
    choices = [meaning]
    other_meanings = list({item[1] for item in vocab if item[1] != meaning})
    random.shuffle(other_meanings)
    choices += other_meanings[:3]
    random.shuffle(choices)
    if request.method == "POST":
        answer = request.form.get("answer")
        if answer == meaning:
            current_user.xp += 10
            current_user.correct_answers += 1
            if not LearnedWord.query.filter_by(user_id=current_user.id, word=word).first():
                db.session.add(LearnedWord(user_id=current_user.id, word=word, meaning=meaning))
            flash("Harika! Doğru cevap. +10 XP", "success")
        else:
            flash(f"Doğru cevap: {meaning}. Bir sonraki soruya geçebilirsin.", "error")
        db.session.commit()
        session["lesson_q"] = index + 1
        session["lesson_id"] = lesson_id
        session["lesson_questions"] = questions
        return redirect(url_for("lesson_next"))
    return render_template("lesson.html", word=word, choices=choices, index=index, total=len(questions), lesson_id=lesson_id)

@app.route("/lesson-next")
@login_required
def lesson_next():
    index = session.get("lesson_q", 0)
    lesson_id = session.get("lesson_id", 1)
    questions = session.get("lesson_questions", [])
    if index >= len(questions):
        current_user.lessons_done += 1
        today = date.today().isoformat()
        if current_user.last_study != today:
            current_user.streak += 1
            current_user.last_study = today
        db.session.commit()
        session.pop("lesson_questions", None)
        return redirect(url_for("lesson_result"))
    return redirect(url_for("lesson", lesson_id=lesson_id, q=index))

@app.route("/lesson-result")
@login_required
def lesson_result():
    return render_template("result.html")

@app.route("/review")
@login_required
def review():
    words = LearnedWord.query.filter_by(user_id=current_user.id).order_by(LearnedWord.id.desc()).limit(50).all()
    return render_template("review.html", words=words)

@app.route("/leaderboard")
@login_required
def leaderboard():
    users = User.query.order_by(User.xp.desc()).limit(10).all()
    return render_template("leaderboard.html", users=users)

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True, port=5001)
