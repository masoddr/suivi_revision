#!/bin/bash

# Création du dossier de déploiement
mkdir -p deploy_suivi_revision

# Copie des fichiers nécessaires
cp -r app.py run.py requirements.txt init_db.py static templates instance deploy_suivi_revision/
cp Dockerfile docker-compose.yml nginx.conf deploy_suivi_revision/

# Création d'un fichier .env pour la production si nécessaire
touch deploy_suivi_revision/.env

# Archive du dossier
tar -czf deploy_suivi_revision.tar.gz deploy_suivi_revision/

# Instructions pour l'envoi (à personnaliser)
echo "Pour envoyer les fichiers sur votre VPS, utilisez la commande :"
echo "scp deploy_suivi_revision.tar.gz massyl@147.79.115.181:/home/massyl/sites_web"

# Nettoyage
rm -rf deploy_suivi_revision 