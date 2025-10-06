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
tabs = st.tabs(["➕ Saisie des résultats", "📊 Tableau des confrontations", "🏆 Classements"])

# --- Onglet 1 : Saisie ---
with tabs[0]:
    st.header("Saisie d'un nouveau résultat")
    
    # Étape 1 : Sélection du vainqueur (hors formulaire)
    vainqueur = st.selectbox("🏆 Qui a gagné ?", options=liste_joueurs, key="vainqueur")
    
    # Étape 2 : Une fois le vainqueur choisi, afficher le reste
    if vainqueur:
        st.divider()
        
        with st.form("saisie_resultat"):
            # Liste des adversaires possibles (tous sauf le vainqueur)
            adversaires_possibles = [j for j in liste_joueurs if j != vainqueur]
            adversaire = st.selectbox("👤 Contre qui ?", options=adversaires_possibles, key="adversaire")
            
            score_adv = st.number_input("Score du joueur perdant", min_value=0, max_value=12, value=0, key="score_adv")
            score_vainqueur = 13
            
            st.caption(f"Résultat : **{vainqueur}** 13 - {score_adv} **{adversaire}**")
            
            submitted = st.form_submit_button("✅ Enregistrer le résultat", use_container_width=True)
        
        if submitted:
            # Vérifier qu'il n'existe pas déjà un résultat entre ces deux joueurs
            existe_deja = False
            if not df.empty:
                existe_deja = (
                    ((df["vainqueur"] == vainqueur) & (df["adversaire"] == adversaire)).any()
                    or ((df["vainqueur"] == adversaire) & (df["adversaire"] == vainqueur)).any()
                )
            
            if existe_deja:
                st.error("⚠️ Un résultat existe déjà pour cette paire de joueurs. Pour le modifier, contacte Stef-la-pétanque")
            else:
                # Ajouter le résultat
                resultats.append_row([vainqueur, adversaire, score_vainqueur, score_adv])
                st.success("✅ Résultat enregistré avec succès !")
                st.rerun()

# --- Onglet 2 : Tableau des confrontations ---
with tabs[1]:
    st.header("Tableau des confrontations")
    
    if df.empty:
        st.info("Aucun résultat enregistré pour le moment")
    else:
        # Création d'une matrice vide
        recap = pd.DataFrame("", index=liste_joueurs, columns=liste_joueurs)
        
        for _, row in df.iterrows():
            vainq = row["vainqueur"]
            adv = row["adversaire"]
            score_v = row.get("score_vainqueur", 13)
            score_a = row.get("score_adversaire", row.get("score_adv", 0))
            
            # Remplir la matrice
            recap.loc[vainq, adv] = f"{score_v}-{score_a}"
            recap.loc[adv, vainq] = f"{score_a}-{score_v}"
        
        st.dataframe(recap, use_container_width=True)

# --- Onglet 3 : Classement général ---
with tabs[2]:
    st.header("Classement général")
    
    if df.empty:
        st.info("Aucun résultat enregistré pour le moment")
    else:
        stats = {j: {"Victoires": 0, "Défaites": 0, "Points marqués": 0, "Points encaissés": 0} for j in liste_joueurs}
        
        for _, row in df.iterrows():
            vainq = row["vainqueur"]
            adv = row["adversaire"]
            score_v = row.get("score_vainqueur", 13)
            score_a = row.get("score_adversaire", row.get("score_adv", 0))
            
            # Mise à jour des statistiques
            stats[vainq]["Victoires"] += 1
            stats[vainq]["Points marqués"] += score_v
            stats[vainq]["Points encaissés"] += score_a
            
            stats[adv]["Défaites"] += 1
            stats[adv]["Points marqués"] += score_a
            stats[adv]["Points encaissés"] += score_v
        
        # Conversion en DataFrame
        classement = pd.DataFrame(stats).T
        classement["Différence"] = classement["Points marqués"] - classement["Points encaissés"]
        classement["Parties jouées"] = classement["Victoires"] + classement["Défaites"]
        classement["% victoires"] = (classement["Victoires"] / classement["Parties jouées"])*100
        
        # Tri : Victoires d'abord puis Différence
        classement = classement.sort_values(by=["Victoires", "Différence"], ascending=[False, False])
        
        # Réorganiser les colonnes
        classement = classement[["Parties jouées", "% victoires", "Victoires", "Défaites", "Différence", "Points marqués", "Points encaissés"]]
        
        st.dataframe(classement, use_container_width=True)
