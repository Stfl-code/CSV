import streamlit as st
import gspread
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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

        moyens_ateliers = [
            np.mean([st.session_state.resultats[f"Atelier {i}"][d] for d in distances])
            for i in range(1, 6)
        ]

        angles = np.linspace(0, 2 * np.pi, 5, endpoint=False)
        moyens_ateliers = np.concatenate((moyens_ateliers, [moyens_ateliers[0]]))
        angles = np.concatenate((angles, [angles[0]]))

        fig = plt.figure(figsize=(6,6))
        ax = plt.subplot(111, polar=True)
        ax.plot(angles, moyens_ateliers)
        ax.fill(angles, moyens_ateliers, alpha=0.3)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels([f"Atelier {i}" for i in range(1, 6)])
        st.pyplot(fig)

        # ==========================================
        # GRAPHIQUE RADAR : MOYENNE par DISTANCE
        # ==========================================
        st.subheader("📈 Radar – Moyenne par distance")

        moyens_distances = [
            np.mean([st.session_state.resultats[f"Atelier {i}"][d] for i in range(1, 6)])
            for d in distances
        ]

        angles2 = np.linspace(0, 2 * np.pi, 4, endpoint=False)
        moyens_distances = np.concatenate((moyens_distances, [moyens_distances[0]]))
        angles2 = np.concatenate((angles2, [angles2[0]]))

        fig2 = plt.figure(figsize=(6,6))
        ax2 = plt.subplot(111, polar=True)
        ax2.plot(angles2, moyens_distances)
        ax2.fill(angles2, moyens_distances, alpha=0.3)
        ax2.set_xticks(angles2[:-1])
        ax2.set_xticklabels(distances)
        st.pyplot(fig2)


    # Bouton pour recommencer
    if st.button("🔄 Faire un nouveau joueur"):
        st.session_state.clear()
        st.rerun()


    # Bouton pour enregistrer
    if st.button("✔ Enregistrer"):
        st.session_state.clear()
        st.rerun()