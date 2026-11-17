
import os

from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    flash,
    send_from_directory
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user
)
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

# Güvenli SECRET_KEY ayarı
secret_key = os.environ.get("SECRET_KEY")

if not secret_key:
    if os.environ.get("RENDER"):
        raise RuntimeError("SECRET_KEY ortam değişkeni ayarlanmalıdır.")
    secret_key = "development-key-change-before-deployment"

app.config["SECRET_KEY"] = secret_key

# Veritabanı ayarları
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///language_bank.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Giriş sistemi
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Devam etmek için giriş yapmalısın."


# Kullanıcı modeli
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    learning_language = db.Column(
        db.String(50),
        default="Henüz seçilmedi"
    )
    total_points = db.Column(db.Integer, default=0)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Kayıt formu
class RegisterForm(FlaskForm):
    username = StringField(
        "Kullanıcı Adı",
        validators=[DataRequired(), Length(min=3, max=30)]
    )
    email = StringField(
        "E-posta",
        validators=[DataRequired(), Email()]
    )
    password = PasswordField(
        "Şifre",
        validators=[DataRequired(), Length(min=8)]
    )
    confirm_password = PasswordField(
        "Şifre Tekrarı",
        validators=[
            DataRequired(),
            EqualTo("password", message="Şifreler eşleşmiyor.")
        ]
    )
    submit = SubmitField("Kayıt Ol")


# Giriş formu
class LoginForm(FlaskForm):
    email = StringField(
        "E-posta",
        validators=[DataRequired(), Email()]
    )
    password = PasswordField(
        "Şifre",
        validators=[DataRequired()]
    )
    submit = SubmitField("Giriş Yap")


# Dil seçme formu
class LanguageForm(FlaskForm):
    language = SelectField(
        "Öğrenmek istediğin dil",
        choices=[
            ("İngilizce", "İngilizce"),
            ("Almanca", "Almanca"),
            ("Fransızca", "Fransızca"),
            ("İspanyolca", "İspanyolca"),
            ("İtalyanca", "İtalyanca"),
            ("Japonca", "Japonca"),
            ("Korece", "Korece"),
            ("Türkçe", "Türkçe")
        ],
        validators=[DataRequired()]
    )
    submit = SubmitField("Dili Kaydet")


# Ana sayfa
@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("register"))


# Kayıt sayfası
@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    form = RegisterForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        username = form.username.data.strip()

        existing_user = User.query.filter(
            (User.email == email) |
            (User.username == username)
        ).first()

        if existing_user:
            flash(
                "Bu e-posta veya kullanıcı adı zaten kullanılıyor.",
                "error"
            )
            return render_template("register.html", form=form)

        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(form.password.data)
        )

        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)

        flash("Language Bank'e hoş geldin!", "success")
        return redirect(url_for("dashboard"))

    return render_template("register.html", form=form)


# Giriş sayfası
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(
            user.password,
            form.password.data
        ):
            login_user(user)
            flash("Başarıyla giriş yaptın!", "success")
            return redirect(url_for("dashboard"))

        flash("E-posta veya şifre hatalı.", "error")

    return render_template("login.html", form=form)


# Kullanıcı paneli
@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    form = LanguageForm()

    if form.validate_on_submit():
        current_user.learning_language = form.language.data
        db.session.commit()

        flash("Öğrenme dilin başarıyla kaydedildi!", "success")
        return redirect(url_for("dashboard"))

    if current_user.learning_language in [
        choice[0] for choice in form.language.choices
    ]:
        form.language.data = current_user.learning_language

    return render_template(
        "dashboard.html",
        user=current_user,
        form=form
    )


# Çıkış
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Başarıyla çıkış yaptın.", "success")
    return redirect(url_for("login"))


# PWA Service Worker
@app.route("/service-worker.js")
def service_worker():
    response = send_from_directory(
        app.root_path,
        "service-worker.js",
        mimetype="application/javascript"
    )
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache"
    return response


# Veritabanını oluştur
with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
