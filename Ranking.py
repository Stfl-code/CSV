import streamlit as st
import gspread
import pandas as pd

# Connexion à Google Sheets
gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
sh = gc.open_by_key(st.secrets["sheet"]["id"])

# Onglet "Résultats"
worksheet = sh.sheet1

# Onglet "Joueurs"
try:
    joueurs_ws = sh.worksheet("Joueurs")  # crée un onglet "Joueurs" avec une liste simple en colonne A
    joueurs = joueurs_ws.col_values(1)[1:]  # saute l’entête si tu en as un
except:
    joueurs = []

# Charger les résultats existants
rows = worksheet.get_all_records()
df = pd.DataFrame(rows)

# Onglets
tabs = st.tabs(["➕ Saisie des résultats", "📊 Statistiques"])

# --- Onglet 1 : Saisie ---
with tabs[0]:
    st.header("Saisie d'un nouveau résultat")

    with st.form("saisie_resultat"):
        joueur_A = st.selectbox("Joueur A", options=joueurs)
        joueur_B = st.selectbox("Joueur B", options=[j for j in joueurs if j != joueur_A])
        score_A = st.number_input("Score A", min_value=0, max_value=13, value=0)
        score_B = st.number_input("Score B", min_value=0, max_value=13, value=0)
        submitted = st.form_submit_button("Enregistrer")

        if submitted:
            # Vérifications de validité
            if (score_A == 13 and score_B < 13) or (score_B == 13 and score_A < 13):
                # Vérifier qu'il n’existe pas déjà un résultat entre ces deux joueurs
                existe_deja = False
                if not df.empty:
                    existe_deja = (
                        ((df["joueur_A"] == joueur_A) & (df["joueur_B"] == joueur_B)).any()
                        or ((df["joueur_A"] == joueur_B) & (df["joueur_B"] == joueur_A)).any()
                    )
                if existe_deja:
                    st.error("⚠️ Un résultat existe déjà pour cette paire de joueurs.")
                else:
                    worksheet.append_row([joueur_A, joueur_B, score_A, score_B])
                    st.success("✅ Résultat enregistré avec succès")
            else:
                st.error("⚠️ Score invalide : un joueur doit avoir 13 points et l’autre moins de 13.")

# --- Onglet 2 : Stats ---
with tabs[1]:
    st.header("Statistiques générales")
    if not df.empty:
        st.dataframe(df)

        # Exemple : pourcentage de victoires par joueur
        stats = []
        for joueur in joueurs:
            parties = df[(df["joueur_A"] == joueur) | (df["joueur_B"] == joueur)]
            if not parties.empty:
                victoires = (
                    ((parties["joueur_A"] == joueur) & (parties["score_A"] == 13))
                    | ((parties["joueur_B"] == joueur) & (parties["score_B"] == 13))
                ).sum()
                taux = 100 * victoires / len(parties)
                stats.append({"Joueur": joueur, "Victoires": victoires, "Parties": len(parties), "Winrate %": round(taux, 1)})

        if stats:
            st.dataframe(pd.DataFrame(stats).sort_values("Winrate %", ascending=False))
    else:
        st.info("Aucun résultat encore enregistré.")
