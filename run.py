from app import app, db
from init_db import init_db
import os

if __name__ == '__main__':
    # Créer le dossier instance si nécessaire
    os.makedirs('instance', exist_ok=True)
    
    with app.app_context():
        # Créer les tables si elles n'existent pas
        db.create_all()
        
        # Initialiser les données si la base est vide
        from app import User
        if not User.query.first():
            print("Initialisation de la base de données...")
            init_db()
    
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 