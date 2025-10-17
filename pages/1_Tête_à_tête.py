import streamlit as st
import gspread
import pandas as pd
import random

#############
# Affichage #
#############
st.set_page_config(page_title="Tête-à-tête", page_icon="👤")
st.image("images/img_tournoi.png", use_container_width=True)
st.write("# Parties en tête-à-tête du club de pétanque de Vaux-sur-Seine")

#######################
# Liens et chargement #
#######################
# Initialiser la connexion Google Sheets uniquement si nécessaire
if 'sheets_loaded' not in st.session_state:
    gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    sh = gc.open_by_key(st.secrets["sheet"]["id"])
    
    # Onglets Google Sheets
    resultats = sh.worksheet("resultats")
    joueurs_sheet = sh.worksheet("joueurs")
    tournoi_sheet = sh.worksheet("tournoi")
    
    # Charger les joueurs
    prenoms = joueurs_sheet.col_values(1)[1:]
    noms = joueurs_sheet.col_values(2)[1:]
    st.session_state.liste_joueurs_complet = [f"{p} {n}" for p, n in zip(prenoms, noms)]
    
    # Charger les matchs du tournoi
    tournoi_rows = tournoi_sheet.get_all_records()
    st.session_state.df_tournoi = pd.DataFrame(tournoi_rows)
    
    # Sauvegarder les worksheets
    st.session_state.resultats = resultats
    st.session_state.tournoi_sheet = tournoi_sheet
    st.session_state.sheets_loaded = True
else:
    resultats = st.session_state.resultats
    tournoi_sheet = st.session_state.tournoi_sheet

# Utiliser les données en cache
liste_joueurs_complet = st.session_state.liste_joueurs_complet
df_tournoi = st.session_state.df_tournoi

# Charger les résultats existants (on recharge à chaque fois car ils changent)
rows = resultats.get_all_records()
df = pd.DataFrame(rows)

# Récupérer les joueurs participant au tournoi
joueurs_tournoi = []
if not df_tournoi.empty:
    j1_list = df_tournoi["joueur_1"].unique().tolist()
    j2_list = df_tournoi["joueur_2"].unique().tolist()
    joueurs_tournoi = list(set(j1_list + j2_list))
    liste_joueurs = joueurs_tournoi
else:
    liste_joueurs = liste_joueurs_complet

#############
# Fonctions #
#############
# Fonction pour calculer les stats du tournoi actuel
def calculer_stats_tournoi():
    stats_tournoi = {j: {"Victoires": 0, "Défaites": 0, "Points_marques": 0, "Points_encaisses": 0, "Diff": 0} for j in liste_joueurs}
    
    if not df_tournoi.empty:
        for _, row in df_tournoi.iterrows():
            if row["statut"] == "terminé":
                vainq = row["vainqueur"]
                j1 = row["joueur_1"]
                j2 = row["joueur_2"]
                score_p = row["score_perdant"]
                
                perdant = j2 if vainq == j1 else j1
                
                if vainq in stats_tournoi:
                    stats_tournoi[vainq]["Victoires"] += 1
                    stats_tournoi[vainq]["Points_marques"] += 13
                    stats_tournoi[vainq]["Points_encaisses"] += score_p
                
                if perdant in stats_tournoi:
                    stats_tournoi[perdant]["Défaites"] += 1
                    stats_tournoi[perdant]["Points_marques"] += score_p
                    stats_tournoi[perdant]["Points_encaisses"] += 13
    
    for j in stats_tournoi:
        stats_tournoi[j]["Diff"] = stats_tournoi[j]["Points_marques"] - stats_tournoi[j]["Points_encaisses"]
    
    return stats_tournoi

# Fonction pour calculer les stats du jeu libre
def calculer_stats():
    stats = {j: {"Victoires": 0, "Défaites": 0, "Points_marques": 0, "Points_encaisses": 0, "Diff": 0, "Tôle_infligées": 0, "Tôle_encaissées": 0} for j in liste_joueurs_complet}
    
    if not df.empty:  # df correspond à la feuille "résultats"
        for _, row in df.iterrows():
            vainq = row["vainqueur"]
            perdant = row["adversaire"]
            score_v = row.get("score_vainqueur", 13)
            score_p = row.get("score_adversaire", 0)
            
            # Mettre à jour les stats du vainqueur
            if vainq in stats:
                stats[vainq]["Victoires"] += 1
                stats[vainq]["Points_marques"] += score_v
                stats[vainq]["Points_encaisses"] += score_p
                if score_p == 0: 
                    stats[vainq]["Tôle_infligées"] += 1
            
            # Mettre à jour les stats du perdant
            if perdant in stats:
                stats[perdant]["Défaites"] += 1
                stats[perdant]["Points_marques"] += score_p
                stats[perdant]["Points_encaisses"] += score_v
                if score_p == 0:
                    stats[perdant]["Tôle_encaissées"] += 1
    
    # Calculer la différence de points
    for j in stats:
        stats[j]["Diff"] = stats[j]["Points_marques"] - stats[j]["Points_encaisses"]
    
    return stats

# Fonction pour générer les appariements (ronde suisse)
def generer_appariements_suisse(nb_matchs, joueurs_liste):
    stats_tournoi = calculer_stats_tournoi()
    
    # Créer un classement temporaire
    classement = sorted(stats_tournoi.items(), key=lambda x: (x[1]["Victoires"], x[1]["Diff"]), reverse=True)
    joueurs_classes = [j[0] for j in classement if j[0] in joueurs_liste]
    
    # Identifier les paires déjà jouées ou programmées
    paires_existantes = set()
    if not df_tournoi.empty:
        for _, row in df_tournoi.iterrows():
            j1, j2 = sorted([row["joueur_1"], row["joueur_2"]])
            paires_existantes.add((j1, j2))
    
    # Générer les appariements pour cette ronde
    nouveaux_matchs = []
    joueurs_deja_apparies = set()
    
    # Pour chaque joueur (dans l'ordre du classement)
    for i, j1 in enumerate(joueurs_classes):
        # Si on a assez de matchs ou si ce joueur est déjà apparié, passer
        if len(nouveaux_matchs) >= nb_matchs or j1 in joueurs_deja_apparies:
            continue
        
        # Chercher le meilleur adversaire disponible
        meilleur_adversaire = None
        
        # Parcourir les joueurs suivants dans le classement (les plus proches)
        for j2 in joueurs_classes[i+1:]:
            # Vérifier que j2 n'est pas déjà apparié et que la paire n'existe pas
            if j2 not in joueurs_deja_apparies:
                paire = tuple(sorted([j1, j2]))
                if paire not in paires_existantes:
                    meilleur_adversaire = j2
                    break
        
        # Si pas trouvé en cherchant "vers le bas", chercher "vers le haut"
        if not meilleur_adversaire:
            for j2 in joueurs_classes[:i]:
                if j2 not in joueurs_deja_apparies:
                    paire = tuple(sorted([j1, j2]))
                    if paire not in paires_existantes:
                        meilleur_adversaire = j2
                        break
        
        # Si un adversaire a été trouvé, créer le match
        if meilleur_adversaire:
            nouveaux_matchs.append([j1, meilleur_adversaire, "à jouer", "", ""])
            paires_existantes.add(tuple(sorted([j1, meilleur_adversaire])))
            joueurs_deja_apparies.add(j1)
            joueurs_deja_apparies.add(meilleur_adversaire)
    
    return nouveaux_matchs

# Fonction pour générer les appariements aléatoires
def generer_appariements_aleatoires(nb_matchs, joueurs_liste):
    # Identifier les paires déjà jouées ou programmées
    paires_existantes = set()
    if not df_tournoi.empty:
        for _, row in df_tournoi.iterrows():
            j1, j2 = sorted([row["joueur_1"], row["joueur_2"]])
            paires_existantes.add((j1, j2))
    
    # Mélanger la liste des joueurs
    joueurs_shuffle = joueurs_liste.copy()
    random.shuffle(joueurs_shuffle)
    
    nouveaux_matchs = []
    joueurs_deja_apparies = set()
    
    # Essayer de créer des paires aléatoires
    for i in range(len(joueurs_shuffle)):
        if len(nouveaux_matchs) >= nb_matchs:
            break
        
        j1 = joueurs_shuffle[i]
        if j1 in joueurs_deja_apparies:
            continue
        
        # Chercher un adversaire aléatoire non encore apparié
        for j2 in joueurs_shuffle[i+1:]:
            if j2 not in joueurs_deja_apparies:
                paire = tuple(sorted([j1, j2]))
                if paire not in paires_existantes:
                    nouveaux_matchs.append([j1, j2, "à jouer", "", ""])
                    paires_existantes.add(paire)
                    joueurs_deja_apparies.add(j1)
                    joueurs_deja_apparies.add(j2)
                    break
    
    return nouveaux_matchs


# Tableau complet avec mise en surbrillance du joueur sélectionné
def highlight_joueur(row):
    if row.name == joueur:
        return ['background-color: #90EE90; font-weight: bold'] * len(row)  # vert
    return [''] * len(row)

########################
# Choix du mode de jeu #
########################
st.divider()
mode = st.radio(
    "Mode de jeu",
    ["🏆 Tournoi/Championnat", "🎲 Jeu libre"],
    horizontal=True
)
st.divider()

############################
# Mode tournoi/championnat #
############################
if mode == "🏆 Tournoi/Championnat":

    # Onglets de l'application
    tabs = st.tabs(["👥 Participants", "🎪 Tournoi", "➕ Saisie résultat", "📊 Confrontations", "🏆 Classement"])
    
    # --- Onglet Participants ---
    with tabs[0]:
        st.header("👥 Sélection des participants")
        
        if not df_tournoi.empty:
            st.info(f"✅ Le tournoi est déjà lancé avec {len(joueurs_tournoi)} participants")
            st.write("**Participants :**")
            for j in sorted(joueurs_tournoi):
                st.write(f"• {j}")
            
            st.divider()
            st.warning("⚠️ Pour modifier les participants, il faut réinitialiser le tournoi (supprimer toutes les lignes de l'onglet 'tournoi' dans le spreadsheet)")
        
        else:
            st.write("Sélectionne les joueurs qui participeront au tournoi :")
            
            # Initialiser la sélection dans session_state
            if 'joueurs_selectionnes' not in st.session_state:
                st.session_state.joueurs_selectionnes = liste_joueurs_complet.copy()
            
            # Créer des checkboxes pour chaque joueur
            col1, col2 = st.columns(2)
            mid = len(liste_joueurs_complet) // 2
            
            with col1:
                for j in liste_joueurs_complet[:mid]:
                    checked = st.checkbox(j, value=j in st.session_state.joueurs_selectionnes, key=f"cb_{j}")
                    if checked and j not in st.session_state.joueurs_selectionnes:
                        st.session_state.joueurs_selectionnes.append(j)
                    elif not checked and j in st.session_state.joueurs_selectionnes:
                        st.session_state.joueurs_selectionnes.remove(j)
            
            with col2:
                for j in liste_joueurs_complet[mid:]:
                    checked = st.checkbox(j, value=j in st.session_state.joueurs_selectionnes, key=f"cb_{j}")
                    if checked and j not in st.session_state.joueurs_selectionnes:
                        st.session_state.joueurs_selectionnes.append(j)
                    elif not checked and j in st.session_state.joueurs_selectionnes:
                        st.session_state.joueurs_selectionnes.remove(j)
            
            st.divider()
            
            joueurs_selectionnes = st.session_state.joueurs_selectionnes
            
            if len(joueurs_selectionnes) < 2:
                st.error("⚠️ Sélectionne au moins 2 joueurs pour lancer le tournoi")
            else:
                st.success(f"✅ {len(joueurs_selectionnes)} joueurs sélectionnés")
                
                nb_parties_total = len(joueurs_selectionnes) * (len(joueurs_selectionnes) - 1) // 2
                st.info(f"📊 Ce tournoi nécessitera **{nb_parties_total} parties** au total ({len(joueurs_selectionnes) - 1} par joueur)")
                
                st.divider()
                
                col_init1, col_init2, col_init3 = st.columns([2, 1, 1])
                with col_init1:
                    nb_matchs_init = st.slider("Nombre de matchs à générer", 1, min(20, nb_parties_total), min(10, nb_parties_total))
                
                with col_init2:
                    st.write("")
                    st.write("")
                    if st.button("🎲 Aléatoire", use_container_width=True):
                        nouveaux_matchs = generer_appariements_aleatoires(nb_matchs_init, joueurs_selectionnes)
                        
                        for match in nouveaux_matchs:
                            tournoi_sheet.append_row(match)
                        
                        # Recharger les données du tournoi
                        tournoi_rows = tournoi_sheet.get_all_records()
                        st.session_state.df_tournoi = pd.DataFrame(tournoi_rows)
                        
                        st.success(f"✅ {len(nouveaux_matchs)} matchs aléatoires générés !")
                        st.rerun()
                
                with col_init3:
                    st.write("")
                    st.write("")
                    if st.button("🎯 Ronde suisse", use_container_width=True):
                        nouveaux_matchs = generer_appariements_aleatoires(nb_matchs_init, joueurs_selectionnes)
                        
                        for match in nouveaux_matchs:
                            tournoi_sheet.append_row(match)
                        
                        # Recharger les données du tournoi
                        tournoi_rows = tournoi_sheet.get_all_records()
                        st.session_state.df_tournoi = pd.DataFrame(tournoi_rows)
                        
                        st.success(f"✅ {len(nouveaux_matchs)} matchs générés !")
                        st.rerun()
    
    # --- Onglet Tournoi ---
    with tabs[1]:
        st.header("🎪 Gestion du Tournoi")
        
        if df_tournoi.empty:
            st.warning("⚠️ Voir dans l'onglet **👥 Participants** pour lancer le tournoi")
        
        else:
            # Statistiques globales
            nb_total = len(joueurs_tournoi) * (len(joueurs_tournoi) - 1) // 2
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
            
            # Afficher les matchs en cours
            matchs_en_cours = df_tournoi[df_tournoi["statut"] == "à jouer"]
            
            if not matchs_en_cours.empty:
                st.subheader("⚡ Matchs à jouer")
                for _, match in matchs_en_cours.iterrows():
                    st.info(f"🎯 **{match['joueur_1']}** vs **{match['joueur_2']}**")
            
            st.divider()
            
            # Boutons pour générer plus de matchs
            st.subheader("➕ Générer de nouveaux appariements")
            
            col_gen1, col_gen2, col_gen3 = st.columns([2, 1, 1])
            with col_gen1:
                nb_nouveaux = st.slider("Nombre de nouveaux matchs", 1, 10, 5)
            
            with col_gen2:
                st.write("")
                st.write("")
                if st.button("🎲 Aléatoire", use_container_width=True, key="btn_aleatoire"):
                    nouveaux = generer_appariements_aleatoires(nb_nouveaux, joueurs_tournoi)
                    
                    if nouveaux:
                        for match in nouveaux:
                            tournoi_sheet.append_row(match)
                        
                        # Recharger les données du tournoi
                        tournoi_rows = tournoi_sheet.get_all_records()
                        st.session_state.df_tournoi = pd.DataFrame(tournoi_rows)
                        
                        st.success(f"✅ {len(nouveaux)} matchs aléatoires générés !")
                        st.rerun()
                    else:
                        st.warning("⚠️ Impossible de générer plus de matchs")
            
            with col_gen3:
                st.write("")
                st.write("")
                if st.button("🎯 Ronde suisse", use_container_width=True, key="btn_suisse"):
                    nouveaux = generer_appariements_suisse(nb_nouveaux, joueurs_tournoi)
                    
                    if nouveaux:
                        for match in nouveaux:
                            tournoi_sheet.append_row(match)
                        
                        # Recharger les données du tournoi
                        tournoi_rows = tournoi_sheet.get_all_records()
                        st.session_state.df_tournoi = pd.DataFrame(tournoi_rows)
                        
                        st.success(f"✅ {len(nouveaux)} matchs générés !")
                        st.rerun()
                    else:
                        st.warning("⚠️ Impossible de générer plus de matchs")
            
            st.divider()
            
            # Historique complet
            with st.expander("📋 Voir tous les matchs du tournoi"):
                st.dataframe(df_tournoi, use_container_width=True)
    
    # --- Onglet Saisie ---
    with tabs[2]:
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
                    date = pd.to_datetime('now').strftime("%Y-%m-%d %H:%M:%S")
                    
                    st.caption(f"Résultat : **{vainqueur}** 13 - {score_perdant} **{j2 if vainqueur == j1 else j1}**")
                    
                    submitted = st.form_submit_button("✅ Enregistrer", use_container_width=True)
                
                if submitted:
                    # Trouver la ligne du match dans le sheet
                    all_data = tournoi_sheet.get_all_values()
                    row_idx = None
                    
                    for i, row in enumerate(all_data[1:], start=2):  # Skip header, start at row 2
                        if (row[0] == j1 and row[1] == j2) or (row[0] == j2 and row[1] == j1):
                            if row[2] == "à jouer":  # Vérifier que c'est bien un match à jouer
                                row_idx = i
                                break
                    
                    if row_idx:
                        # Mettre à jour le tournoi
                        tournoi_sheet.update(f"C{row_idx}:F{row_idx}", [["terminé", vainqueur, score_perdant, date]])
                        
                        # Recharger les données du tournoi
                        tournoi_rows = tournoi_sheet.get_all_records()
                        st.session_state.df_tournoi = pd.DataFrame(tournoi_rows)
                        
                        st.success("✅ Résultat enregistré !")
                        st.rerun()
                    else:
                        st.error("❌ Erreur : impossible de trouver le match")
    
    # --- Onglet Confrontations ---
    with tabs[3]:
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
                
                if vainq in liste_joueurs and adv in liste_joueurs:
                    recap.loc[vainq, adv] = f"{score_v}-{score_a}"
                    recap.loc[adv, vainq] = f"{score_a}-{score_v}"
            
            st.dataframe(recap, use_container_width=True)
    
    # --- Onglet Classement ---
    with tabs[4]:
        st.header("Classement du tournoi")
        
        stats_tournoi = calculer_stats_tournoi()
        
        if all(s["Victoires"] == 0 and s["Défaites"] == 0 for s in stats_tournoi.values()):
            st.info("Aucune partie terminée pour le moment")
        else:
            classement = pd.DataFrame(stats_tournoi).T
            classement["Parties jouées"] = classement["Victoires"] + classement["Défaites"]
            classement["%_Victoires"] = ((classement["Victoires"] / classement["Parties jouées"]) * 100).round(0).astype(int).astype(str) + "%"
            
            classement = classement.sort_values(by=["%_Victoires", "Diff"], ascending=[False, False])
            
            classement = classement[["Parties jouées", "Victoires", "Défaites", "%_Victoires", "Points_marques", "Points_encaisses", "Diff"]]
            classement.columns = ["J", "V", "D", "%V", "PM", "PE", "Diff"]
            
            st.dataframe(classement, use_container_width=True)

##################
# Mode Jeu libre #
##################
else: 
    tabs = st.tabs(["➕ Saisie résultat", "📊 Statistiques"])
    with tabs[0]:
        # Saisie simplifiée sans lien avec le tournoi
        st.header("Saisie d'un résultat libre")
        # Code de saisie adapté
        
        joueur_A = st.selectbox("Joueur A", options=liste_joueurs_complet, key="joueur_A")
        joueur_B = st.selectbox("Joueur B", options=[j for j in liste_joueurs_complet if j != joueur_A], key="joueur_B")
        with st.form("saisie_resultat_open"):
            # Vainqueur dépend des joueurs choisis
            
            vainqueur = st.radio("Qui a gagné ?", [joueur_A, joueur_B])
            score_perdant = st.number_input("Score du perdant", min_value=0, max_value=12, value=0)
            date = pd.to_datetime('now').strftime("%Y-%m-%d %H:%M:%S")
                    
            st.caption(f"Résultat : **{vainqueur}** 13 - {score_perdant} **{joueur_B if vainqueur == joueur_A else joueur_A}**")
                    
            submitted = st.form_submit_button("✅ Enregistrer", use_container_width=True)

        if submitted:
            # Ajouter aussi dans les résultats généraux
            perdant = joueur_B if vainqueur == joueur_A else joueur_A
            resultats.append_row([vainqueur, perdant, 13, score_perdant, date])
            st.success("✅ Résultat enregistré !")
            st.rerun()
    
    with tabs[1]:
        # Statistiques globales tous joueurs
        st.header("Choisissez un joueur pour afficher ses stats et le mettre en surbrillance dans le tableau")
        # Classement basé sur tous les résultats
        stats = calculer_stats()

        # Sélection d'un joueur à afficher
        joueur = st.selectbox("Choix du joueur", options=liste_joueurs_complet, key="joueur")

        # Mise en forme des stats
        stats_tab = pd.DataFrame(stats).T
        
        # Calcul de stats additionnelles
        stats_tab["Parties jouées"] = stats_tab["Victoires"] + stats_tab["Défaites"]
        stats_tab["%_Victoires"] = ((stats_tab["Victoires"] / stats_tab["Parties jouées"]) * 100).fillna(0).replace([float('inf'), -float('inf')], 0).round(0).astype(int).astype(str) + "%"
        
        # Affichage des statistiques
        stats_tab = stats_tab[["Parties jouées", "Victoires", "Défaites", "%_Victoires", "Points_marques", "Points_encaisses", "Diff", "Tôle_infligées", "Tôle_encaissées"]]
        stats_tab.columns = ["Joué", "Vict", "Déf", "%Vict", "PM", "PE", "Diff", "0-infli", "0-encais"]
        # Afficher sous forme de métriques plutôt qu'un tableau
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Parties jouées", stats_tab.loc[joueur, "Joué"])
        with col2:
            st.metric("Victoires", stats_tab.loc[joueur, "Vict"])
        with col3:
            st.metric("Défaites", stats_tab.loc[joueur, "Déf"])
        with col4:
            st.metric("% Victoires", stats_tab.loc[joueur, "%Vict"])
        with col5:
            st.metric("Différence points", stats_tab.loc[joueur, "Diff"])

        st.divider()

        # Affichage du tableau complet
        stats_tab_styled = stats_tab.style.apply(highlight_joueur, axis=1)
        st.dataframe(stats_tab_styled, use_container_width=True)
