import streamlit as st
import pandas as pd
from github import Github
import base64
import os

# -------------------------
# Paramètres
# -------------------------
GITHUB_REPO = st.secrets.get("GITHUB_REPO", "Stfl-code/CSV")
RESULTS_PATH = "resultats.csv"
PLAYERS_PATH = "joueurs.csv"

# Authentification GitHub
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
g = Github(GITHUB_TOKEN)
repo = g.get_repo(GITHUB_REPO)

# -------------------------
# Charger les fichiers depuis GitHub
# -------------------------
def load_csv_from_github(path):
    try:
        contents = repo.get_contents(path)
        df = pd.read_csv(pd.compat.StringIO(contents.decoded_content.decode()))
        return df, contents
    except Exception:
        return pd.DataFrame(), None

# Charger joueurs et résultats
df, results_file = load_csv_from_github(RESULTS_PATH)
if df.empty:
    df = pd.DataFrame(columns=["joueur_A", "joueur_B", "score_A", "score_B", "vainqueur"])

players_df, _ = load_csv_from_github(PLAYERS_PATH)
if not players_df.empty:
    joueurs_list = players_df["Nom"].tolist()
else:
    joueurs_list = ["Jean", "Paul", "Marie", "Lucas"]

# -------------------------
# Sauvegarde sur GitHub
# -------------------------
def save_to_github(df, path, file_ref):
    csv_bytes = df.to_csv(index=False).encode()
    message = "Mise à jour résultats via Streamlit"
    if file_ref:
        repo.update_file(file_ref.path, message, csv_bytes.decode(), file_ref.sha)
    else:
        repo.create_file(path, message, csv_bytes.decode())

# -------------------------
# Onglets Streamlit
# -------------------------
tabs = st.tabs(["➕ Saisie des résultats", "📊 Statistiques"])

# -------------------------
# Onglet 1 : Saisie des résultats
# -------------------------
with tabs[0]:
    st.header("Saisie d'un nouveau résultat")

    col1, col2 = st.columns(2)
    with col1:
        new_joueur_A = st.selectbox("Joueur A", options=joueurs_list, index=0)
    with col2:
        new_joueur_B = st.selectbox("Joueur B", options=joueurs_list, index=1)

    score_A = st.number_input("Score A", min_value=0, max_value=13, value=0)
    score_B = st.number_input("Score B", min_value=0, max_value=13, value=0)

    if st.button("Vérifier le résultat"):
        if new_joueur_A == new_joueur_B:
            st.error("Un joueur ne peut pas jouer contre lui-même.")
        else:
            # Vérification si la paire existe déjà
            deja_joue = not df[((df["joueur_A"] == new_joueur_A) & (df["joueur_B"] == new_joueur_B)) |
                                ((df["joueur_A"] == new_joueur_B) & (df["joueur_B"] == new_joueur_A))].empty
            if deja_joue:
                st.error("Un résultat existe déjà pour cette paire de joueurs.")
            else:
                vainqueur = new_joueur_A if score_A > score_B else new_joueur_B
                st.info(f"⚖️ Résumé : {new_joueur_A} {score_A} - {score_B} {new_joueur_B} → Vainqueur : {vainqueur}")

                confirm_col1, confirm_col2 = st.columns(2)
                with confirm_col1:
                    if st.button("✅ Confirmer"):
                        new_data = pd.DataFrame([[new_joueur_A, new_joueur_B, score_A, score_B, vainqueur]],
                                                columns=df.columns)
                        df = pd.concat([df, new_data], ignore_index=True)
                        save_to_github(df, RESULTS_PATH, results_file)
                        st.success("Résultat enregistré et envoyé sur GitHub !")
                with confirm_col2:
                    st.button("❌ Annuler")

# -------------------------
# Onglet 2 : Statistiques
# -------------------------
with tabs[1]:
    st.header("Classement et statistiques")

    if df.empty:
        st.info("Aucun résultat enregistré pour l'instant.")
    else:
        joueurs = set(df["joueur_A"]).union(set(df["joueur_B"]))
        stats = []
        for j in joueurs:
            jouees = len(df[(df["joueur_A"] == j) | (df["joueur_B"] == j)])
            gagnees = len(df[df["vainqueur"] == j])
            perdues = jouees - gagnees
            points_marques = df.loc[df["joueur_A"] == j, "score_A"].sum() + df.loc[df["joueur_B"] == j, "score_B"].sum()
            points_encaisses = df.loc[df["joueur_A"] == j, "score_B"].sum() + df.loc[df["joueur_B"] == j, "score_A"].sum()
            goal_average = points_marques - points_encaisses
            stats.append([j, jouees, gagnees, perdues, round(gagnees/jouees*100,1) if jouees>0 else 0, points_marques, points_encaisses, goal_average])

        stats_df = pd.DataFrame(stats, columns=["Joueur", "Parties jouées", "Victoires", "Défaites", "% Victoires", "Points marqués", "Points encaissés", "Goal Average"])
        stats_df = stats_df.sort_values(by=["Victoires", "Goal Average"], ascending=[False, False])

        st.dataframe(stats_df, use_container_width=True)
        st.bar_chart(stats_df.set_index("Joueur")["Victoires"])
