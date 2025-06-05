import os
from pypdf import PdfReader 
import docx # de python-docx

def extract_text_from_pdf(file_path):
    """Extrait le texte d'un fichier PDF."""
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text: # S'assurer qu'il y a du texte sur la page
                text += page_text + "\n" # Ajouter un saut de ligne entre les pages
        return text.strip() if text else None
    except Exception as e:
        print(f"Erreur lors de la lecture du PDF {file_path}: {e}")
        return None

def extract_text_from_docx(file_path):
    """Extrait le texte d'un fichier DOCX."""
    try:
        doc = docx.Document(file_path)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text.strip() if text else None
    except Exception as e:
        print(f"Erreur lors de la lecture du DOCX {file_path}: {e}")
        return None

def parse_document(file_path):
    """
    Détecte le type de fichier et appelle la fonction de parsing appropriée.
    Retourne le texte extrait ou None en cas d'erreur ou de type non supporté.
    """
    if not os.path.exists(file_path):
        print(f"Le fichier {file_path} n'existe pas.")
        return None

    _, file_extension = os.path.splitext(file_path)
    file_extension = file_extension.lower()

    if file_extension == ".pdf":
        return extract_text_from_pdf(file_path)
    elif file_extension == ".docx":
        return extract_text_from_docx(file_path)
    elif file_extension == ".txt": # Ajoutons le support pour .txt
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            print(f"Erreur lors de la lecture du TXT {file_path}: {e}")
            return None
    else:
        print(f"Type de fichier non supporté: {file_extension} pour le fichier {file_path}")
        return None

# --- Section de test (vous pouvez la mettre en commentaire plus tard) ---
if __name__ == "__main__":

    # Créez le dossier 'data' s'il n'existe pas pour les tests
    if not os.path.exists("./data"):
        os.makedirs("./data")
    
