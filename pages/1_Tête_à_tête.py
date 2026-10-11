import streamlit as st
import gspread
import pandas as pd
import random
import networkx as nx
import itertools
import sys
sys.path.append('..')  # Pour importer depuis la racine
from utils import init_google_sheets

#############
# Affichage #
#############
st.set_page_config(page_title="Tête-à-tête", page_icon="👤")
st.image("images/petanque_1.jpg", use_container_width=True)
st.write("# Parties en tête-à-tête du club de pétanque de Vaux-sur-Seine")

#######################
# Liens et chargement #
#######################
# Utiliser les données en cache
init_google_sheets()
liste_joueurs_complet = st.session_state.liste_joueurs_complet

# Charger les matchs du tournoi tête-à-tête
tournoi_tat_rows = st.session_state.sheet_tournoi_tat.get_all_records()
tournoi_tat_df = pd.DataFrame(tournoi_tat_rows)

# Charger les matchs du championnat tête-à-tête
championnat_tat_rows = st.session_state.sheet_championnat_tat.get_all_records()
championnat_tat_df = pd.DataFrame(championnat_tat_rows)

# Charger les parties en jeu libre tête-à-tête
resultats_tat_rows = st.session_state.sheet_resultats_tat.get_all_records()
resultats_tat_df = pd.DataFrame(resultats_tat_rows)

# Récupérer les joueurs participant au tournoi
joueurs_tournoi = []
if not tournoi_tat_df.empty:
    j1_list = tournoi_tat_df["joueur_1"].unique().tolist()
    j2_list = tournoi_tat_df["joueur_2"].unique().tolist()
    joueurs_tournoi = list(set(j1_list + j2_list))
    liste_joueurs = joueurs_tournoi
else:
    liste_joueurs = liste_joueurs_complet

joueurs_championnat = []
if not championnat_tat_df.empty:
    j1_list = championnat_tat_df["joueur_1"].unique().tolist()
    j2_list = championnat_tat_df["joueur_2"].unique().tolist()
    joueurs_championnat = list(set(j1_list + j2_list))
    liste_joueurs = joueurs_championnat
else:
    liste_joueurs = liste_joueurs_complet

#############
# Fonctions #
#############

# Fonction pour calculer les stats du tournoi actuel
####################################################
def calculer_stats_tournoi():
    stats_tournoi = {j: {"Victoires": 0, "Défaites": 0, "Points_marques": 0, "Points_encaisses": 0, "Diff": 0, "Tôle_infligées": 0, "Tôle_encaissées": 0} for j in joueurs_tournoi}
    
    if not tournoi_tat_df.empty:
        for _, row in tournoi_tat_df.iterrows():
            if row["statut"] == "terminé":
                vainq = row["vainqueur"]
                perdant = row["adversaire"]
                score_v = row.get("score_vainqueur", 13)
                score_p = row.get("score_adversaire", 0)
                
                if vainq in stats_tournoi:
                    stats_tournoi[vainq]["Victoires"] += 1
                    stats_tournoi[vainq]["Points_marques"] += score_v
                    stats_tournoi[vainq]["Points_encaisses"] += score_p
                    if score_p == 0: 
                        stats_tournoi[vainq]["Tôle_infligées"] += 1
                
                if perdant in stats_tournoi:
                    stats_tournoi[perdant]["Défaites"] += 1
                    stats_tournoi[perdant]["Points_marques"] += score_p
                    stats_tournoi[perdant]["Points_encaisses"] += score_v
                    if score_p == 0:
                        stats_tournoi[perdant]["Tôle_encaissées"] += 1
    
    for j in stats_tournoi:
        stats_tournoi[j]["Diff"] = stats_tournoi[j]["Points_marques"] - stats_tournoi[j]["Points_encaisses"]
    
    return stats_tournoi

# Fonction pour calculer les stats du championnat actuel
########################################################
def calculer_stats_championnat():
    stats_championnat = {j: {"Victoires": 0, "Défaites": 0, "Points_marques": 0, "Points_encaisses": 0, "Diff": 0, "Tôle_infligées": 0, "Tôle_encaissées": 0} for j in liste_joueurs}
    
    if not championnat_tat_df.empty:
        for _, row in championnat_tat_df.iterrows():
            if row["statut"] == "terminé":
                vainq = row["vainqueur"]
                perdant = row["adversaire"]
                score_v = row.get("score_vainqueur", 13)
                score_p = row.get("score_adversaire", 0)
                
                if vainq in stats_championnat:
                    stats_championnat[vainq]["Victoires"] += 1
                    stats_championnat[vainq]["Points_marques"] += score_v
                    stats_championnat[vainq]["Points_encaisses"] += score_p
                    if score_p == 0: 
                        stats_championnat[vainq]["Tôle_infligées"] += 1
                
                if perdant in stats_championnat:
                    stats_championnat[perdant]["Défaites"] += 1
                    stats_championnat[perdant]["Points_marques"] += score_p
                    stats_championnat[perdant]["Points_encaisses"] += score_v
                    if score_p == 0:
                        stats_championnat[perdant]["Tôle_encaissées"] += 1
    
    for j in stats_championnat:
        stats_championnat[j]["Diff"] = stats_championnat[j]["Points_marques"] - stats_championnat[j]["Points_encaisses"]
    
    return stats_championnat

# Fonction pour calculer les stats du jeu libre
###############################################
def calculer_stats():
    stats = {j: {"Victoires": 0, "Défaites": 0, "Points_marques": 0, "Points_encaisses": 0, "Diff": 0, "Tôle_infligées": 0, "Tôle_encaissées": 0} for j in liste_joueurs_complet}
    
    if not resultats_tat_df.empty:  # resultats_tat_df correspond au dataframe lié à la feuille "résultats_tat"
        for _, row in resultats_tat_df.iterrows():
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

# Fonction pour générer les appariements en tournoi (ronde suisse)
##################################################################
def generer_appariements_suisse(nb_matchs, joueurs_liste):
    """
    Génère les appariements du prochain tour selon un système de ronde suisse :
    - Priorité aux matchs entre joueurs proches au classement
    - Aucune paire répétée
    - Nombre maximal de matchs sans doublons
    """

    # --- Déterminer le numéro du tour ---
    if not tournoi_tat_df.empty and "tour n°" in tournoi_tat_df.columns:
        tours_existants = tournoi_tat_df["tour n°"].astype(str)
        dernier_tour = 0
        for t in tours_existants:
            if t.startswith("Tour "):
                try:
                    dernier_tour = max(dernier_tour, int(t.replace("Tour ", "")))
                except ValueError:
                    pass
        num_tour = dernier_tour + 1
    else:
        num_tour = 1

    # --- Cas 1 : premier tour ---
    if tournoi_tat_df.empty:
        random.shuffle(joueurs_liste)
        nouveaux_matchs = []

        for i in range(0, len(joueurs_liste) - 1, 2):
            j1, j2 = joueurs_liste[i], joueurs_liste[i + 1]
            nouveaux_matchs.append([j1, j2, f"Tour {num_tour}", "à jouer", "", ""])

        # Si nombre impair de joueurs, dernier joueur est exempt
        if len(joueurs_liste) % 2 != 0:
            nouveaux_matchs.append([joueurs_liste[-1], "Exempt", f"Tour {num_tour}", "à jouer", "", ""])

        return nouveaux_matchs

    # --- Cas 2 : tournoi en cours ---
    # Identifier les paires déjà jouées
    paires_existantes = set()
    for _, row in tournoi_tat_df.iterrows():
        j1, j2 = sorted([row["joueur_1"], row["joueur_2"]])
        paires_existantes.add((j1, j2))

    # Calculer le classement
    stats_tournoi = calculer_stats_tournoi()
    classement = sorted(
        stats_tournoi.items(),
        key=lambda x: (x[1]["Victoires"], x[1]["Diff"], random.random()),
        reverse=True
    )
    joueurs_classes = [j[0] for j in classement if j[0] in joueurs_liste]

    # Graphe de compatibilité
    G = nx.Graph()
    G.add_nodes_from(joueurs_classes)
    position = {joueur: i for i, joueur in enumerate(joueurs_classes)}

    # Ajouter des arêtes pondérées selon la proximité au classement
    for i, j in itertools.combinations(joueurs_classes, 2):
        paire = tuple(sorted([i, j]))
        if paire not in paires_existantes:
            distance = abs(position[i] - position[j])
            poids = 1000 - distance  # plus la distance est petite, plus le poids est élevé
            G.add_edge(i, j, weight=poids)

    # ✅ Vérifier s'il reste des matchs possibles
    if G.number_of_edges() == 0:
        st.warning("✅ Toutes les rencontres possibles ont déjà été jouées !")
        return []

    # Trouver le matching maximal pondéré
    matching = list(nx.max_weight_matching(G, maxcardinality=True))
    matching.sort()

    # Convertir le matching en liste de matchs
    nouveaux_matchs = [[i, j, f"Tour {num_tour}", "à jouer", "", ""] for i, j in matching]

    # Si nombre impair de joueurs : ajouter un exempt
    joueurs_utilises = {i for m in matching for i in m}
    restants = [j for j in joueurs_classes if j not in joueurs_utilises]
    if restants:
        nouveaux_matchs.append([restants[0], "Exempt", f"Tour {num_tour}", "à jouer", "", ""])

    return nouveaux_matchs[:nb_matchs]

# Fonction pour générer les appariements complet du championnat
###############################################################
def generer_appariements_aleatoires(joueurs, seed=None):
    """
    Retourne une liste de rounds; chaque round est une liste de paires (j1, j2).
    Pour n impair, on ajoute 'BYE' (match contre BYE = repos).
    """
    if seed is not None:
        random.seed(seed)
    joueurs = list(joueurs)
    random.shuffle(joueurs)  # randomiser l'ordre initial
    n = len(joueurs)
    bye = None
    if n % 2 == 1:
        bye = "BYE"
        joueurs.append(bye)
        n += 1

    rounds = []
    # méthode du cercle : on fixe joueurs[0], on fait tourner le reste
    for r in range(n - 1):
        paires = []
        for i in range(n // 2):
            a = joueurs[i]
            b = joueurs[n - 1 - i]
            if a != bye and b != bye:
                paires.append((a, b, f"Tour {r+1}", "à jouer"))
        rounds.append(paires)
        # rotation (fixer joueurs[0])
        joueurs = [joueurs[0]] + [joueurs[-1]] + joueurs[1:-1]
    return rounds

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
    ["🎲 Jeu libre", "🏅 Championnat", "🏆 Tournoi"],
    horizontal=True
)
st.divider()

################
# Mode tournoi #
################
if mode == "🏆 Tournoi":

    # Onglets de l'application
    tabs = st.tabs(["👥 Participants", "🎪 Tournoi", "➕ Saisie résultat", "📊 Confrontations", "🏆 Classement"])
    
    # --------------------------- # 
    # --- Onglet Participants --- #
    # --------------------------- #
    with tabs[0]:
        st.header("👥 Sélection des participants")
        
        if not tournoi_tat_df.empty:
            st.info(f"✅ Le tournoi est déjà lancé avec {len(joueurs_tournoi)} participants")
            st.write("**Participants :**")
            for j in sorted(joueurs_tournoi):
                st.write(f"• {j}")
            
            st.divider()

            st.warning("⚠️ Pour modifier les participants, il faut réinitialiser le tournoi (Contacter Stef-la-pétanque)")
        
        else:
            st.write("Sélectionner les joueurs qui participeront au tournoi :")
            
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
                nb_parties_tour = round(len(joueurs_selectionnes) // 2)
                nb_parties_total = len(joueurs_selectionnes) * (len(joueurs_selectionnes) - 1) // 2
                st.info(f"📊 Ce tournoi nécessitera **{nb_parties_total} parties** au total ({len(joueurs_selectionnes) - 1} par joueur)")
                
                st.divider()
                
                if st.button("🎲 Création du tournoi", use_container_width=True, key="btn_aleatoire"):
                    nouveaux_matchs = generer_appariements_suisse(nb_parties_tour, joueurs_selectionnes)
                    for match in nouveaux_matchs:
                        st.session_state.sheet_tournoi_tat.append_row(match)
                        
                    # Recharger les données du tournoi
                    st.session_state.tournoi_tat_df = pd.DataFrame(tournoi_tat_rows)
                        
                    st.success(f"✅ {len(nouveaux_matchs)} matchs générés !")
                    st.rerun()

    # ---------------------- # 
    # --- Onglet Tournoi --- #
    # ---------------------- # 
    with tabs[1]:
        st.header("🎪 Gestion du Tournoi")
        
        if tournoi_tat_df.empty:
            st.warning("⚠️ Voir dans l'onglet **👥 Participants** pour lancer le tournoi")
        
        else:
            # Calculs nécéssaires
            nb_total = len(joueurs_tournoi) * (len(joueurs_tournoi) - 1) // 2
            nb_parties_tour = round(len(liste_joueurs) // 2)
            nb_joues = len(tournoi_tat_df[tournoi_tat_df["statut"] == "terminé"]) if not tournoi_tat_df.empty else 0
            nb_en_cours = len(tournoi_tat_df[tournoi_tat_df["statut"] == "à jouer"]) if not tournoi_tat_df.empty else 0
            
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
            
            # - Afficher la liste des parties en cours - #
            parties_en_cours = tournoi_tat_df[tournoi_tat_df["statut"] == "à jouer"]
            
            if not parties_en_cours.empty:
                st.subheader("⚡ Parties à jouer")
                st.write("")
                st.write("")
                for tour_num, groupe in parties_en_cours.groupby("tour n°"):
                    st.markdown(f"### 🏁 {str(tour_num)}")
                    for _, parties in groupe.iterrows():
                        st.info(f"🎯 **{parties['joueur_1']}** vs **{parties['joueur_2']}**")
            
            st.divider()

            # - Afficher la liste des parties terminés - #
            parties_termines = tournoi_tat_df[tournoi_tat_df["statut"] == "terminé"]

            if not parties_termines.empty:
                st.subheader("✅ Parties terminés")
                for tour_num, groupe in parties_termines.groupby("tour n°"):
                    st.markdown(f"### 🏁 {str(tour_num)}")
                    for _, parties in groupe.iterrows():
                        st.info(f"🎯 **{parties['joueur_1']}** vs **{parties['joueur_2']}**")


            st.subheader("➕ Générer de nouveaux appariements")
            
            ################################
            # Appel au bouton ronde suisse #
            ################################
            st.write("")
            st.write("")
            if st.button("🎯 Ronde suisse", use_container_width=True, key="btn_suisse"):

                # --- Vérification de sécurité : matchs encore en cours ---
                if not tournoi_tat_df.empty:
                    matchs_en_cours = tournoi_tat_df[tournoi_tat_df["statut"] == "à jouer"]
                    if not matchs_en_cours.empty:
                        st.error("⚠️ Des matchs du tour précédent sont encore en cours. Toutes les parties doivent être terminées avant de générer le prochain tour.")
                        st.stop()

                nouveaux = generer_appariements_suisse(nb_parties_tour, joueurs_tournoi)
                    
                if nouveaux:
                    for match in nouveaux:
                        st.session_state.sheet_tournoi_tat.append_row(match)
                        
                    # Recharger les données du tournoi
                    tournoi_tat_rows = st.session_state.sheet_tournoi_tat.get_all_records()
                    st.session_state.tournoi_tat_df = pd.DataFrame(tournoi_tat_rows)
                        
                    st.success(f"✅ {len(nouveaux)} matchs générés !")
                    st.rerun()
                else:
                    st.warning("⚠️ Impossible de générer plus de matchs")

            st.warning("⚠️ L'appariement **'Ronde suisse'** fait s'affronter en priorité des joueurs au classement similaire")

            st.divider()
            
            # Historique complet
            with st.expander("📋 Voir tous les matchs du tournoi"):
                st.dataframe(tournoi_tat_df, use_container_width=True)
    
    # --------------------- #
    # --- Onglet Saisie --- #
    # --------------------- #
    with tabs[2]:
        st.header("Saisie d'un résultat")
        
        # Récupérer les matchs à jouer
        matchs_disponibles = []
        if not tournoi_tat_df.empty:
            matchs_a_jouer = tournoi_tat_df[tournoi_tat_df["statut"] == "à jouer"]
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
                    if vainqueur == j1:
                        perdant = j2 
                    else: 
                        perdant = j1
                    score_vainqueur = 13
                    score_perdant = st.number_input("Score du perdant", min_value=0, max_value=12, value=0)
                    date = pd.to_datetime('now').strftime("%Y-%m-%d %H:%M:%S")
                    
                    st.caption(f"Résultat : **{vainqueur}** 13 - {score_perdant} **{j2 if vainqueur == j1 else j1}**")
                    
                    submitted = st.form_submit_button("✅ Enregistrer", use_container_width=True)
                
                if submitted:
                    # Trouver la ligne du match dans le sheet
                    all_data = st.session_state.sheet_tournoi_tat.get_all_values()
                    row_idx = None
                    
                    for i, row in enumerate(all_data[1:], start=2):  # Skip header, start at row 2
                        if (row[0] == j1 and row[1] == j2) or (row[0] == j2 and row[1] == j1):
                            if row[3] == "à jouer":  # Vérifier que c'est bien un match à jouer
                                row_idx = i
                                break
                    
                    if row_idx:
                        # Mettre à jour le tournoi
                        st.session_state.sheet_tournoi_tat.update(f"D{row_idx}:I{row_idx}", [["terminé", vainqueur, perdant, score_vainqueur, score_perdant, date]])
                        
                        # Recharger les données du tournoi
                        tournoi_tat_rows = st.session_state.sheet_tournoi_tat.get_all_records()
                        st.session_state.tournoi_tat_df = pd.DataFrame(tournoi_tat_rows)
                        
                        st.success("✅ Résultat enregistré !")
                        st.rerun()
                    else:
                        st.error("❌ Erreur : impossible de trouver le match")
    
    # ----------------------------- #
    # --- Onglet Confrontations --- #
    # ----------------------------- #
    with tabs[3]:
        st.header("Tableau des confrontations")
        
        if tournoi_tat_df.empty:
            st.info("Aucun résultat enregistré pour le moment")
        else:
            recap = pd.DataFrame("", index=joueurs_tournoi, columns=joueurs_tournoi)
            
            for _, row in tournoi_tat_df.iterrows():
                vainq = row["vainqueur"]
                adv = row["adversaire"]
                score_v = row.get("score_vainqueur", 13)
                score_a = row.get("score_adversaire", row.get("score_adv", 0))
                
                if vainq in liste_joueurs and adv in liste_joueurs:
                    recap.loc[vainq, adv] = f"{score_v}-{score_a}"
                    recap.loc[adv, vainq] = f"{score_a}-{score_v}"
            
            st.dataframe(recap, use_container_width=True)

    # ------------------------- #
    # --- Onglet Classement --- #
    # ------------------------- #
    with tabs[4]:
        st.header("Classement du tournoi")
        st.subheader("Choisir un joueur pour afficher ses stats et le mettre en surbrillance dans le tableau")        

        # Calcul des stats
        stats_tournoi = calculer_stats_tournoi()

        # Sélection du joueur à afficher
        joueur = st.selectbox("Choix du joueur", options=joueurs_tournoi, key="joueur")

        # Mise en forme des stats
        classement = pd.DataFrame(stats_tournoi).T
        classement["Parties jouées"] = classement["Victoires"] + classement["Défaites"]
        classement["%_Victoires"] = ((classement["Victoires"] / classement["Parties jouées"]) * 100).fillna(0).replace([float('inf'), -float('inf')], 0).round(0).astype(int).astype(str) + "%"
        classement = classement.sort_values(by=["Victoires", "Diff"], ascending=[False, False])
        classement = classement[["Parties jouées", "Victoires", "Défaites", "%_Victoires", "Points_marques", "Points_encaisses", "Diff", "Tôle_infligées", "Tôle_encaissées"]]
        classement.columns = ["Joué", "Victoires", "Défaites", "% Victoires", "Points Marqués", "Points Encaissés", "Différence de points", "Tôle infligées", "Tôle encaissées"]

        # Afficher les principales métriques
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Parties jouées", classement.loc[joueur, "Joué"])
        with col2:
            st.metric("% Victoires", classement.loc[joueur, "% Victoires"])
        with col3:
            st.metric("Différence de points", classement.loc[joueur, "Différence de points"])

        st.divider()
        classement_styled = classement.style.apply(highlight_joueur, axis=1)
        st.dataframe(classement_styled, use_container_width=True)

####################
# Mode Championnat #
####################
elif mode == "🏅 Championnat":

    # Onglets de l'application
    tabs = st.tabs(["👥 Participants", "🎪 Championnat", "➕ Saisie résultat", "📊 Confrontations", "🏅 Classement"])
    
    # --------------------------- # 
    # --- Onglet Participants --- #
    # --------------------------- #
    with tabs[0]:
        st.header("👥 Sélection des participants")
        
        if not championnat_tat_df.empty:
            st.info(f"✅ Le championnat est déjà lancé avec {len(joueurs_championnat)} participants")
            st.write("**Participants :**")
            for j in sorted(joueurs_championnat):
                st.write(f"• {j}")
            
            st.divider()

            st.warning("⚠️ Pour modifier les participants, il faut réinitialiser le championnat (Contacter Stef-la-pétanque)")
        
        else:
            st.write("Sélectionner les joueurs qui participeront au championnat :")
            
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
                st.error("⚠️ Sélectionne au moins 2 joueurs pour lancer le championnat")
            else:
                st.success(f"✅ {len(joueurs_selectionnes)} joueurs sélectionnés")
                nb_parties_tour = round(len(joueurs_selectionnes) // 2)
                nb_parties_total = len(joueurs_selectionnes) * (len(joueurs_selectionnes) - 1) // 2
                st.info(f"📊 Ce tournoi nécessitera **{nb_parties_total} parties** au total ({len(joueurs_selectionnes) - 1} par joueur)")
                
                st.divider()
                
                if st.button("🎲 Création du championnat", use_container_width=True, key="btn_aleatoire"):
                    nouveaux_matchs = generer_appariements_aleatoires(joueurs_selectionnes, seed=42)
                    for match in nouveaux_matchs:
                        st.session_state.sheet_championnat_tat.append_rows(list(match))
                        
                    # Recharger les données du tournoi
                    st.session_state.championnat_tat_df = pd.DataFrame(tournoi_tat_rows)
                        
                    st.success(f"✅ {len(nouveaux_matchs)} matchs générés !")
                    st.rerun()

    # -------------------------- # 
    # --- Onglet championnat --- #
    # -------------------------- # 
    with tabs[1]:
        st.header("🎪 Gestion du championnat")
        
        if championnat_tat_df.empty:
            st.warning("⚠️ Voir dans l'onglet **👥 Participants** pour lancer le championnat")
        
        else:
            # Calculs nécéssaires
            nb_total = len(joueurs_championnat) * (len(joueurs_championnat) - 1) // 2
            nb_parties_tour = round(len(liste_joueurs) // 2)
            nb_joues = len(championnat_tat_df[championnat_tat_df["statut"] == "terminé"]) if not championnat_tat_df.empty else 0
            nb_en_cours = len(championnat_tat_df[championnat_tat_df["statut"] == "à jouer"]) if not championnat_tat_df.empty else 0
            
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
            
            # - Afficher la liste des parties en cours - #
            parties_en_cours = championnat_tat_df[championnat_tat_df["statut"] == "à jouer"]
            
            if not parties_en_cours.empty:
                st.subheader("⚡ Parties à jouer")
                st.write("")
                st.write("")

                # Trier les tours par ordre numérique
                parties_en_cours["tour_num"] = parties_en_cours["tour n°"].str.extract(r'(\d+)').astype(int)
                parties_en_cours = parties_en_cours.sort_values("tour_num")

                for tour_num, groupe in parties_en_cours.groupby("tour_num"):
                    st.markdown(f"### 🏁 Tour {tour_num}")
                    for _, parties in groupe.iterrows():
                        st.info(f"🎯 **{parties['joueur_1']}** vs **{parties['joueur_2']}**")
            
            st.divider()

            # - Afficher la liste des parties terminés - #
            parties_termines = championnat_tat_df[championnat_tat_df["statut"] == "terminé"]

            if not parties_termines.empty:
                st.subheader("✅ Parties terminés")

                # Trier les tours par ordre numérique
                parties_termines["tour_num"] = parties_termines["tour n°"].str.extract(r'(\d+)').astype(int)
                parties_termines = parties_termines.sort_values("tour_num")

                for tour_num, groupe in parties_termines.groupby("tour_num"):
                    st.markdown(f"### 🏁 Tour {tour_num}")
                    for _, parties in groupe.iterrows():
                        st.info(f"🎯 **{parties['joueur_1']}** vs **{parties['joueur_2']}**")

            st.divider()
            
            # Historique complet
            with st.expander("📋 Voir tous les matchs du championnat"):
                st.dataframe(championnat_tat_df, use_container_width=True)
    
    # --------------------- #
    # --- Onglet Saisie --- #
    # --------------------- #
    with tabs[2]:
        st.header("Saisie d'un résultat de championnat")
        
        # Récupérer les matchs à jouer
        matchs_disponibles = []
        if not championnat_tat_df.empty:
            matchs_a_jouer = championnat_tat_df[championnat_tat_df["statut"] == "à jouer"]
            for _, match in matchs_a_jouer.iterrows():
                matchs_disponibles.append(f"{match['joueur_1']} vs {match['joueur_2']}")
        
        if not matchs_disponibles:
            st.warning("⚠️ Aucun match en attente. Va dans l'onglet 🎪 Championnat pour en générer !")
        else:
            match_selectionne = st.selectbox("Sélectionne le match", matchs_disponibles)
            
            if match_selectionne:
                j1, j2 = match_selectionne.replace(" vs ", "|").split("|")
                
                st.divider()
                
                with st.form("saisie_resultat_championnat"):
                    vainqueur = st.radio("Qui a gagné ?", [j1, j2])
                    if vainqueur == j1:
                        perdant = j2 
                    else: 
                        perdant = j1
                    score_vainqueur = 13
                    score_perdant = st.number_input("Score du perdant", min_value=0, max_value=12, value=0)
                    date = pd.to_datetime('now').strftime("%Y-%m-%d %H:%M:%S")
                    
                    st.caption(f"Résultat : **{vainqueur}** 13 - {score_perdant} **{j2 if vainqueur == j1 else j1}**")
                    
                    submitted = st.form_submit_button("✅ Enregistrer", use_container_width=True)
                
                if submitted:
                    # Trouver la ligne du match dans le sheet
                    all_data = st.session_state.sheet_championnat_tat.get_all_values()
                    row_idx = None
                    
                    for i, row in enumerate(all_data[1:], start=2):  # Skip header, start at row 2
                        if (row[0] == j1 and row[1] == j2) or (row[0] == j2 and row[1] == j1):
                            if row[3] == "à jouer":  # Vérifier que c'est bien un match à jouer
                                row_idx = i
                                break
                    
                    if row_idx:
                        # Mettre à jour le championnat
                        st.session_state.sheet_championnat_tat.update(f"D{row_idx}:I{row_idx}", [["terminé", vainqueur, perdant, score_vainqueur, score_perdant, date]])
                        
                        # Recharger les données du championnat
                        championnat_tat_rows = st.session_state.sheet_championnat_tat.get_all_records()
                        st.session_state.championnat_tat_df = pd.DataFrame(championnat_tat_rows)
                        
                        st.success("✅ Résultat enregistré !")
                        st.rerun()
                    else:
                        st.error("❌ Erreur : impossible de trouver le match")
    
    # ----------------------------- #
    # --- Onglet Confrontations --- #
    # ----------------------------- #
    with tabs[3]:
        st.header("Tableau des confrontations")
        
        if championnat_tat_df.empty:
            st.info("Aucun résultat enregistré pour le moment")
        else:
            recap = pd.DataFrame("", index=liste_joueurs, columns=liste_joueurs)
            
            for _, row in championnat_tat_df.iterrows():
                vainq = row["vainqueur"]
                adv = row["adversaire"]
                score_v = row.get("score_vainqueur", 13)
                score_a = row.get("score_adversaire", row.get("score_adv", 0))
                
                if vainq in liste_joueurs and adv in liste_joueurs:
                    recap.loc[vainq, adv] = f"{score_v}-{score_a}"
                    recap.loc[adv, vainq] = f"{score_a}-{score_v}"
            
            st.dataframe(recap, use_container_width=True)

    # ------------------------- #
    # --- Onglet Classement --- #
    # ------------------------- #
    with tabs[4]:
        st.header("Classement du championnat")
        st.subheader("Choisissez un joueur pour afficher ses stats et le mettre en surbrillance dans le tableau")
        
        # Calcul des stats
        stats_championnat = calculer_stats_championnat()

        # Sélection du joueur à afficher
        joueur = st.selectbox("Choix du joueur", options=liste_joueurs, key="joueur")

        # Mise en forme des stats        
        classement = pd.DataFrame(stats_championnat).T
        classement["Parties jouées"] = classement["Victoires"] + classement["Défaites"]
        classement["%_Victoires"] = ((classement["Victoires"] / classement["Parties jouées"]) * 100).fillna(0).replace([float('inf'), -float('inf')], 0).round(0).astype(int).astype(str) + "%"
        classement = classement.sort_values(by=["Victoires", "Diff"], ascending=[False, False])
        classement = classement[["Parties jouées", "Victoires", "Défaites", "%_Victoires", "Points_marques", "Points_encaisses", "Diff", "Tôle_infligées", "Tôle_encaissées"]]
        classement.columns = ["Joué", "Victoires", "Défaites", "% Victoires", "Points Marqués", "Points Encaissés", "Différence de points", "Tôle infligées", "Tôle encaissées"]
            
        # Afficher les principales métriques
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Parties jouées", classement.loc[joueur, "Joué"])
        with col2:
            st.metric("% Victoires", classement.loc[joueur, "% Victoires"])
        with col3:
            st.metric("Différence de points", classement.loc[joueur, "Différence de points"])

        st.divider()
        classement_styled = classement.style.apply(highlight_joueur, axis=1)
        st.dataframe(classement_styled, use_container_width=True)

##################
# Mode Jeu libre #
##################
else: 
    tabs = st.tabs(["➕ Saisie résultat", "📊 Statistiques"])
    
    # --------------------- #
    # --- Onglet Saisie --- # 
    # --------------------- #
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
            st.session_state.sheet_resultats_tat.append_row([vainqueur, perdant, 13, score_perdant, date])
            st.success("✅ Résultat enregistré !")
            st.rerun()

    # -------------------- #
    # --- Onglet stats --- #
    # -------------------- #
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
