# utils.py
import streamlit as st
import gspread

def init_google_sheets():
    """Initialise la connexion Google Sheets si nécessaire"""
    if 'sheets_loaded' not in st.session_state:
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        sh = gc.open_by_key(st.secrets["sheet"]["id"])
        
        # Charger tous les worksheets
        st.session_state.sheet_joueurs = sh.worksheet("joueurs")
        st.session_state.sheet_resultats_tat = sh.worksheet("resultats_tat")
        st.session_state.sheet_resultats_doub = sh.worksheet("resultats_doub")
        st.session_state.sheet_resultats_trip = sh.worksheet("resultats_trip")
        st.session_state.sheet_tournoi_tat = sh.worksheet("tournoi_tat")
        st.session_state.sheet_tournoi_doub = sh.worksheet("tournoi_doub")
        st.session_state.sheet_tournoi_trip = sh.worksheet("tournoi_trip")
        st.session_state.sheet_championnat_tat = sh.worksheet("championnat_tat")
        st.session_state.sheet_championnat_doub = sh.worksheet("championnat_doub")
        st.session_state.sheet_championnat_trip = sh.worksheet("championnat_trip")
        
        # Charger les joueurs
        prenoms = st.session_state.sheet_joueurs.col_values(1)[1:]
        noms = st.session_state.sheet_joueurs.col_values(2)[1:]
        st.session_state.liste_joueurs_complet = [f"{p} {n}" for p, n in zip(prenoms, noms)]
        
        st.session_state.sheets_loaded = True