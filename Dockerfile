
FROM python:3.12-slim 
# Si python:3.12-slim n'est pas disponible ou cause des soucis, essayez python:3.11-slim ou python:3.10-slim

# Définir des variables d'environnement pour Python pour un meilleur comportement dans Docker
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier le fichier des dépendances en premier
COPY requirements.txt .

# Mettre à jour pip et installer les dépendances
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copier le dossier src contenant votre code applicatif
COPY src/ ./src/

# Copier le fichier .env pour que python-dotenv puisse le lire à l'intérieur du conteneur
# ATTENTION: Pour la production, gérez les secrets différemment (variables d'env Docker, secrets manager)
COPY .env .

# Exposer le port sur lequel Chainlit s'exécute
EXPOSE 8000

# La commande pour exécuter l'application lorsque le conteneur démarre
# --host 0.0.0.0 est crucial pour l'accessibilité externe du conteneur
# --port 8000 spécifie le port à l'intérieur du conteneur
CMD ["chainlit", "run", "src/app.py", "-w", "--host", "0.0.0.0", "--port", "8000"]