{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 1,
   "id": "6f88df93-dff0-4e3a-a501-427b008db771",
   "metadata": {
    "execution": {
     "iopub.execute_input": "2025-09-29T12:49:42.731216Z",
     "iopub.status.busy": "2025-09-29T12:49:42.730218Z",
     "iopub.status.idle": "2025-09-29T12:49:46.745161Z",
     "shell.execute_reply": "2025-09-29T12:49:46.743162Z",
     "shell.execute_reply.started": "2025-09-29T12:49:42.731216Z"
    }
   },
   "outputs": [],
   "source": [
    "import streamlit as st\n",
    "import pandas as pd\n",
    "import os\n",
    "\n",
    "# -------------------------\n",
    "# Onglets Streamlit\n",
    "# -------------------------\n",
    "tabs = st.tabs([\"➕ Saisie des résultats\", \"📊 Statistiques\"])\n",
    "\n",
    "# Onglet 1 : Saisie des résultats\n",
    "with tabs[0]:\n",
    "    st.header(\"Saisie d'un nouveau résultat\")\n",
    "\n",
    "    joueurs = list(set(df[\"joueur_A\"]).union(set(df[\"joueur_B\"]))) if not df.empty else []\n",
    "    new_joueur_A = st.text_input(\"Joueur A\")\n",
    "    new_joueur_B = st.text_input(\"Joueur B\")\n",
    "    score_A = st.number_input(\"Score A\", min_value=0, max_value=13, value=0)\n",
    "    score_B = st.number_input(\"Score B\", min_value=0, max_value=13, value=0)\n",
    "\n",
    "    if st.button(\"Enregistrer le résultat\"):\n",
    "        if new_joueur_A and new_joueur_B and new_joueur_A != new_joueur_B:\n",
    "            vainqueur = new_joueur_A if score_A > score_B else new_joueur_B\n",
    "            new_data = pd.DataFrame([[new_joueur_A, new_joueur_B, score_A, score_B, vainqueur]],\n",
    "                                    columns=df.columns)\n",
    "            df = pd.concat([df, new_data], ignore_index=True)\n",
    "            df.to_csv(DATA_FILE, index=False)\n",
    "            st.success(\"Résultat enregistré !\")\n",
    "        else:\n",
    "            st.error(\"Vérifiez les noms des joueurs\")\n",
    "\n",
    "# Onglet 2 : Statistiques\n",
    "with tabs[1]:\n",
    "    st.header(\"Classement et statistiques\")\n",
    "\n",
    "    if df.empty:\n",
    "        st.info(\"Aucun résultat enregistré pour l'instant.\")\n",
    "    else:\n",
    "        # Calcul des stats par joueur\n",
    "        joueurs = set(df[\"joueur_A\"]).union(set(df[\"joueur_B\"]))\n",
    "        stats = []\n",
    "        for j in joueurs:\n",
    "            jouees = len(df[(df[\"joueur_A\"] == j) | (df[\"joueur_B\"] == j)])\n",
    "            gagnees = len(df[df[\"vainqueur\"] == j])\n",
    "            perdues = jouees - gagnees\n",
    "            points_marques = df.loc[df[\"joueur_A\"] == j, \"score_A\"].sum() + df.loc[df[\"joueur_B\"] == j, \"score_B\"].sum()\n",
    "            points_encaisses = df.loc[df[\"joueur_A\"] == j, \"score_B\"].sum() + df.loc[df[\"joueur_B\"] == j, \"score_A\"].sum()\n",
    "            goal_average = points_marques - points_encaisses\n",
    "            stats.append([j, jouees, gagnees, perdues, round(gagnees/jouees*100,1) if jouees>0 else 0, points_marques, points_encaisses, goal_average])\n",
    "\n",
    "        stats_df = pd.DataFrame(stats, columns=[\"Joueur\", \"Parties jouées\", \"Victoires\", \"Défaites\", \"% Victoires\", \"Points marqués\", \"Points encaissés\", \"Goal Average\"])\n",
    "        stats_df = stats_df.sort_values(by=[\"Victoires\", \"Goal Average\"], ascending=[False, False])\n",
    "\n",
    "        st.dataframe(stats_df, use_container_width=True)\n",
    "\n",
    "        # Graphique simple\n",
    "        st.bar_chart(stats_df.set_index(\"Joueur\")[\"Victoires\"])"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3 (ipykernel)",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.12.9"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
