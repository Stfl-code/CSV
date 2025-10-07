import streamlit as st
import gspread
import pandas as pd
import random

# Connexion à Google Sheets
gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
sh = gc.open_by_key(st.secrets["sheet"]["id"])

# Onglets Google Sheets
resultats = sh.worksheet("resultats")
joueurs = sh.worksheet("joueurs")
tournoi_sheet = sh.worksheet("tournoi")

# Charger les joueurs
prenoms = joueurs.col_values(1)[1:]
noms = joueurs.col_values(2)[1:]
liste_joueurs = [f"{p} {n}" for p, n in zip(prenoms, noms)]

# Charger les résultats existants
rows = resultats.get_all_records()
df = pd.DataFrame(rows)

# Charger les matchs du tournoi
tournoi_rows = tournoi_sheet.get_all_records()
df_tournoi = pd.DataFrame(tournoi_rows)

# Fonction pour calculer les stats actuelles
def calculer_stats():
    stats = {j: {"Victoires": 0, "Défaites": 0, "Points_marques": 0, "Points_encaisses": 0, "Diff": 0} for j in liste_joueurs}
    
    if not df_tournoi.empty:
        for _, row in df_tournoi.iterrows():
            if row["statut"] == "terminé":
                vainq = row["vainqueur"]
                j1 = row["joueur_1"]
                j2 = row["joueur_2"]
                score_p = row["score_perdant"]
                
                perdant = j2 if vainq == j1 else j1
                
                stats[vainq]["Victoires"] += 1
                stats[vainq]["Points_marques"] += 13
                stats[vainq]["Points_encaisses"] += score_p
                
                stats[perdant]["Défaites"] += 1
                stats[perdant]["Points_marques"] += score_p
                stats[perdant]["Points_encaisses"] += 13
    
    for j in stats:
        stats[j]["Diff"] = stats[j]["Points_marques"] - stats[j]["Points_encaisses"]
    
    return stats

# Fonction pour générer les appariements
def generer_appariements(nb_matchs=5):
    stats = calculer_stats()
    
    # Créer un classement temporaire
    classement = sorted(stats.items(), key=lambda x: (x[1]["Victoires"], x[1]["Diff"]), reverse=True)
    
    # Identifier les paires déjà jouées ou programmées
    paires_existantes = set()
    if not df_tournoi.empty:
        for _, row in df_tournoi.iterrows():
            j1, j2 = sorted([row["joueur_1"], row["joueur_2"]])
            paires_existantes.add((j1, j2))
    
    # Générer de nouveaux appariements
    joueurs_disponibles = [j[0] for j in classement]
    nouveaux_matchs = []
    
    # Essayer d'apparier les joueurs proches au classement
    tentatives = 0
    while len(nouveaux_matchs) < nb_matchs and len(joueurs_disponibles) >= 2 and tentatives < 100:
        tentatives += 1
        
        # Prendre le premier joueur disponible
        j1 = joueurs_disponibles[0]
        
        # Chercher un adversaire proche au classement
        adversaire_trouve = False
        for j2 in joueurs_disponibles[1:]:
            paire = tuple(sorted([j1, j2]))
            if paire not in paires_existantes:
                nouveaux_matchs.append([j1, j2, "à jouer", "", ""])
                paires_existantes.add(paire)
                joueurs_disponibles.remove(j1)
                joueurs_disponibles.remove(j2)
                adversaire_trouve = True
                break
        
        if not adversaire_trouve:
            joueurs_disponibles.remove(j1)
    
    return nouveaux_matchs

# Onglets de l'application
tabs = st.tabs(["🎪 Tournoi", "➕ Saisie résultat", "📊 Confrontations", "🏆 Classement"])

# --- Onglet Tournoi ---
with tabs[0]:
    st.header("🎪 Gestion du Tournoi")
    
    # Statistiques globales
    nb_total = len(liste_joueurs) * (len(liste_joueurs) - 1) // 2
    nb_joues = len(df_tournoi[df_tournoi["statut"] == "terminé"]) if not df_tournoi.empty else 0
    nb_en_cours = len(df_tournoi[df_tournoi["statut"] == "à jouer"]) if not df_tournoi.empty else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Parties terminées", f"{nb_joues}/{nb_total}")
    with col2:
        st.metric("En cours", nb_en_cours)
    with col3:
        progression = (nb_joues / nb_total * 100) if nb_total > 0 else 0
        st.metric("Progression", f"{progression:.0f}%")
    
    st.progress(progression / 100)
    
    st.divider()
    
    # Initialisation du tournoi
    if df_tournoi.empty:
        st.info("🎲 Le tournoi n'a pas encore été initialisé")
        
        col_init1, col_init2 = st.columns([2, 1])
        with col_init1:
            nb_matchs_init = st.slider("Nombre de matchs à générer", 5, 20, 10)
        with col_init2:
            st.write("")
            st.write("")
            if st.button("🚀 Lancer le tournoi", use_container_width=True):
                # Générer les premiers appariements aléatoires
                joueurs_shuffle = liste_joueurs.copy()
                random.shuffle(joueurs_shuffle)
                
                nouveaux_matchs = []
                for i in range(0, min(nb_matchs_init * 2, len(joueurs_shuffle) - 1), 2):
                    if i + 1 < len(joueurs_shuffle):
                        nouveaux_matchs.append([joueurs_shuffle[i], joueurs_shuffle[i+1], "à jouer", "", ""])
                
                # Ajouter au sheet
                for match in nouveaux_matchs:
                    tournoi_sheet.append_row(match)
                
                st.success(f"✅ {len(nouveaux_matchs)} matchs générés !")
                st.rerun()
    
    else:
        # Afficher les matchs en cours
        matchs_en_cours = df_tournoi[df_tournoi["statut"] == "à jouer"]
        
        if not matchs_en_cours.empty:
            st.subheader("⚡ Matchs à jouer")
            for _, match in matchs_en_cours.iterrows():
                st.info(f"🎯 **{match['joueur_1']}** vs **{match['joueur_2']}**")
        
        st.divider()
        
        # Bouton pour générer plus de matchs
        st.subheader("➕ Générer de nouveaux appariements")
        
        col_gen1, col_gen2 = st.columns([2, 1])
        with col_gen1:
            nb_nouveaux = st.slider("Nombre de nouveaux matchs", 1, 10, 5)
        with col_gen2:
            st.write("")
            st.write("")
            if st.button("Générer les appariements", use_container_width=True):
                nouveaux = generer_appariements(nb_nouveaux)
                
                if nouveaux:
                    for match in nouveaux:
                        tournoi_sheet.append_row(match)
                    st.success(f"✅ {len(nouveaux)} nouveaux matchs générés !")
                    st.rerun()
                else:
                    st.warning("⚠️ Impossible de générer plus de matchs (tous les joueurs se sont déjà affrontés)")
        
        st.divider()
        
        # Historique complet
        with st.expander("📋 Voir tous les matchs du tournoi"):
            st.dataframe(df_tournoi, use_container_width=True)

# --- Onglet Saisie ---
with tabs[1]:
    st.header("Saisie d'un résultat de tournoi")
    
    # Récupérer les matchs à jouer
    matchs_disponibles = []
    if not df_tournoi.empty:
        matchs_a_jouer = df_tournoi[df_tournoi["statut"] == "à jouer"]
        for _, match in matchs_a_jouer.iterrows():
            matchs_disponibles.append(f"{match['joueur_1']} vs {match['joueur_2']}")
    
    if not matchs_disponibles:
        st.warning("⚠️ Aucun match en attente. Va dans l'onglet Tournoi pour en générer !")
    else:
        match_selectionne = st.selectbox("Sélectionne le match", matchs_disponibles)
        
        if match_selectionne:
            j1, j2 = match_selectionne.replace(" vs ", "|").split("|")
            
            st.divider()
            
            with st.form("saisie_resultat_tournoi"):
                vainqueur = st.radio("Qui a gagné ?", [j1, j2])
                score_perdant = st.number_input("Score du perdant", min_value=0, max_value=12, value=0)
                
                st.caption(f"Résultat : **{vainqueur}** 13 - {score_perdant} **{j2 if vainqueur == j1 else j1}**")
                
                submitted = st.form_submit_button("✅ Enregistrer", use_container_width=True)
            
            if submitted:
                # Mettre à jour le tournoi
                cell = tournoi_sheet.find(match_selectionne.replace(" vs ", ""))
                if cell:
                    row_idx = cell.row
                    tournoi_sheet.update(f"C{row_idx}:E{row_idx}", [["terminé", vainqueur, score_perdant]])
                    
                    # Ajouter aussi dans les résultats généraux
                    resultats.append_row([vainqueur, j2 if vainqueur == j1 else j1, 13, score_perdant])
                    
                    st.success("✅ Résultat enregistré !")
                    st.rerun()

# --- Onglet Confrontations ---
with tabs[2]:
    st.header("Tableau des confrontations")
    
    if df.empty:
        st.info("Aucun résultat enregistré pour le moment")
    else:
        recap = pd.DataFrame("", index=liste_joueurs, columns=liste_joueurs)
        
        for _, row in df.iterrows():
            vainq = row["vainqueur"]
            adv = row["adversaire"]
            score_v = row.get("score_vainqueur", 13)
            score_a = row.get("score_adversaire", row.get("score_adv", 0))
            
            recap.loc[vainq, adv] = f"{score_v}-{score_a}"
            recap.loc[adv, vainq] = f"{score_a}-{score_v}"
        
        st.dataframe(recap, use_container_width=True)

# --- Onglet Classement ---
with tabs[3]:
    st.header("Classement du tournoi")
    
    stats = calculer_stats()
    
    if all(s["Victoires"] == 0 and s["Défaites"] == 0 for s in stats.values()):
        st.info("Aucune partie terminée pour le moment")
    else:
        classement = pd.DataFrame(stats).T
        classement["Parties jouées"] = classement["Victoires"] + classement["Défaites"]
        
        classement = classement.sort_values(by=["Victoires", "Diff"], ascending=[False, False])
        
        classement = classement[["Parties jouées", "Victoires", "Défaites", "Points_marques", "Points_encaisses", "Diff"]]
        classement.columns = ["Parties", "V", "D", "PM", "PE", "Diff"]
        
        st.dataframe(classement, use_container_width=True)
