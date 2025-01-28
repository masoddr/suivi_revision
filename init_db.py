from app import app, db, User, Exercice
from werkzeug.security import generate_password_hash

# Créer un contexte d'application
with app.app_context():
    # Recréer la base de données
    db.drop_all()
    db.create_all()

    # Créer un utilisateur de test
    user = User(
        username="Juliette",
        password_hash=generate_password_hash("mdp")
    )
    db.session.add(user)
    db.session.commit()

    # Ajouter quelques exercices de test
    exercices = [
        {
            "sujet": "Amérique du Sud 21 novembre 2024",
            "lien": "https://www.apmep.fr/IMG/pdf/SpeJ1_21_11_2024_Ameri_Sud_DV_2.pdf",
            "numero": 1,
            "themes": "Equa diff / etude de fonctions / python",
            "user_id": user.id
        },
        {
            "sujet": "Amérique du Sud 21 novembre 2024",
            "lien": "https://www.apmep.fr/IMG/pdf/SpeJ1_21_11_2024_Ameri_Sud_DV_2.pdf",
            "numero": 2,
            "themes": "Probabilités / Loi binomiale",
            "user_id": user.id
        },
        {
            "sujet": "Amérique du Sud 21 novembre 2024",
            "lien": "https://www.apmep.fr/IMG/pdf/SpeJ1_21_11_2024_Ameri_Sud_DV_2.pdf",
            "numero": 3,
            "themes": "Suites",
            "user_id": user.id
        },
        {
            "sujet": "Amérique du Sud 21 novembre 2024",
            "lien": "https://www.apmep.fr/IMG/pdf/SpeJ1_21_11_2024_Ameri_Sud_DV_2.pdf",
            "numero": 4,
            "themes": "Géométrie dans l'espace",
            "user_id": user.id
        },
        {
            "sujet": "Métropole 19 juin 2024",
            "lien": "https://www.apmep.fr/IMG/pdf/Metropole_J1_spe_19_06_2024_VTFK.pdf",
            "numero": 1,
            "themes": "Suites / Logarithme néperien",
            "user_id": user.id
        },
        {
            "sujet": "Métropole 19 juin 2024",
            "lien": "https://www.apmep.fr/IMG/pdf/Metropole_J1_spe_19_06_2024_VTFK.pdf",
            "numero": 2,
            "themes": "Intégrales / Exponentielle",
            "user_id": user.id
        }
    ]

    for exercice_data in exercices:
        exercice = Exercice(**exercice_data)
        db.session.add(exercice)

    db.session.commit() 