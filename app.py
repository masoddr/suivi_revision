import os
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError

# Configuration des chemins
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

# Configuration de la base de données
if os.environ.get('RENDER'):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "revisions.db")}'

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24).hex())
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuration de sécurité
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 heure

# Initialisation des extensions
db = SQLAlchemy(app)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Configuration de Talisman (HTTPS et en-têtes de sécurité)
csp = {
    'default-src': "'self'",
    'img-src': "'self' data: https:",
    'script-src': "'self' 'unsafe-inline'",
    'style-src': "'self' 'unsafe-inline' https://fonts.googleapis.com",
    'font-src': "'self' https://fonts.gstatic.com",
}

Talisman(app,
         force_https=True,
         strict_transport_security=True,
         session_cookie_secure=True,
         content_security_policy=csp)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    exercices = db.relationship('Exercice', backref='user', lazy=True)

class Exercice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sujet = db.Column(db.String(200), nullable=False)
    lien = db.Column(db.String(500))
    numero = db.Column(db.Integer, nullable=False)
    themes = db.Column(db.String(200), nullable=False)
    complete = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Formulaires
class LoginForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    submit = SubmitField('Se connecter')

class RegisterForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('S\'inscrire')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Ce nom d\'utilisateur est déjà pris.')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('accueil'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('accueil'))
        flash('Identifiants invalides')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('accueil'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            password_hash=generate_password_hash(form.password.data)
        )
        db.session.add(user)
        db.session.commit()
        flash('Inscription réussie ! Vous pouvez maintenant vous connecter.')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def accueil():
    themes = ['Suites', 'Probabilités', 'Convexité', 'Intégrales', 
             'Géométrie dans l\'espace', 'Etudes de fonctions', 
             'Logarithme néperien', 'Exponentielle']
    progress_data = calculate_progress(current_user.id)
    return render_template('accueil.html', progress_data=progress_data, themes=themes)

@app.route('/exercices')
@login_required
def exercices():
    # Récupérer tous les exercices de l'utilisateur
    all_exercices = Exercice.query.filter_by(user_id=current_user.id).all()
    
    # Organiser les exercices par sujet
    sujets = {}
    for exercice in all_exercices:
        if exercice.sujet not in sujets:
            sujets[exercice.sujet] = {
                'nom': exercice.sujet,
                'lien': exercice.lien,
                'exercices': {}
            }
        sujets[exercice.sujet]['exercices'][exercice.numero] = exercice
    
    return render_template('exercices.html', sujets=sujets.values())

@app.route('/update_exercice', methods=['POST'])
@login_required
def update_exercice():
    exercice_id = request.json['id']
    complete = request.json['complete']
    
    exercice = Exercice.query.get(exercice_id)
    if exercice.user_id != current_user.id:
        return jsonify({'success': False}), 403
        
    exercice.complete = complete
    db.session.commit()
    
    progress_data = calculate_progress(current_user.id)
    return jsonify({
        'success': True,
        'progress': progress_data
    })

@app.route('/check_annale_complete', methods=['POST'])
@login_required
def check_annale_complete():
    sujet = request.json['sujet']
    exercices = Exercice.query.filter_by(
        user_id=current_user.id,
        sujet=sujet
    ).all()
    
    is_complete = all(ex.complete for ex in exercices)
    if is_complete:
        # Compter le nombre total d'annales complétées
        completed_annales = db.session.query(Exercice.sujet).filter(
            Exercice.user_id == current_user.id,
            Exercice.complete == True
        ).group_by(Exercice.sujet).count()
        
        return jsonify({
            'complete': True,
            'count': completed_annales,
            'message': f'Bravo ! Tu as complété {completed_annales} annale{"s" if completed_annales > 1 else ""} !'
        })
    return jsonify({'complete': False})

@app.route('/get_progress')
@login_required
def get_progress():
    progress_data = calculate_progress(current_user.id)
    return jsonify({'progress': progress_data})

def calculate_progress(user_id):
    themes = ['Suites', 'Probabilités', 'Convexité', 'Intégrales', 
             'Géométrie dans l\'espace', 'Etudes de fonctions', 
             'Logarithme néperien', 'Exponentielle']
    
    progress = []
    for theme in themes:
        completed = Exercice.query.filter(
            Exercice.user_id == user_id,
            Exercice.themes.like(f'%{theme}%'),
            Exercice.complete == True
        ).count()
        
        # On limite à 10 exercices maximum par thème
        progress.append(min(completed, 10))
    
    return progress 