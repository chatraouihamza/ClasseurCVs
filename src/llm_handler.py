import os
import json
import re
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
from dotenv import load_dotenv

# Chargement des variables d'environnement
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# Configuration
try:
    api_key = os.environ["MISTRAL_API_KEY"]
    client = MistralClient(api_key=api_key) if api_key else None
except KeyError:
    print("ERREUR: MISTRAL_API_KEY non définie dans .env")
    client = None

def extract_json_from_response(text):
    """Extrait un objet JSON d'une réponse texte, même mal formatée."""
    try:
        # Essai de parsing direct
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            # Tentative d'extraction avec regex
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                return json.loads(json_match.group())
        except Exception:
            pass
    return None

def get_mistral_response(prompt_text, model="open-mixtral-8x7b"):
    """Envoie un prompt à Mistral et retourne la réponse."""
    if not client or not prompt_text:
        print("Client non initialisé ou prompt vide")
        return None

    try:
        response = client.chat(
            model=model,
            messages=[ChatMessage(role="user", content=prompt_text)],
            temperature=0.7,
            response_format={"type": "json_object"}  # Force le format JSON
        )
        return response.choices[0].message.content if response.choices else None
    except Exception as e:
        print(f"Erreur API Mistral: {str(e)}")
        return None

def generate_structured_summary(cv_text, jd_text):
    """Génère un résumé structuré JSON d'un CV par rapport à une JD."""
    if not all([cv_text, jd_text]):
        return None

    prompt = f"""Analysez ce CV par rapport à la Description de Poste (JD) et retournez UNIQUEMENT un JSON valide.

Description de Poste:
{jd_text}

CV à analyser:
{cv_text}

Format JSON attendu:
{{
  "nom_candidat": "string",
  "score_adequation_preliminaire": 0-10,
  "competences_cles_presentes": ["string"],
  "competences_cles_manquantes": ["string"],
  "annees_experience_pertinente": "string",
  "niveau_formation_correspond": "string",
  "points_forts_synthetiques": ["string"],
  "points_faibles_synthetiques": ["string"]
}}"""

    response = get_mistral_response(prompt)
    if not response:
        return None

    json_data = extract_json_from_response(response)
    if not json_data:
        print(f"Réponse non JSON reçue:\n{response[:500]}...")
        return None

    # Validation des champs requis
    required_fields = ["nom_candidat", "score_adequation_preliminaire", "competences_cles_presentes"]
    if not all(field in json_data for field in required_fields):
        print("Champs manquants dans la réponse JSON")
        return None

    return json_data

def generate_ranking(summaries, jd_text):
    """Génère un classement des candidats basé sur leurs résumés."""
    if not summaries or not jd_text:
        return None

    candidates_str = "\n\n".join(
        f"Candidat {i+1}:\n{json.dumps(s, indent=2)}" 
        for i, s in enumerate(summaries))
    
    prompt = f"""Classer ces candidats par ordre de pertinence pour le poste. 
Retournez UNIQUEMENT un JSON avec le format:
{{
  "classement": [
    {{
      "nom": "string",
      "position": 1,
      "justification": "string"
    }}
  ],
  "analyse_comparative": "string"
}}

Description du poste:
{jd_text}

Candidats:
{candidates_str}"""

    response = get_mistral_response(prompt)
    return extract_json_from_response(response)
