import streamlit as st
import gspread
import pandas as pd
import random

#############
# Affichage #
#############
st.set_page_config(page_title="Doublette", page_icon="👥")

st.write("# Parties en doublette du club de pétanque de Vaux-sur-Seine")

#######################
# Liens et chargement #
#######################
# Initialiser la connexion Google Sheets uniquement si nécessaire
if 'sheets_loaded' not in st.session_state:
    gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    sh = gc.open_by_key(st.secrets["sheet"]["id"])
    
    # Onglets Google Sheets
    resultats_doub = sh.worksheet("resultats_doub")
    joueurs_sheet = sh.worksheet("joueurs")
    tournoi_doub = sh.worksheet("tournoi_doub")
    
    # Charger les joueurs
    prenoms = joueurs_sheet.col_values(1)[1:]
    noms = joueurs_sheet.col_values(2)[1:]
    st.session_state.liste_joueurs_complet = [f"{p} {n}" for p, n in zip(prenoms, noms)]
    
    # Charger les matchs du tournoi
    tournoi_rows_doub = tournoi_doub.get_all_records()
    st.session_state.df_tournoi_doub = pd.DataFrame(tournoi_rows_doub)
    
    # Sauvegarder les worksheets
    st.session_state.resultats_doub = resultats_doub
    st.session_state.tournoi_doub = tournoi_doub
    st.session_state.sheets_loaded = True
else:
    resultats_doub = st.session_state.resultats_doub
    tournoi_doub = st.session_state.tournoi_doub

# Utiliser les données en cache
liste_joueurs_complet = st.session_state.liste_joueurs_complet
df_tournoi_doub = st.session_state.df_tournoi_doub

# Charger les résultats existants (on recharge à chaque fois car ils changent)
rows_doub = resultats_doub.get_all_records()
df_doublette = pd.DataFrame(rows_doub)

# Récupérer les joueurs participant au tournoi
joueurs_tournoi_doub = []
if not df_tournoi_doub.empty:
    j1_list = df_tournoi_doub["joueur_1"].unique().tolist()
    j2_list = df_tournoi_doub["joueur_2"].unique().tolist()
    joueurs_tournoi_doub = list(set(j1_list + j2_list))
    liste_joueurs_doub = joueurs_tournoi_doub
else:
    liste_joueurs_doub = liste_joueurs_complet

#############
# Fonctions #
#############
# Fonction pour calculer les stats en doublette
def calculer_stats_doublette(joueur_selectionne=None, partenaire_selectionne=None):
    stats = {j: {"Victoires": 0, "Défaites": 0, "Points_marques": 0, "Points_encaisses": 0, "Diff": 0, "Tôle_infligées": 0, "Tôle_encaissées": 0} for j in liste_joueurs_complet}
    
    if not df_doublette.empty:  # df_doublette = résultats de la feuille doublette
        for _, row in df_doublette.iterrows():
            vainq1 = row["vainqueur1"]
            vainq2 = row["vainqueur2"]
            adv1 = row["adversaire1"]
            adv2 = row["adversaire2"]
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
    st.write("")
    st.image("images/WIP1.jpg", use_container_width=True)
    st.write("")
    st.write("# Je finis la section tête à tête et ensuite je m'en occupe 😉")

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

            resultats_doub.append_row([vainqueur1, vainqueur2, adversaire1, adversaire2, 13, score_perdant, date])
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
