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
st.set_page_config(page_title="Triplette", page_icon="👤👤👤")

st.write("# Parties en triplette du club de pétanque de Vaux-sur-Seine")

#######################
# Liens et chargement #
#######################
# Utiliser les données en cache
init_google_sheets()
liste_joueurs_complet = st.session_state.liste_joueurs_complet

# Charger les matchs du tournoi
tournoi_trip_rows = st.session_state.sheet_tournoi_trip.get_all_records()
tournoi_trip = pd.DataFrame(tournoi_trip_rows)

# Charger les matchs du championnat
championnat_trip_rows = st.session_state.sheet_championnat_trip.get_all_records()
championnat_trip = pd.DataFrame(championnat_trip_rows)

# Charger les résultats existants (on recharge à chaque fois car ils changent)
resultats_trip_rows = st.session_state.sheet_resultats_trip.get_all_records()
resultats_trip_df = pd.DataFrame(resultats_trip_rows)

# Récupérer les joueurs participant au tournoi
joueurs_tournoi_trip = []
if not tournoi_trip.empty:
    j1_list = tournoi_trip["joueur_1"].unique().tolist()
    j2_list = tournoi_trip["joueur_2"].unique().tolist()
    joueurs_tournoi_trip = list(set(j1_list + j2_list))
    liste_joueurs_trip = joueurs_tournoi_doub
else:
    liste_joueurs_trip = liste_joueurs_complet

# Récupérer les joueurs participant au championnat
joueurs_championnat_trip = []
if not championnat_trip.empty:
    j1_list = championnat_trip["joueur_1"].unique().tolist()
    j2_list = championnat_trip["joueur_2"].unique().tolist()
    joueurs_championnat_trip = list(set(j1_list + j2_list))
    liste_joueurs_trip = joueurs_championnat_trip
else:
    liste_joueurs_trip = liste_joueurs_complet

#############
# Fonctions #
#############
# Fonction pour calculer les stats en triplette
def calculer_stats_triplette(joueur_selectionne=None, partenaire1_selectionne=None, partenaire2_selectionne=None):
    stats = {j: {"Victoires": 0, "Défaites": 0, "Points_marques": 0, "Points_encaisses": 0, "Diff": 0, "Tôle_infligées": 0, "Tôle_encaissées": 0} for j in liste_joueurs_complet}
    
    if not resultats_trip_df.empty:
        for _, row in resultats_trip_df.iterrows():
            vainq1 = row["vainqueur1"]
            vainq2 = row["vainqueur2"]
            vainq3 = row["vainqueur3"]
            adv1 = row["adversaire1"]
            adv2 = row["adversaire2"]
            adv3 = row["adversaire3"]
            score_v = row.get("score_vainqueur", 13)
            score_p = row.get("score_adversaire", 0)
            
            # Équipes gagnante et perdante
            equipe_gagnante = [vainq1, vainq2, vainq3]
            equipe_perdante = [adv1, adv2, adv3]
            
            # Filtrer selon le joueur et partenaires sélectionnés
            if joueur_selectionne:
                if partenaire1_selectionne == "Tous" and partenaire2_selectionne == "Tous":
                    # Cas "Tous" : vérifier juste si le joueur a participé
                    if joueur_selectionne not in equipe_gagnante + equipe_perdante:
                        continue
                elif partenaire1_selectionne != "Tous" and partenaire2_selectionne != "Tous":
                    # Cas spécifique : trio complet
                    trio = sorted([joueur_selectionne, partenaire1_selectionne, partenaire2_selectionne])
                    trio_gagnant = sorted(equipe_gagnante)
                    trio_perdant = sorted(equipe_perdante)
                    
                    if trio != trio_gagnant and trio != trio_perdant:
                        continue
                else:
                    # Un partenaire spécifié, l'autre "Tous"
                    partenaire_specifie = partenaire1_selectionne if partenaire1_selectionne != "Tous" else partenaire2_selectionne
                    
                    # Vérifier si le joueur et le partenaire spécifié sont dans la même équipe
                    joueur_et_partenaire_gagnants = joueur_selectionne in equipe_gagnante and partenaire_specifie in equipe_gagnante
                    joueur_et_partenaire_perdants = joueur_selectionne in equipe_perdante and partenaire_specifie in equipe_perdante
                    
                    if not (joueur_et_partenaire_gagnants or joueur_et_partenaire_perdants):
                        continue
            
            # Mettre à jour les stats des vainqueurs
            for vainqueur in [vainq1, vainq2, vainq3]:
                if vainqueur in stats:
                    stats[vainqueur]["Victoires"] += 1
                    stats[vainqueur]["Points_marques"] += score_v
                    stats[vainqueur]["Points_encaisses"] += score_p
                    if  score_p == 0:
                        stats[vainqueur]["Tôle_infligées"] += 1
            
            # Mettre à jour les stats des perdants
            for perdant in [adv1, adv2, adv3]:
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
    st.write("")
    st.image("images/WIP1.jpg", use_container_width=True)
    st.write("")
    st.write("# Je finis la section doublette et ensuite je m'en occupe 😉")

####################
# Mode championnat #
####################
if mode == "🏆 Championnat":

    # Onglets de l'application
    tabs = st.tabs(["👥 Participants", "🎪 Championnat", "➕ Saisie résultat", "📊 Confrontations", "🏆 Classement"])
    st.write("")
    st.image("images/WIP2.jpg", use_container_width=True)
    st.write("")
    st.write("# Je finis la section doublette et ensuite je m'en occupe 😉")

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
        joueur_A3 = st.selectbox("Joueur A3", options=[j for j in liste_joueurs_complet if j not in (joueur_A1, joueur_A2)], key="joueur_A3")
        equipe_A = joueur_A1 + "/" + joueur_A2 + "/" + joueur_A3

        # Equipe B
        st.text("Sélection des joueurs constituant la 2ème équipe")
        joueur_B1 = st.selectbox("Joueur B1", options=[j for j in liste_joueurs_complet if j not in (joueur_A1, joueur_A2, joueur_A3)], key="joueur_B1")
        joueur_B2 = st.selectbox("Joueur B2", options=[j for j in liste_joueurs_complet if j not in (joueur_A1, joueur_A2, joueur_A3, joueur_B1)], key="joueur_B2")
        joueur_B3 = st.selectbox("Joueur B3", options=[j for j in liste_joueurs_complet if j not in (joueur_A1, joueur_A2, joueur_A3, joueur_B1, joueur_B2)], key="joueur_B3")
        equipe_B = joueur_B1 + "/" + joueur_B2 + "/" + joueur_B3

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
                vainqueur3 = joueur_A3
                adversaire1 = joueur_B1
                adversaire2 = joueur_B2
                adversaire3 = joueur_B3
            else:
                vainqueur1 = joueur_B1
                vainqueur2 = joueur_B2
                vainqueur3 = joueur_B3
                adversaire1 = joueur_A1
                adversaire2 = joueur_A2
                adversaire3 = joueur_A3
            resultats_trip.append_row([vainqueur1, vainqueur2, vainqueur3, adversaire1, adversaire2, adversaire3, 13, score_perdant, date])
            st.success("✅ Résultat enregistré !")
            st.rerun()

    with tabs[1]:
        # Statistiques globales tous joueurs
        st.header("Choisissez un joueur pour afficher ses stats et le mettre en surbrillance dans le tableau")

        # Sélection d'un joueur à afficher
        joueur = st.selectbox("Choix du joueur", options=liste_joueurs_complet, key="joueur_triplette")

        # Créer la liste des partenaires potentiels
        partenaires_possibles = ["Tous"] + [j for j in liste_joueurs_complet if j != joueur]

        col1, col2 = st.columns(2)
        with col1:
            partenaire1 = st.selectbox("Partenaire 1", options=partenaires_possibles, key="partenaire1_triplette")
    
        with col2:
            # Partenaire 2 exclut le joueur ET le partenaire 1 (sauf si partenaire1 == "Tous")
            if partenaire1 == "Tous":
                partenaires_possibles2 = partenaires_possibles
            else:
                partenaires_possibles2 = ["Tous"] + [j for j in liste_joueurs_complet if j != joueur and j != partenaire1]
        
            partenaire2 = st.selectbox("Partenaire 2", options=partenaires_possibles2, key="partenaire2_triplette")

        # Calculer les stats filtrées
        stats = calculer_stats_triplette(joueur, partenaire1, partenaire2)

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
        if partenaire1 == "Tous" and partenaire2 == "Tous":
            st.info(f"📊 Statistiques de **{joueur}** en triplette avec n'importe quels partenaires")
        elif partenaire1 != "Tous" and partenaire2 != "Tous":
            st.info(f"📊 Statistiques de **{joueur}** en triplette avec **{partenaire1}** et **{partenaire2}**")
        else:
            partenaire_specifie = partenaire1 if partenaire1 != "Tous" else partenaire2
            st.info(f"📊 Statistiques de **{joueur}** en équipe avec **{partenaire_specifie}** (tous 3èmes partenaires confondus)")

        # Affichage du tableau complet
        stats_tab_styled = stats_tab.style.apply(highlight_joueur, axis=1)
        st.dataframe(stats_tab_styled, use_container_width=True)