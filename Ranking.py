import streamlit as st
import gspread
import pandas as pd

# Connexion à Google Sheets
gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
sh = gc.open_by_key(st.secrets["sheet"]["id"])

# Onglet "Résultats"
resultats = sh.worksheet("resultats")

# Onglet "Joueurs"
joueurs = sh.worksheet("joueurs")
prenoms = joueurs.col_values(1)[1:]
noms = joueurs.col_values(2)[1:]
liste_joueurs = [f"{p} {n}" for p, n in zip(prenoms, noms)]

# Charger les résultats existants
rows = resultats.get_all_records()
df = pd.DataFrame(rows)

# Onglets
tabs = st.tabs(["➕ Saisie des résultats", "Tableau des confrontations" , "📊 Classements"])

# --- Onglet 1 : Saisie ---
with tabs[0]:
    st.header("Saisie d'un nouveau résultat")

    with st.form("saisie_resultat"):
        joueur_A = st.selectbox("Joueur A", options=liste_joueurs)
        joueur_B = st.selectbox("Joueur B", options=[j for j in liste_joueurs if j != joueur_A])
        vainqueur = st.selectbox("Joueur A", options=[joueur_A, joueur_B])
        if vainqueur == joueur_A:
            score_A = 13
            st.number_input("Score A", min_value=13, max_value=13, value=13, disabled=True)
            score_B = st.number_input("Score B", min_value=0, max_value=12, value=0)
        else:
            score_B = 13
            st.number_input("Score B", min_value=13, max_value=13, value=13, disabled=True)
            score_A = st.number_input("Score A", min_value=0, max_value=12, value=0)
        submitted = st.form_submit_button("Enregistrer")

        if submitted:
           # Vérifier qu'il n’existe pas déjà un résultat entre ces deux joueurs
           existe_deja = False
           if not df.empty:
                existe_deja = (
                    ((df["joueur_A"] == joueur_A) & (df["joueur_B"] == joueur_B)).any()
                    or ((df["joueur_A"] == joueur_B) & (df["joueur_B"] == joueur_A)).any()
                )
                if existe_deja:
                    st.error("⚠️ Un résultat existe déjà pour cette paire de joueurs, s'il est nécessaire de le modifier veuillez contacter Stef-la-pétanque")
                else:
                    resultats.append_row([joueur_A, joueur_B, score_A, score_B, vainqueur])
                    st.success("✅ Résultat enregistré avec succès")

# --- Onglet 2 : Résultats récapitulatifs ---
with tabs[1]:
    st.header("Tableau des confrontations")

    # Création d’une matrice vide
    recap = pd.DataFrame("", index=liste_joueurs, columns=liste_joueurs)

    for _, row in df.iterrows():
        A, B, sA, sB = row["joueur_A"], row["joueur_B"], row["score_A"], row["score_B"]
        recap.loc[A, B] = sA
        recap.loc[B, A] = sB

    st.dataframe(recap)

# --- Onglet 3 : Classement général ---
with tabs[2]:
    st.header("Classement général")

    stats = {j: {"Victoires": 0, "Points marqués": 0, "Points encaissés": 0} for j in liste_joueurs}

    for _, row in df.iterrows():
        A, B, sA, sB = row["joueur_A"], row["joueur_B"], row["score_A"], row["score_B"]

        # Mise à jour des points
        stats[A]["Points marqués"] += sA
        stats[A]["Points encaissés"] += sB
        stats[B]["Points marqués"] += sB
        stats[B]["Points encaissés"] += sA

        # Attribution des victoires
        if sA > sB:
            stats[A]["Victoires"] += 1
        elif sB > sA:
            stats[B]["Victoires"] += 1

    # Conversion en DataFrame
    classement = pd.DataFrame(stats).T
    classement["Différence"] = classement["Points marqués"] - classement["Points encaissés"]

    # Tri : Victoires d'abord puis Différence
    classement = classement.sort_values(by=["Victoires", "Différence"], ascending=[False, False])

    st.dataframe(classement)
