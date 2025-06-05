import chainlit as cl
import os

# Importer depuis vos modules locaux
try:
    from cv_parser import parse_document
    from llm_handler import (
        generate_structured_summary,
        generate_ranking,
        client as mistral_llm_client
    )
except ImportError as e:
    print(f"Erreur d'importation des modules locaux: {e}")
    parse_document = None
    generate_structured_summary = None
    generate_ranking = None
    mistral_llm_client = None


@cl.on_chat_start
async def start_chat():
    # ... (code identique jusqu'à la fin de @cl.on_chat_start) ...
    if not mistral_llm_client:
        await cl.Message(
            content="**ERREUR : Le client Mistral n'a pas pu être initialisé.** " # Gras pour l'erreur
                    "Veuillez vérifier la configuration et redémarrer l'application."
        ).send()
        return
    
    if not all([parse_document, generate_structured_summary, generate_ranking]):
        await cl.Message(
            content="**ERREUR : Fonctions backend manquantes.** Vérifiez les logs." # Gras pour l'erreur
        ).send()
        return

    await cl.Message(
        content="Bienvenue dans l'Assistant de Classement de CVs !\n"
                "Pour commencer, veuillez fournir les documents requis."
    ).send()

    files_res = None
    while files_res is None:
        files_res = await cl.AskFileMessage( 
            content="Veuillez uploader :\n1. **Un seul fichier pour la Description de Poste (JD)** (PDF, DOCX, ou TXT)\n2. **Un ou plusieurs fichiers pour les CVs des candidats** (PDF, DOCX, ou TXT)",
            accept={
                "application/pdf": [".pdf"],
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
                "text/plain": [".txt"]
            },
            max_size_mb=20,
            max_files=10,
            timeout=3000,
        ).send()

    actual_jd_file_object = None
    actual_cv_file_objects = []

    if not files_res:
        await cl.Message(content="Aucun fichier n'a été uploadé. Veuillez rafraîchir pour réessayer.").send()
        return

    if len(files_res) < 2:
        await cl.Message(content="**Erreur : Vous devez uploader au moins une Description de Poste ET un CV.**").send()
        return

    file_names = [f.name for f in files_res] 
    
    jd_choice_answer_msg = await cl.AskUserMessage(
        content=f"Parmi les fichiers suivants, lequel est la **Description de Poste (JD)** ?\n" +
                "\n".join([f"{i+1}. {name}" for i, name in enumerate(file_names)]) +
                "\n\nEntrez le numéro correspondant.",
        timeout=60
    ).send()

    if jd_choice_answer_msg and jd_choice_answer_msg['output'].strip().isdigit():
        try:
            jd_index = int(jd_choice_answer_msg['output'].strip()) - 1
            if 0 <= jd_index < len(files_res):
                actual_jd_file_object = files_res.pop(jd_index) 
                actual_cv_file_objects = files_res             
                
                print(f"DEBUG @on_chat_start: Type de actual_jd_file_object: {type(actual_jd_file_object)}")
                if actual_cv_file_objects:
                    print(f"DEBUG @on_chat_start: Type de actual_cv_file_objects[0]: {type(actual_cv_file_objects[0])}")

                cl.user_session.set("the_jd_file", actual_jd_file_object) 
                cl.user_session.set("the_cv_files", actual_cv_file_objects)
            else:
                await cl.Message(content="**Numéro invalide pour la JD.** Veuillez rafraîchir et réessayer.").send()
                return
        except ValueError:
            await cl.Message(content="**Entrée invalide.** Veuillez entrer un numéro. Rafraîchissez et réessayer.").send()
            return
    else:
        await cl.Message(content="Aucune sélection valide pour la JD ou timeout. Veuillez rafraîchir et réessayer.").send()
        return

    if not actual_cv_file_objects:
        await cl.Message(content="**Erreur : Aucun CV n'a été identifié après la sélection de la JD.**").send()
        return
    if not actual_jd_file_object:
        await cl.Message(content="**Erreur : La JD n'a pas été identifiée.**").send()
        return

    await cl.Message(
        content=f"Description de Poste '{actual_jd_file_object.name}' et {len(actual_cv_file_objects)} CV(s) reçu(s).\n"
                "Cliquez sur 'Analyser et Classer' pour lancer le traitement."
    ).send()

    actions = [
        cl.Action(
            name="analyze_and_rank", 
            payload={"status": "data_ready"},
            label="Analyser et Classer",
            description="Cliquez ici pour démarrer l'analyse et le classement !"
        )
    ]
    await cl.Message(content="Prêt à analyser ?", actions=actions).send()


@cl.action_callback("analyze_and_rank")
async def on_analyze_and_rank(action: cl.Action):
    if action.payload and action.payload.get("status") == "data_ready":
        retrieved_jd_obj_from_session = cl.user_session.get("the_jd_file")
        retrieved_cv_list_from_session = cl.user_session.get("the_cv_files")

        if not retrieved_jd_obj_from_session or not retrieved_cv_list_from_session:
            await cl.Message(content="**Erreur : Fichiers JD ou CVs non trouvés dans la session (callback).** Veuillez recommencer.").send()
            return

        processing_msg = cl.Message(content="", author="Assistant") 
        await processing_msg.send() 

        # Utiliser des préfixes emoji et/ou italique pour le statut
        # Le _texte_ mettra le texte en italique en Markdown
        # Vous pouvez aussi utiliser *texte* pour italique ou **texte** pour gras.

        await processing_msg.stream_token("⚙️ _Début de l'analyse..._\n")
        
        jd_text = None
        jd_target_for_parsing = None

        if hasattr(retrieved_jd_obj_from_session, 'path'):
            jd_target_for_parsing = retrieved_jd_obj_from_session
        
        if not jd_target_for_parsing: # Logique de fallback
            if hasattr(retrieved_jd_obj_from_session, 'files') and isinstance(retrieved_jd_obj_from_session.files, list) and retrieved_jd_obj_from_session.files:
                 candidate_file = retrieved_jd_obj_from_session.files[0]
                 if hasattr(candidate_file, 'path'):
                     jd_target_for_parsing = candidate_file
                     await processing_msg.stream_token(f"⚙️ _Trouvé un fichier JD dans .files[0] : {candidate_file.path}_\n")

        if not jd_target_for_parsing or not hasattr(jd_target_for_parsing, 'path'):
            await processing_msg.stream_token("⚠️ **ERREUR FINALE: Impossible de déterminer l'objet fichier JD valide ou son chemin.**\n")
            return
        
        try:
            await processing_msg.stream_token(f"⚙️ _Traitement de la Description de Poste '{jd_target_for_parsing.name}'..._\n")
            jd_text = parse_document(jd_target_for_parsing.path)
        except Exception as e:
            await processing_msg.stream_token(f"⚠️ **ERREUR lors du parsing JD '{jd_target_for_parsing.name}': {e}**\n")
            return
            
        if not jd_text:
            await processing_msg.stream_token(f"⚠️ **ERREUR: Contenu vide pour JD '{jd_target_for_parsing.name}'.**\n")
            return
        
        await processing_msg.stream_token("✅ _JD analysée avec succès._\n")

        all_summaries = []
        has_errors = False

        for i, cv_item_original_from_list in enumerate(retrieved_cv_list_from_session):
            cv_target_for_parsing = None
            if hasattr(cv_item_original_from_list, 'path'):
                cv_target_for_parsing = cv_item_original_from_list
            elif hasattr(cv_item_original_from_list, 'files') and isinstance(cv_item_original_from_list.files, list) and cv_item_original_from_list.files:
                cv_target_for_parsing = cv_item_original_from_list.files[0]

            if not cv_target_for_parsing or not hasattr(cv_target_for_parsing, 'path'):
                await processing_msg.stream_token(f"⚠️ **ERREUR CV {i+1}: Impossible de déterminer l'objet fichier CV.** Type: {type(cv_item_original_from_list)}.\n")
                has_errors = True
                continue

            await processing_msg.stream_token(f"\n⚙️ _Traitement du CV {i+1}/{len(retrieved_cv_list_from_session)}: '{cv_target_for_parsing.name}'..._\n")
            cv_text = None
            try:
                await processing_msg.stream_token(f"⚙️ _Lecture du CV '{cv_target_for_parsing.name}'..._\n")
                cv_text = parse_document(cv_target_for_parsing.path)
            except Exception as e:
                await processing_msg.stream_token(f"⚠️ **ERREUR lors du parsing CV '{cv_target_for_parsing.name}': {e}**\n")
                has_errors = True
                continue
            
            if not cv_text:
                await processing_msg.stream_token(f"⚠️ **ERREUR: Contenu vide pour CV '{cv_target_for_parsing.name}'.**\n")
                has_errors = True
                continue 

            await processing_msg.stream_token(f"⚙️ _Génération du résumé pour '{cv_target_for_parsing.name}'..._\n")
            summary = await cl.make_async(generate_structured_summary)(cv_text, jd_text)

            if summary:
                all_summaries.append(summary)
                await processing_msg.stream_token(f"✅ _Résumé pour '{cv_target_for_parsing.name}' généré._\n")
            else:
                await processing_msg.stream_token(f"⚠️ **ERREUR: Échec de la génération du résumé pour '{cv_target_for_parsing.name}'.**\n")
                has_errors = True
        
        if not all_summaries:
            final_message = "Aucun résumé de CV n'a pu être généré."
            if has_errors:
                final_message += " Des erreurs sont survenues pendant le traitement."
            await cl.Message(content=f"**{final_message}**", author="Assistant").send() 
            return

        await processing_msg.stream_token("⚙️ _Génération du classement final..._\n")
        # Vous pouvez supprimer processing_msg ici si vous voulez un nouveau message pour le classement.
        # await processing_msg.remove()

        ranking_data = await cl.make_async(generate_ranking)(all_summaries, jd_text)
        
        if ranking_data and "classement" in ranking_data:
            report_content = f"## Rapport de Classement des CVs\n\n" 
            if "analyse_comparative" in ranking_data:
                report_content += f"**Analyse Comparative Globale:**\n{ranking_data['analyse_comparative']}\n\n"
            report_content += "**Classement Détaillé:**\n"
            for rank_entry in ranking_data["classement"]:
                report_content += f"- **Position {rank_entry.get('position', 'N/A')}: {rank_entry.get('nom', 'N/A')}**\n"
                report_content += f"  *Justification:* {rank_entry.get('justification', 'N/A')}\n"
            # Le message final du rapport est en Markdown standard, pas de style spécifique ici.
            await cl.Message(content=report_content, author="Assistant RH").send() 
        else:
            await cl.Message(content="**Erreur : Échec de la génération du classement final ou format de réponse incorrect du LLM.**").send()
        
        if has_errors:
            await cl.Message(content="️️️⚠️ _Note : Des erreurs sont survenues lors du traitement de certains fichiers. Veuillez vérifier les messages de statut et les logs du serveur._").send()
    else:
        await cl.Message(content=f"**Action '{action.name}' reçue avec un payload inattendu: {action.payload}.**").send()