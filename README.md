# ClasseurCVs

Voici un **README complet** sous forme **d’un seul bloc de code** intégrant toutes les sections : installation, structure, Docker, Kubernetes, technologies, etc.

```markdown
# 📄 Classeur Intelligent de CVs

Cette application web permet aux recruteurs d’analyser et de classer des CVs par rapport à une **description de poste**. Elle utilise un **modèle de langage (LLM)** pour extraire la pertinence de chaque profil. Développée avec **Python**, **Chainlit** pour l’interface, et déployable avec **Docker** ou **Kubernetes (`kind`)**.

---

## 🚀 Fonctionnalités

- 📄 Téléversement de la **description de poste** (fichier `.txt` ou `.docx`) ou saisie manuelle
- 📑 Téléversement **multi-CVs** au format `.pdf`
- 🧠 Analyse via **LLM (Mistral)** : compétences, expérience, adéquation
- 📊 Classement des candidats avec explications
- 🌐 Interface utilisateur conviviale avec **Chainlit**
- 🐳 Conteneurisation avec **Docker**
- ☸️ Déploiement local avec **Kubernetes** (`kind`)

---

## 🧰 Technologies

- `Python`
- `Chainlit`
- `pypdf`, `python-docx` (lecture de fichiers)
- `dotenv` (gestion des secrets)
- `Docker`
- `Kubernetes` avec `kind`

---

## 📁 Structure du projet

```

classeur\_cv\_project/
├── src/
│   ├── app.py                  # Script principal
│   ├── cv\_parser.py            # Extraction de contenu des CVs
│   └── llm\_handler.py          # Interaction avec le LLM
├── data/                       # Dossier de stockage
├── temp\_app\_files\_chainlit/    # Fichiers temporaires (uploads)
├── .env                        # Clé API LLM (non versionnée)
├── Dockerfile                  # Image Docker
├── classeur-cv-k8s.yaml        # Manifestes Kubernetes
├── requirements.txt            # Dépendances Python
└── README.md

````

---

## ⚙️ Installation locale (sans Docker)

```bash
git clone https://github.com/monrepo/classeur_cv_project.git
cd classeur_cv_project
python -m venv venv
source venv/bin/activate        # ou venv\Scripts\activate sous Windows
pip install -r requirements.txt
````

Créer un fichier `.env` :

```env
MISTRAL_API_KEY="votre_clé_api_mistral"
```

Lancer l’application localement :

```bash
chainlit run src/app.py -w
```

Accès via : [http://localhost:8000](http://localhost:8000)

---

## 🐳 Exécution avec Docker

### 1. Build de l’image :

```bash
docker build -t classeur-cv-app:v1 .
```

### 2. Lancement du conteneur :

```bash
docker run -p 8000:8000 --rm --name classeur-cv classeur-cv-app:v1
```

Interface accessible sur : [http://localhost:8000](http://localhost:8000)

---

## ☸️ Déploiement sur Kubernetes (via kind)

### 1. Créer le cluster

```bash
kind create cluster --name classeur-cv-cluster
```

### 2. Charger l’image dans le cluster

```bash
kind load docker-image classeur-cv-app:v1 --name classeur-cv-cluster
```

### 3. Appliquer le fichier YAML

```bash
kubectl apply -f classeur-cv-k8s.yaml
```

### 4. Exposer le service en local

```bash
kubectl port-forward service/classeur-cv-service 8080:8000
```

Naviguer vers : [http://localhost:8080](http://localhost:8080)

---

## 📌 Améliorations futures

* Gestion avancée des erreurs utilisateur
* Suppression automatique des fichiers temporaires
* Optimisation des prompts LLM
* Déploiement cloud (GCP, Azure, AWS)
* Ajout d’un système d’authentification (admin/recruteur)

---



