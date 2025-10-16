import streamlit as st
import gspread
import pandas as pd
import random

#############
# Affichage #
#############
st.set_page_config(page_title="Triplette", page_icon="👤👤👤")

st.write("# Parties en triplette du club de pétanque de Vaux-sur-Seine")
st.write("")
st.image("images/WIP2.jpg", use_container_width=True)
st.write("")
st.write("# Je finis les sections tête à tête et doublette et ensuite je m'en occupe 😉")