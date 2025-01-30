import os
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'revisions.db')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'votre_clé_secrète_ici')
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('accueil'))
        flash('Identifiants invalides')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Nom d\'utilisateur déjà pris')
            return redirect(url_for('register'))
            
        user = User(username=username, 
                   password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def accueil():
    # Récupérer les statistiques
    user_exercises = Exercice.query.filter_by(user_id=current_user.id).all()
    total_count = len(user_exercises)
    completed_count = sum(1 for ex in user_exercises if ex.complete)
    
    # Calculer le meilleur thème
    themes = ['Suites', 'Probabilités', 'Convexité', 'Intégrales', 
             'Géométrie dans l\'espace', 'Etudes de fonctions', 
             'Logarithme néperien', 'Exponentielle']
    
    theme_scores = {}
    for theme in themes:
        theme_exercises = Exercice.query.filter(
            Exercice.user_id == current_user.id,
            Exercice.themes.like(f'%{theme}%')
        ).all()
        
        if theme_exercises:
            completion_rate = sum(1 for ex in theme_exercises if ex.complete) / len(theme_exercises)
            theme_scores[theme] = completion_rate
    
    best_theme = max(theme_scores.items(), key=lambda x: x[1])[0] if theme_scores else "Aucun"
    
    # Calculer les données de progression
    progress_data = calculate_progress(current_user.id)
    
    return render_template('accueil.html',
                         progress_data=progress_data,
                         total_count=total_count,
                         completed_count=completed_count,
                         best_theme=best_theme)

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

@app.route('/reset_progress', methods=['POST'])
@login_required
def reset_progress():
    try:
        # Récupérer tous les exercices de l'utilisateur connecté
        user_exercises = Exercice.query.filter_by(user_id=current_user.id).all()
        
        # Mettre à jour le statut de tous les exercices à False
        for exercise in user_exercises:
            exercise.complete = False
        
        # Sauvegarder les modifications dans la base de données
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Progrès réinitialisés avec succès'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

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