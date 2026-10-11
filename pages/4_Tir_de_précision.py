import streamlit as st
import gspread
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import sys
sys.path.append('..')  # Pour importer depuis la racine
from utils import init_google_sheets

#############
# Affichage #
#############
st.set_page_config(page_title="Tir de précision", page_icon="👤")
st.image("images/Tir.jpg", use_container_width=True)
st.write("# Tir de précision du club de pétanque de Vaux-sur-Seine")

#######################
# Liens et chargement #
#######################
# Utiliser les données en cache
init_google_sheets()
liste_joueurs_complet = st.session_state.liste_joueurs_complet

# Charger les matchs du tournoi tête-à-tête
tir_precision_rows = st.session_state.sheet_tir_precision.get_all_records()
tir_precision_df = pd.DataFrame(tir_precision_rows)

#############
# Fonctions #
#############
def suivant():
    st.session_state.etape += 1
    st.rerun()

def retour():
    if st.session_state.etape > 1:
        st.session_state.etape -= 1
        st.rerun()

def afficher_atelier(num, nom):
    st.header(f"Atelier {num} : {nom}")

    resultats = {}
    for d in distances:
        resultats[d] = st.selectbox(
            f"Score à {d}",
            scores_possible,
            key=f"{nom}-{d}"
        )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("⬅️ Retour"):
            retour()

    with col2:
        if st.button("➡️ Suivant"):
            st.session_state.resultats[f"Atelier {num}"] = resultats
            suivant()

########################
# Choix du mode de jeu #
########################
st.divider()
mode = st.radio(
    "Mode de jeu",
    ["🎲 Jeu libre", "🏆 Tournoi"],
    horizontal=True
)
st.divider()

################
# Mode tournoi #
################
if mode == "🏆 Tournoi":

    st.image("images/WIP2.jpg", use_container_width=True)

##################
# Mode jeu libre #
##################
else: 

    if "etape" not in st.session_state:
        st.session_state.etape = 1

    if "resultats" not in st.session_state:
        st.session_state.resultats = {
            "Atelier 1": {},
            "Atelier 2": {},
            "Atelier 3": {},
            "Atelier 4": {},
            "Atelier 5": {}
        }

    # Liste des distances et des scores possibles
    distances = ["6m", "7m", "8m", "9m"]
    scores_possible = [0, 1, 3, 5]
    ateliers = ["Boule seule", "Boule derrière bouchon", "Entre deux boules", "Tir à la sautée", "Tir au bouchon"]

    # Sélection du joueur
    joueur = st.selectbox("Choix du joueur", options=liste_joueurs_complet, key="joueur")

    # Onglets de l'application
    #tabs = st.tabs(["Ateliers", "Récapitulatif"])

    # ==========================================
    #  ÉTAPES
    # ==========================================
    if st.session_state.etape <= 5:
        afficher_atelier(st.session_state.etape, ateliers[st.session_state.etape - 1])

    # ==========================================
    # RÉCAPITULATIF FINAL + GOOGLE SHEET + RADAR
    # ==========================================
    elif st.session_state.etape == 6:

        st.header("📊 Récapitulatif complet")

        # -------- Calcul Score Final -------- #
        total_score = sum(
            st.session_state.resultats[f"Atelier {i}"][d]
            for i in range(1, 6)
            for d in distances
        )

        score_sur_100 = total_score  # déjà sur 100

        st.subheader(f"🔥 Score final : **{score_sur_100} / 100**")

        st.write("---")
        st.write("Détails des ateliers :")
        st.write(st.session_state.resultats)

        # ==========================================
        # GRAPHIQUE RADAR : MOYENNE par ATELIER
        # ==========================================
        st.subheader("📈 Radar – Moyenne par atelier")

        # Calculer les moyennes par atelier
        moyens_ateliers = [
            np.mean([st.session_state.resultats[f"Atelier {i}"][d] for d in distances])
            for i in range(1, 6)
        ]

        # Catégories (ateliers)
        categories = [f"Atelier {i}" for i in range(1, 6)]

        # Créer le graphique radar avec Plotly
        fig = go.Figure()

        fig.add_trace(go.Scatterpolar(
            r=moyens_ateliers,
            theta=categories,
            fill='toself',
            name='Moyenne',
            line=dict(color='#1f77b4', width=0),
            fillcolor='rgba(31, 119, 180, 0.3)'
        ))

        # Configuration pour pentagone et échelle fixe 0-5
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 5],  
                    tickmode='linear',
                    tick0=0,
                    dtick=1,  # Graduations tous les 1
                    showline=True,
                    gridcolor='lightgray',
                    linewidth=1
                ),
                angularaxis=dict(
                    gridcolor='lightgray',
                    linecolor='gray',
                    linewidth=1, 
                    rotation=90
                ),
                gridshape='linear'
            ),
            showlegend=False,
            height=500,
            margin=dict(l=80, r=80, t=50, b=50)
        )

        st.plotly_chart(fig, use_container_width=True)

        # ==========================================
        # GRAPHIQUE RADAR : MOYENNE par DISTANCE
        # ==========================================
        st.subheader("📈 Radar – Moyenne par distance")


        moyens_distances = [
            np.mean(st.session_state.resultats[f"{d}"])
            for d in distances
        ]

        # Catégories (distances)
        categories = [f"{d}" for d in distances]

        # Créer le graphique radar avec Plotly
        fig2 = go.Figure()

        fig2.add_trace(go.Scatterpolar(
            r=moyens_distances,
            theta=categories,
            fill='toself',
            name='Moyenne',
            line=dict(color='#1f77b4', width=0),
            fillcolor='rgba(31, 119, 180, 0.3)'
        ))

        fig2.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 5],
                    tickmode='linear',
                    tick0=0,
                    dtick=1,
                    showline=True,
                    gridcolor='lightgray',
                    linewidth=1
                ),
                angularaxis=dict(
                    gridcolor='lightgray',
                    linecolor='gray',
                    linewidth=1
                ),
                gridshape='linear'
            ),
            showlegend=False,
            height=500, 
            margin=dict(l=80, r=80, t=50, b=50)
        ) 

        st.plotly_chart(fig2, use_container_width=True)


    # Bouton pour recommencer
    if st.button("🔄 Faire un nouveau joueur"):
        st.session_state.clear()
        st.rerun()


    # Bouton pour enregistrer
    if st.button("✔ Enregistrer"):
        st.session_state.clear()
        st.rerun()