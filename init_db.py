from app import app, db, User, Exercice
from werkzeug.security import generate_password_hash
import os

def init_db():
    print("Début de l'initialisation de la base de données...")
    print(f"URI de la base de données : {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    with app.app_context():
        print("Création des tables...")
        db.create_all()
        print("Tables créées avec succès!")
        
        sujets = [
            {
                "nom": "Amérique du Sud 21 novembre 2024",
                "lien": "https://www.apmep.fr/IMG/pdf/SpeJ1_21_11_2024_Ameri_Sud_DV_2.pdf",
                "exercices": [
                    "Equa diff / etude de fonctions / python",
                    "Probabilités / Loi binomiale",
                    "Suites",
                    "Géométrie dans l'espace"
                ]
            },
            {
                "nom": "Amérique du Nord 21 novembre 2024",
                "lien": "https://www.apmep.fr/IMG/pdf/Spe__Ame_rique_Nord_J2_22_mai_2024.pdf",
                "exercices": [
                    "Probabilités / Loi Binomiale",
                    "Géométrie dans l'espace",
                    "Suites / ln / python",
                    "Primitive"
                ]
            },
            {
                "nom": "Métropole 19 juin 2024",
                "lien": "https://www.apmep.fr/IMG/pdf/Metropole_J1_spe_19_06_2024_VTFK.pdf",
                "exercices": [
                    "Justification affirmations",
                    "Probabilités / Loi Binomiale",
                    "Géométrie dans l'espace",
                    "Etudes de fonction / Logarithme népérien / Intégrale"
                ]
            },
            {
                "nom": "La Réunion 28 mars 2023",
                "lien": "https://www.apmep.fr/IMG/pdf/La_Reunion_spe_J1_28_mars_2023_DV.pdf",
                "exercices": [
                    "Probabilités / Loi Binomiale",
                    "Etudes de fonctions/ LN",
                    "Suites",
                    "Géométrie dans l'espace"
                ]
            },
            {
                "nom": "Métropole Antilles-Guyane 12 septembre 2024",
                "lien": "https://www.apmep.fr/IMG/pdf/Spe_J2_12_09_2024_Metropole_DV.pdf",
                "exercices": [
                    "Géométrie dans l'espace",
                    "Probabilités / Loi Binomiale",
                    "Etudes de fonctions / Convexité",
                    "QCM"
                ]
            },
            {
                "nom": "Amérique du Nord 21 mai 2024",
                "lien": "https://www.apmep.fr/IMG/pdf/Spe_Amerique_Nord21_05_2024_DV.pdf",
                "exercices": [
                    "Proba / Loi Binomiale",
                    "Géométrie dans l'espace",
                    "Etudes de fonctions / Convexité",
                    "Intégrales"
                ]
            }
        ]

        print("Création de l'utilisateur test...")
        test_user = User.query.filter_by(username="test").first()
        if not test_user:
            test_user = User(username="test", 
                           password_hash=generate_password_hash("test123"))
            db.session.add(test_user)
            db.session.commit()
            print("Utilisateur test créé!")
        else:
            print("Utilisateur test existe déjà!")

        print("Ajout des exercices...")
        for sujet in sujets:
            for i, theme in enumerate(sujet["exercices"], 1):
                exercice = Exercice(
                    sujet=sujet["nom"],
                    lien=sujet["lien"],
                    numero=i,
                    themes=theme,
                    user_id=test_user.id
                )
                db.session.add(exercice)
        
        db.session.commit()
        print("Exercices ajoutés avec succès!")
        print("Initialisation terminée!")

if __name__ == "__main__":
    init_db() 