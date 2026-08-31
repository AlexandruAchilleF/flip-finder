import streamlit as st
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv
import time
import streamlit as st

load_dotenv()

# Configuram aspectul paginii web
st.set_page_config(page_title="Flip Finder Dashboard", page_icon="🏡", layout="wide")
st.title("Flip Finder - Radar Imobiliar Bacău")


# Functie pentru conectare (folosim @st.cache_resource ca sa nu se reconecteze la fiecare click)
@st.cache_resource
def get_connection():
    return psycopg2.connect(st.secrets["DATABASE_URL"])



# Functie pentru a extrage lista de apartamente cu ultimul lor pret
@st.cache_data(ttl=60)  # Pastreaza datele în memorie 60 de secunde
def load_latest_data():
    conn = get_connection()
    query = """
        SELECT 
            a.id_apartament AS "ID",
            a.cartier AS "Cartier",
            a.suprafata_mp AS "Suprafață (mp)",
            ip.pret AS "Preț Curent (€)",
            a.url_anunt AS "Link URL"
        FROM apartamente a
        JOIN istoric_preturi ip ON a.id_apartament = ip.id_apartament
        WHERE ip.data_inregistrarii = (
            SELECT MAX(data_inregistrarii) 
            FROM istoric_preturi 
            WHERE id_apartament = a.id_apartament
        )
        ORDER BY ip.pret ASC;
    """
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df = pd.read_sql(query, conn)
    return df


# Functie pentru a trage istoricul unui singur apartament (pentru grafic)
def load_price_history(id_apartament):
    conn = get_connection()
    query = f"""
        SELECT data_inregistrarii AS "Data", pret AS "Preț"
        FROM istoric_preturi
        WHERE id_apartament = {id_apartament}
        ORDER BY data_inregistrarii ASC;
    """
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return pd.read_sql(query, conn)


# Construirea interfatei grafice

df_apartamente = load_latest_data()

st.write(f"**{len(df_apartamente)}** oferte monitorizate în prezent.")

# Imparțim ecranul în doua coloane
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Lista Apartamentelor (Cele mai ieftine primele)")
    # Afisam tabelul interactiv
    st.dataframe(df_apartamente, use_container_width=True, hide_index=True)

with col2:
    st.subheader("Istoric Preț")
    if not df_apartamente.empty:
        # Cream un meniu de selectie (Dropdown)
        apartament_selectat = st.selectbox(
            "Selectează ID-ul unui apartament pentru a-i vedea graficul:",
            df_apartamente['ID']
        )

        # Extragem si desenam graficul pentru apartamentul selectat
        df_istoric = load_price_history(apartament_selectat)

        # Setam coloana de date ca index pentru a fi afisată pe axa X
        df_istoric.set_index('Data', inplace=True)
        st.line_chart(df_istoric)
    else:
        st.info("Baza de date este goală. Rulează scraper.py mai întâi!")