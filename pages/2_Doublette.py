import streamlit as st
import gspread
import pandas as pd
import random
import networkx as nx
from itertools import combinations
import sys
sys.path.append('..')  # Pour importer depuis la racine
from utils import init_google_sheets

#############
# Affichage #
#############
st.set_page_config(page_title="Doublette", page_icon="👥")
st.image("images/petanque_2.jpg", use_container_width=True)
st.write("# Parties en doublette du club de pétanque de Vaux-sur-Seine")

#######################
# Liens et chargement #
#######################
# Utiliser les données en cache
init_google_sheets()
liste_joueurs_complet = st.session_state.liste_joueurs_complet

# Charger les matchs du tournoi
tournoi_doub_rows = st.session_state.sheet_tournoi_doub.get_all_records()
tournoi_doub_df = pd.DataFrame(tournoi_doub_rows)

# Charger les matchs du championnat
championnat_doub_rows = st.session_state.sheet_championnat_doub.get_all_records()
championnat_doub_df = pd.DataFrame(championnat_doub_rows)

# Charger les résultats existants (jeu libre)
resultats_doub_rows = st.session_state.sheet_resultats_doub.get_all_records()
resultats_doub_df = pd.DataFrame(resultats_doub_rows)

# Récupérer les joueurs participant au tournoi
joueurs_tournoi_doub = []
if not tournoi_doub_df.empty:
    j1_list = tournoi_doub_df["equipe_1"].unique().tolist()
    j2_list = tournoi_doub_df["equipe_2"].unique().tolist()
    joueurs_tournoi_doub = list(set(j1_list + j2_list))
    liste_joueurs_doub = joueurs_tournoi_doub
else:
    liste_joueurs_doub = liste_joueurs_complet

# Récupérer les joueurs participant au championnat
joueurs_championnat_doub = []
if not championnat_doub_df.empty:
    j1_list = championnat_doub_df["equipe_1"].unique().tolist()
    j2_list = championnat_doub_df["equipe_2"].unique().tolist()
    joueurs_championnat_doub = list(set(j1_list + j2_list))
    liste_joueurs_doub = joueurs_championnat_doub
else:
    liste_joueurs_doub = liste_joueurs_complet

#############
# Fonctions #
#############

# Fonction pour générer les appariements complet du tournoi à la mélée
######################################################################
def generer_doublette_melee(joueurs_liste, historique_partenaires, historique_adversaires, nb_matchs_generer=None):
    """
    Génère des appariements pour un concours de doublette à la mélée
    
    Args:
        joueurs_liste: Liste des joueurs disponibles
        historique_partenaires: dict {joueur: {partenaire: nb_fois}}
        historique_adversaires: dict {joueur: {adversaire: nb_fois}}
        nb_matchs_generer: Nombre de matchs à générer (None = maximum possible)
    
    Returns:
        Liste de matchs [[j1, j2, j3, j4], ...] ou None si impossible
    """
    
    n = len(joueurs_liste)
    
    # Vérifier qu'on a un nombre pair de joueurs
    if n % 4 != 0:
        return None, "Le nombre de joueurs doit être un multiple de 4"
    
    if nb_matchs_generer is None:
        nb_matchs_generer = n // 4  # Tous les joueurs jouent
    
    # Créer un graphe pour les paires possibles
    G = nx.Graph()
    G.add_nodes_from(joueurs_liste)
    
    # Ajouter des arêtes pour les paires possibles (pas encore joué ensemble OU moins de 2 fois)
    for i, j in combinations(joueurs_liste, 2):
        nb_fois_partenaires = historique_partenaires.get(i, {}).get(j, 0)
        
        # Contrainte : pas plus de 1 fois partenaire
        if nb_fois_partenaires < 1:
            G.add_edge(i, j, weight=1000 - nb_fois_partenaires)  # Poids élevé pour ceux qui n'ont jamais joué ensemble
    
    # Trouver un matching parfait (paires de partenaires)
    try:
        matching = nx.max_weight_matching(G, maxcardinality=True)
    except:
        return None, "Impossible de créer des paires avec les contraintes actuelles"
    
    if len(matching) < nb_matchs_generer * 2:
        return None, f"Pas assez de paires possibles (besoin de {nb_matchs_generer * 2}, trouvé {len(matching)})"
    
    # Convertir le matching en liste de paires
    paires = list(matching)
    random.shuffle(paires)
    
    # Sélectionner les paires qui vont jouer
    paires_selectionnees = paires[:nb_matchs_generer * 2]
    
    # Créer les matchs en appariant les paires entre elles
    matchs = []
    joueurs_deja_apparies = set()
    
    # Trier les paires par priorité (favoriser ceux qui ne se sont pas affrontés)
    def score_match(paire1, paire2):
        """Calcule un score pour un match (plus élevé = meilleur)"""
        j1, j2 = paire1
        j3, j4 = paire2
        
        score = 0
        
        # Vérifier les confrontations précédentes
        for ja in [j1, j2]:
            for jb in [j3, j4]:
                nb_fois = historique_adversaires.get(ja, {}).get(jb, 0)
                
                # Contrainte : pas plus de 2 fois adversaire
                if nb_fois >= 2:
                    return -1000  # Score très bas, à éviter
                
                # Favoriser ceux qui ne se sont jamais affrontés
                score += (2 - nb_fois) * 10
        
        return score
    
    # Essayer de créer les matchs
    tentatives = 0
    max_tentatives = 100
    
    while len(matchs) < nb_matchs_generer and tentatives < max_tentatives:
        tentatives += 1
        
        # Trouver deux paires disponibles
        paires_disponibles = [p for p in paires_selectionnees 
                             if p[0] not in joueurs_deja_apparies 
                             and p[1] not in joueurs_deja_apparies]
        
        if len(paires_disponibles) < 2:
            break
        
        # Trouver le meilleur appariement
        meilleur_score = -10000
        meilleure_combinaison = None
        
        for i in range(len(paires_disponibles)):
            for j in range(i + 1, len(paires_disponibles)):
                paire1 = paires_disponibles[i]
                paire2 = paires_disponibles[j]
                
                score = score_match(paire1, paire2)
                
                if score > meilleur_score:
                    meilleur_score = score
                    meilleure_combinaison = (paire1, paire2)
        
        if meilleure_combinaison is None or meilleur_score < 0:
            # Pas de bonne combinaison trouvée
            break
        
        paire1, paire2 = meilleure_combinaison
        
        # Créer le match
        match = [paire1[0], paire1[1], paire2[0], paire2[1]]
        matchs.append(match)
        
        # Marquer les joueurs comme appariés
        joueurs_deja_apparies.add(paire1[0])
        joueurs_deja_apparies.add(paire1[1])
        joueurs_deja_apparies.add(paire2[0])
        joueurs_deja_apparies.add(paire2[1])
    
    if len(matchs) < nb_matchs_generer:
        return matchs, f"Seulement {len(matchs)} matchs générés sur {nb_matchs_generer} demandés"
    
    return matchs, None

# Mise à jour de l'historique des appariements à la mélée
#########################################################
def mettre_a_jour_historiques(match, historique_partenaires, historique_adversaires):
    """Met à jour les historiques après un match"""
    j1, j2, j3, j4 = match
    
    # Partenaires
    for ja, jb in [(j1, j2), (j3, j4)]:
        if ja not in historique_partenaires:
            historique_partenaires[ja] = {}
        if jb not in historique_partenaires:
            historique_partenaires[jb] = {}
        
        historique_partenaires[ja][jb] = historique_partenaires[ja].get(jb, 0) + 1
        historique_partenaires[jb][ja] = historique_partenaires[jb].get(ja, 0) + 1
    
    # Adversaires
    for ja in [j1, j2]:
        for jb in [j3, j4]:
            if ja not in historique_adversaires:
                historique_adversaires[ja] = {}
            if jb not in historique_adversaires:
                historique_adversaires[jb] = {}
            
            historique_adversaires[ja][jb] = historique_adversaires[ja].get(jb, 0) + 1
            historique_adversaires[jb][ja] = historique_adversaires[jb].get(ja, 0) + 1


# Fonction pour générer les appariements complet du championnat
###############################################################
def generer_doublette_aleatoires_champ(equipes_doublette, seed=None):
    """
    Retourne une liste de rounds; chaque round est une liste de paires (equipe_1, equipe_2).
    Pour n impair, on ajoute 'BYE' (match contre BYE = repos).
    """
    if seed is not None:
        random.seed(seed)
    equipes = list(equipes_doublette)
    random.shuffle(equipes_doublette)  # randomiser l'ordre initial
    n = len(equipes_doublette)
    bye = None
    if n % 2 == 1:
        bye = "BYE"
        equipes_doublette.append(bye)
        n += 1

    rounds = []
    # méthode du cercle : on fixe equipes_doublette[0], on fait tourner le reste
    for r in range(n - 1):
        paires = []
        for i in range(n // 2):
            a = equipes_doublette[i]
            b = equipes_doublette[n - 1 - i]
            if a != bye and b != bye:
                paires.append((a, b, f"Tour {r+1}", "à jouer"))
        rounds.append(paires)
        # rotation (fixer equipes_doublette[0])
        equipes_doublette = [equipes_doublette[0]] + [equipes_doublette[-1]] + equipes_doublette[1:-1]
    return rounds

# Fonction pour calculer les stats en doublette (jeu libre)
###########################################################

def calculer_stats_doublette(joueur_selectionne=None, partenaire_selectionne=None):
    stats = {j: {"Victoires": 0, "Défaites": 0, "Points_marques": 0, "Points_encaisses": 0, "Diff": 0, "Tôle_infligées": 0, "Tôle_encaissées": 0} for j in liste_joueurs_complet}
    
    if not resultats_doub_df.empty:
        for _, row in resultats_doub_df.iterrows():
            vainq1 = row["vainqueur_1"]
            vainq2 = row["vainqueur_2"]
            adv1 = row["adversaire_1"]
            adv2 = row["adversaire_2"]
            score_v = row.get("score_vainqueur", 13)
            score_p = row.get("score_adversaire", 0)
            
            # Filtrer selon le joueur et partenaire sélectionnés
            if joueur_selectionne and partenaire_selectionne:
                # Vérifier si cette partie concerne le joueur et son partenaire
                if partenaire_selectionne != "Tous":
                    # Cas spécifique : joueur + partenaire précis
                    if not ((joueur_selectionne == vainq1 and partenaire_selectionne == vainq2) or
                            (joueur_selectionne == vainq2 and partenaire_selectionne == vainq1) or
                            (joueur_selectionne == adv1 and partenaire_selectionne == adv2) or
                            (joueur_selectionne == adv2 and partenaire_selectionne == adv1)):
                        continue  # Passer cette ligne si elle ne concerne pas cette paire
                else:
                    # Cas "Tous" : vérifier juste si le joueur a participé
                    if joueur_selectionne not in [vainq1, vainq2, adv1, adv2]:
                        continue
            
            # Mettre à jour les stats des vainqueurs
            for vainqueur in [vainq1, vainq2]:
                if vainqueur in stats:
                    stats[vainqueur]["Victoires"] += 1
                    stats[vainqueur]["Points_marques"] += score_v
                    stats[vainqueur]["Points_encaisses"] += score_p
                    if  score_p == 0:
                        stats[vainqueur]["Tôle_infligées"] += 1
            
            # Mettre à jour les stats des perdants
            for perdant in [adv1, adv2]:
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

# Fonction pour calculer les stats en doublette (championnat)
#############################################################

def calculer_stats_doublette_champ():
    stats_championnat = {j: {"Victoires": 0, "Défaites": 0, "Points_marques": 0, "Points_encaisses": 0, "Diff": 0, "Tôle_infligées": 0, "Tôle_encaissées": 0} for j in joueurs_championnat_doub}
    
    if not championnat_doub_df.empty:
        for _, row in championnat_doub_df.iterrows():
            vainqueur = row["vainqueur"]
            perdant = row["adversaire"]
            score_v = row.get("score_vainqueur", 13)
            score_p = row.get("score_adversaire", 0)
            
            # Mettre à jour les stats des vainqueurs
            if vainqueur in stats_championnat:
                stats_championnat[vainqueur]["Victoires"] += 1
                stats_championnat[vainqueur]["Points_marques"] += score_v
                stats_championnat[vainqueur]["Points_encaisses"] += score_p
                if  score_p == 0:
                    stats_championnat[vainqueur]["Tôle_infligées"] += 1
            
            # Mettre à jour les stats des perdants
            if perdant in stats_championnat:
                stats_championnat[perdant]["Défaites"] += 1
                stats_championnat[perdant]["Points_marques"] += score_p
                stats_championnat[perdant]["Points_encaisses"] += score_v
                if score_p == 0:
                    stats_championnat[perdant]["Tôle_encaissées"] += 1
    
    # Calculer la différence de points
    for j in stats_championnat:
        stats_championnat[j]["Diff"] = stats_championnat[j]["Points_marques"] - stats_championnat[j]["Points_encaisses"]
    
    return stats_championnat

# Tableau complet avec mise en surbrillance du joueur sélectionné
#################################################################

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
    st.write("")

    # --------------------------- # 
    # --- Onglet Participants --- #
    # --------------------------- #
    with tabs[0]:  # Onglet "Génération matchs mêlée"
        st.header("🎲 Concours en doublette à la mêlée")
        
        # Initialiser les historiques dans session_state
        if 'historique_partenaires_melee' not in st.session_state:
            st.session_state.historique_partenaires_melee = {}
        
        if 'historique_adversaires_melee' not in st.session_state:
            st.session_state.historique_adversaires_melee = {}
        
        # Sélection des joueurs disponibles
        st.subheader("👥 Joueurs disponibles pour ce tour")
        
        # Checkbox pour sélectionner les joueurs
        if 'joueurs_dispo_melee' not in st.session_state:
            st.session_state.joueurs_dispo_melee = liste_joueurs_complet.copy()
        
        col1, col2 = st.columns(2)
        mid = len(liste_joueurs_complet) // 2
        
        joueurs_selectionnes_tour = []
        
        with col1:
            for j in liste_joueurs_complet[:mid]:
                if st.checkbox(j, value=True, key=f"melee_{j}"):
                    joueurs_selectionnes_tour.append(j)
        
        with col2:
            for j in liste_joueurs_complet[mid:]:
                if st.checkbox(j, value=True, key=f"melee_{j}"):
                    joueurs_selectionnes_tour.append(j)
        
        st.divider()
        
        nb_joueurs = len(joueurs_selectionnes_tour)
        nb_matchs_possible = nb_joueurs // 4
        
        if nb_joueurs < 4:
            st.warning("⚠️ Il faut au moins 4 joueurs pour générer des matchs")
        elif nb_joueurs % 4 != 0:
            st.warning(f"⚠️ Le nombre de joueurs doit être un multiple de 4 (actuellement {nb_joueurs})")
            st.info(f"💡 Déselectionne {nb_joueurs % 4} joueur(s) ou ajoute {4 - (nb_joueurs % 4)} joueur(s)")
        else:
            st.success(f"✅ {nb_joueurs} joueurs sélectionnés → {nb_matchs_possible} match(s) possible(s)")
            
            # Slider pour choisir le nombre de matchs
            nb_matchs_generer = st.slider(
                "Nombre de matchs à générer",
                1,
                nb_matchs_possible,
                nb_matchs_possible,
                help="Tous les joueurs sélectionnés joueront si tu choisis le maximum"
            )
            
            st.divider()
            
            # Afficher les statistiques actuelles
            with st.expander("📊 Statistiques des appariements"):
                st.write("**Partenaires déjà formés :**")
                for j in joueurs_selectionnes_tour:
                    partenaires = st.session_state.historique_partenaires_melee.get(j, {})
                    if partenaires:
                        st.write(f"{j}: {', '.join([f'{p} ({n}x)' for p, n in partenaires.items()])}")
                
                st.divider()
                
                st.write("**Adversaires déjà affrontés :**")
                for j in joueurs_selectionnes_tour:
                    adversaires = st.session_state.historique_adversaires_melee.get(j, {})
                    if adversaires:
                        adversaires_tries = sorted(adversaires.items(), key=lambda x: x[1], reverse=True)[:5]
                        st.write(f"{j}: {', '.join([f'{p} ({n}x)' for p, n in adversaires_tries])}")
            
            st.divider()
            
            # Bouton pour générer
            if st.button("🎲 Générer les appariements", type="primary", use_container_width=True):
                matchs, erreur = generer_doublette_melee(
                    joueurs_selectionnes_tour,
                    st.session_state.historique_partenaires_melee,
                    st.session_state.historique_adversaires_melee,
                    nb_matchs_generer
                )
                
                if erreur and not matchs:
                    st.error(f"❌ {erreur}")
                else:
                    if erreur:
                        st.warning(f"⚠️ {erreur}")
                    
                    st.success(f"✅ {len(matchs)} match(s) généré(s) !")
                    
                    # Afficher les matchs
                    st.subheader("🎯 Matchs générés")
                    
                    for idx, match in enumerate(matchs, 1):
                        j1, j2, j3, j4 = match
                        
                        col_match1, col_match2 = st.columns(2)
                        
                        with col_match1:
                            st.info(f"**Match {idx}**")
                        
                        with col_match2:
                            st.write(f"🔵 **{j1}** & **{j2}**  vs  🔴 **{j3}** & **{j4}**")
                        
                        # Mettre à jour les historiques
                        mettre_a_jour_historiques(
                            match,
                            st.session_state.historique_partenaires_melee,
                            st.session_state.historique_adversaires_melee
                        )
                            
                        # Enregistrer dans le spreadsheet
                        st.session_state.sheet_tournoi_doub.append_row([j1, j2, j3, j4, "à jouer", "", ""])
                            
                        st.success(f"Match {idx} enregistré !")
                        #st.rerun()
                            
                    
    st.image("images/WIP1.jpg", use_container_width=True)
    st.write("")
    st.write("# La mise au point d'un algorythme de création des équipes à la mélée va prendre un peu de temps 😉")

####################
# Mode Championnat #
####################
elif mode == "🏅 Championnat":

    # Onglets de l'application
    tabs = st.tabs(["👥 Participants", "🎪 Championnat", "➕ Saisie résultat", "📊 Confrontations", "🏆 Classement"])
    st.write("")

    # --------------------------- # 
    # --- Onglet Participants --- #
    # --------------------------- #
    with tabs[0]:
        # Sélection des joueurs et des équipes
        st.header("👥 Constitution des équipes")

        # Initialiser la liste des équipes dans session_state
        if 'equipes_doublette' not in st.session_state:
            st.session_state.equipes_doublette = []
        if 'equipes_doublette_txt' not in st.session_state:
            st.session_state.equipes_doublette_txt = []

        if not championnat_doub_df.empty:
            st.info(f"✅ Le championnat est déjà lancé avec {len(joueurs_championnat_doub)} participants")
            st.write("**Participants :**")
            for j in sorted(joueurs_championnat_doub):
                st.write(f"• {j}")
            
            st.divider()

            st.warning("⚠️ Pour modifier les participants, il faut réinitialiser le championnat (Contacter Stef-la-pétanque)")

        else:
    
            # Afficher les équipes déjà enregistrées
            if st.session_state.equipes_doublette:
                st.subheader("Équipes enregistrées :")
                for idx, equipe in enumerate(st.session_state.equipes_doublette, 1):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.info(f"**Équipe {idx}** : {equipe[0]} et {equipe[1]}")
                    with col2:
                        if st.button("🗑️", key=f"delete_{idx}", help="Supprimer cette équipe"):
                            st.session_state.equipes_doublette.pop(idx - 1)
                            st.session_state.equipes_doublette_txt.pop(idx - 1)
                            st.rerun()
    
            st.divider()
    
            # Créer la liste des joueurs encore disponibles
            joueurs_deja_pris = []
            for equipe in st.session_state.equipes_doublette:
                joueurs_deja_pris.extend(equipe)
            
            joueurs_disponibles = [j for j in liste_joueurs_complet if j not in joueurs_deja_pris]
            
            # Formulaire pour ajouter une nouvelle équipe
            if len(joueurs_disponibles) >= 2:
                st.subheader("Ajouter une nouvelle équipe :")
                
                col1, col2 = st.columns(2)
                with col1:
                    joueur_1 = st.selectbox("Joueur 1", options=joueurs_disponibles, key="joueur_1_new")
                with col2:
                    joueur_2 = st.selectbox("Joueur 2", options=[j for j in joueurs_disponibles if j != joueur_1], key="joueur_2_new")
                
                st.caption(f"Équipe : **{joueur_1}** et **{joueur_2}**")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("➕ Ajouter cette équipe", use_container_width=True):
                        st.session_state.equipes_doublette_txt.append(joueur_1 + "/" + joueur_2)
                        st.session_state.equipes_doublette.append([joueur_1, joueur_2])
                        st.success(f"✅ Équipe ajoutée : {joueur_1} et {joueur_2}")
                        st.rerun()
                
                
    
                with col_btn2:
                    if len(st.session_state.equipes_doublette) >= 2:
                        if st.button("🏁 Valider et lancer le tournoi", use_container_width=True, type="primary"):
                            
                            equipes_doublette = st.session_state.equipes_doublette
                            equipes_doublette_txt = st.session_state.equipes_doublette_txt
                            
                            # Vérifier qu'il y a au moins 4 équipes
                            if len(equipes_doublette) < 4:
                                st.error("⚠️ Il faut au moins 4 équipes pour lancer le tournoi")
                            else:
                                nb_equipes_doublette = len(equipes_doublette_txt)
                                nb_parties_total = nb_equipes_doublette * (nb_equipes_doublette - 1) // 2
                                
                                st.success(f"🎉 Tournoi lancé avec {nb_equipes_doublette} équipes ({nb_parties_total} parties au total)")
                                
                                nouveaux_matchs = generer_doublette_aleatoires_champ(equipes_doublette_txt, seed=42)
                                st.success(f"✅ {(nouveaux_matchs)} matchs générés !")
                                for match in nouveaux_matchs:
                                    st.session_state.sheet_championnat_doub.append_rows(match)
                            
                                # Recharger les données du tournoi
                                st.session_state.championnat_doub_df = pd.DataFrame(tournoi_doub_rows)
                            
                                st.success(f"✅ {(nouveaux_matchs)} matchs générés !")
                                
                                st.rerun()
            else:
                st.warning("⚠️ Plus assez de joueurs disponibles pour créer une nouvelle équipe")
            
            st.divider()
            
            # Statistiques
            if st.session_state.equipes_doublette:
                nb_equipes_doublette = len(st.session_state.equipes_doublette)
                nb_joueurs_utilises = len(joueurs_deja_pris)
                nb_parties_total = nb_equipes_doublette * (nb_equipes_doublette - 1) // 2
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Équipes", nb_equipes_doublette)
                with col2:
                    st.metric("Joueurs utilisés", nb_joueurs_utilises)
                with col3:
                    st.metric("Parties totales", nb_parties_total)
                
                # Bouton de réinitialisation
                if st.button("🔄 Réinitialiser toutes les équipes", type="secondary"):
                    st.session_state.equipes_doublette = []
                    st.rerun()

    # -------------------------- # 
    # --- Onglet championnat --- #
    # -------------------------- # 
    with tabs[1]:
        st.header("🎪 Gestion du championnat")
        
        if championnat_doub_df.empty:
            st.warning("⚠️ Voir dans l'onglet **👥 Participants** pour lancer le championnat")
        
        else:
            # Calculs nécéssaires
            nb_total = len(joueurs_championnat_doub) * (len(joueurs_championnat_doub) - 1) // 2
            nb_parties_tour = round(len(liste_joueurs_doub) // 2)
            nb_joues = len(championnat_doub_df[championnat_doub_df["statut"] == "terminé"]) if not championnat_doub_df.empty else 0
            nb_en_cours = len(championnat_doub_df[championnat_doub_df["statut"] == "à jouer"]) if not championnat_doub_df.empty else 0
            
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
            parties_en_cours = championnat_doub_df[championnat_doub_df["statut"] == "à jouer"]
            
            if not parties_en_cours.empty:
                st.subheader("⚡ Parties à jouer")
                st.write("")
                st.write("")
                for tour_num, groupe in parties_en_cours.groupby("tour n°"):
                    st.markdown(f"### 🏁 {str(tour_num)}")
                    for _, parties in groupe.iterrows():
                        st.info(f"🎯 **{parties['equipe_1']}** vs **{parties['equipe_2']}**")
            
            st.divider()

            # - Afficher la liste des parties terminés - #
            parties_termines = championnat_doub_df[championnat_doub_df["statut"] == "terminé"]

            if not parties_termines.empty:
                st.subheader("✅ Parties terminés")
                for tour_num, groupe in parties_termines.groupby("tour n°"):
                    st.markdown(f"### 🏁 {str(tour_num)}")
                    for _, parties in groupe.iterrows():
                        st.info(f"🎯 **{parties['equipe_1']}** vs **{parties['equipe_2']}**")

            st.divider()
            
            # Historique complet
            with st.expander("📋 Voir tous les matchs du championnat"):
                st.dataframe(tournoi_doub_df, use_container_width=True)

    # --------------------- #
    # --- Onglet Saisie --- #
    # --------------------- #
    with tabs[2]:
        st.header("Saisie d'un résultat de championnat")
        
        # Récupérer les matchs à jouer
        matchs_disponibles = []
        if not championnat_doub_df.empty:
            matchs_a_jouer = championnat_doub_df[championnat_doub_df["statut"] == "à jouer"]
            for _, match in matchs_a_jouer.iterrows():
                matchs_disponibles.append(f"{match['equipe_1']} vs {match['equipe_2']}")
        
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
                    all_data = st.session_state.sheet_championnat_doub.get_all_values()
                    row_idx = None
                    
                    for i, row in enumerate(all_data[1:], start=2):  # Skip header, start at row 2
                        if (row[0] == j1 and row[1] == j2) or (row[0] == j2 and row[1] == j1):
                            if row[3] == "à jouer":  # Vérifier que c'est bien un match à jouer
                                row_idx = i
                                break
                    
                    if row_idx:
                        # Mettre à jour le championnat
                        st.session_state.sheet_championnat_doub.update(f"D{row_idx}:I{row_idx}", [["terminé", vainqueur, perdant, score_vainqueur, score_perdant, date]])
                        
                        # Recharger les données du championnat
                        championnat_doub_rows = st.session_state.sheet_championnat_doub.get_all_records()
                        st.session_state.championnat_doub_df = pd.DataFrame(tournoi_doub_rows)
                        
                        st.success("✅ Résultat enregistré !")
                        st.rerun()
                    else:
                        st.error("❌ Erreur : impossible de trouver le match")

    # ----------------------------- #
    # --- Onglet Confrontations --- #
    # ----------------------------- #
    with tabs[3]:
        st.header("Tableau des confrontations")
        
        if championnat_doub_df.empty:
            st.info("Aucun résultat enregistré pour le moment")
        else:
            recap = pd.DataFrame("", index=liste_joueurs_doub, columns=liste_joueurs_doub)
            
            for _, row in championnat_doub_df.iterrows():
                vainq = row["vainqueur"]
                adv = row["adversaire"]
                score_v = row.get("score_vainqueur", 13)
                score_a = row.get("score_adversaire", row.get("score_adv", 0))
                
                if vainq in liste_joueurs_doub and adv in liste_joueurs_doub:
                    recap.loc[vainq, adv] = f"{score_v}-{score_a}"
                    recap.loc[adv, vainq] = f"{score_a}-{score_v}"
            
            st.dataframe(recap, use_container_width=True)

    # ------------------------- #
    # --- Onglet Classement --- #
    # ------------------------- #
    with tabs[4]:
        st.header("Classement du championnat")
        
        stats_championnat = calculer_stats_doublette_champ()
        
        if all(s["Victoires"] == 0 and s["Défaites"] == 0 for s in stats_championnat.values()):
            st.info("Aucune partie terminée pour le moment")
        else:
            classement = pd.DataFrame(stats_championnat).T
            classement["Parties jouées"] = classement["Victoires"] + classement["Défaites"]
            classement["%_Victoires"] = ((classement["Victoires"] / classement["Parties jouées"]) * 100).fillna(0).replace([float('inf'), -float('inf')], 0).round(0).astype(int).astype(str) + "%"
            
            classement = classement.sort_values(by=["Victoires", "Diff"], ascending=[False, False])
            
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
        
        # Sélection des joueurs et des équipes
        # Equipe A
        st.text("Sélection des joueurs constituant la 1ère équipe")
        joueur_A1 = st.selectbox("Joueur A1", options=liste_joueurs_complet, key="joueur_A1")
        joueur_A2 = st.selectbox("Joueur A2", options=[j for j in liste_joueurs_complet if j != joueur_A1], key="joueur_A2")
        equipe_A = joueur_A1 + "/" + joueur_A2

        # Equipe B
        st.text("Sélection des joueurs constituant la 2ème équipe")
        joueur_B1 = st.selectbox("Joueur B1", options=[j for j in liste_joueurs_complet if j not in (joueur_A1, joueur_A2)], key="joueur_B1")
        joueur_B2 = st.selectbox("Joueur B2", options=[j for j in liste_joueurs_complet if j not in (joueur_A1, joueur_A2, joueur_B1)], key="joueur_B2")
        equipe_B = joueur_B1 + "/" + joueur_B2

        with st.form("saisie_resultat_open"):
            # Vainqueur dépend des joueurs choisis
            
            vainqueur = st.radio("Qui a gagné ?", [equipe_A, equipe_B])
            score_perdant = st.number_input("Score de l'équipe perdante", min_value=0, max_value=12, value=0)
            date = pd.to_datetime('now').strftime("%Y-%m-%d %H:%M:%S")
                    
            st.caption(f"Résultat : **{vainqueur}** 13 - {score_perdant} **{equipe_B if vainqueur == equipe_A else equipe_A}**")
                    
            submitted = st.form_submit_button("✅ Enregistrer", use_container_width=True)

        if submitted:
            # Ajouter aussi dans les résultats généraux
            if vainqueur == equipe_A:
                vainqueur1 = joueur_A1
                vainqueur2 = joueur_A2
                adversaire1 = joueur_B1
                adversaire2 = joueur_B2
            else:
                vainqueur1 = joueur_B1
                vainqueur2 = joueur_B2
                adversaire1 = joueur_A1
                adversaire2 = joueur_A2

            st.session_state.sheet_resultats_doub.append_row([vainqueur1, vainqueur2, adversaire1, adversaire2, 13, score_perdant, date])
            st.success("✅ Résultat enregistré !")
            st.rerun()

    with tabs[1]:
        # Statistiques globales tous joueurs
        st.header("Choisissez un joueur pour afficher ses stats et le mettre en surbrillance dans le tableau")

        # Sélection d'un joueur à afficher
        joueur = st.selectbox("Choix du joueur", options=liste_joueurs_complet, key="joueur")

        # Créer la liste des partenaires potentiels
        partenaires_possibles = ["Tous"] + [j for j in liste_joueurs_complet if j != joueur]
        partenaire = st.selectbox("Partenaire", options=partenaires_possibles, key="partenaire_doublette")

        # Calculer les stats filtrées
        stats = calculer_stats_doublette(joueur, partenaire)

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

        # Message explicatif
        if partenaire == "Tous":
            st.info(f"📊 Statistiques de **{joueur}** avec tous ses partenaires")
        else:
            st.info(f"📊 Statistiques de **{joueur}** en doublette avec **{partenaire}**")

        # Affichage du tableau complet
        stats_tab_styled = stats_tab.style.apply(highlight_joueur, axis=1)
        st.dataframe(stats_tab_styled, use_container_width=True)
