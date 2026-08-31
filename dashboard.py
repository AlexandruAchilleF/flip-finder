import streamlit as st
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv
import time

load_dotenv()

# Configuram aspectul paginii web
st.set_page_config(page_title="Flip Finder Dashboard", page_icon="🏡", layout="wide")
st.title("Flip Finder - Radar Imobiliar Bacău")


# Functie pentru conectare
def get_connection():
    return psycopg2.connect(st.secrets["DATABASE_URL"])


# Functie pentru a extrage lista de apartamente
@st.cache_data(ttl=60)
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
    conn.close()
    return df


# Functie pentru a extrage istoricul unui singur apartament
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
        df = pd.read_sql(query, conn)
    conn.close()
    return df

# Construirea interfatei
df_apartamente = load_latest_data()

if not df_apartamente.empty:

    st.sidebar.header("Filtrează Anunțurile")

    # Filtru Cartier
    lista_cartiere = ["Toate"] + list(df_apartamente['Cartier'].unique())
    cartier_ales = st.sidebar.selectbox("Alege cartierul:", lista_cartiere)

    # Filtru Pret
    pret_min = int(df_apartamente['Preț Curent (€)'].min())
    pret_max = int(df_apartamente['Preț Curent (€)'].max())
    pret_ales = st.sidebar.slider("Preț maxim (€):", pret_min, pret_max, pret_max)

    # Aplicam filtrele
    df_filtrat = df_apartamente[df_apartamente['Preț Curent (€)'] <= pret_ales]
    if cartier_ales != "Toate":
        df_filtrat = df_filtrat[df_filtrat['Cartier'] == cartier_ales]

    st.write(f"S-au găsit **{len(df_filtrat)}** oferte (din totalul de {len(df_apartamente)}).")

    #Afisare rezultate
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Lista Apartamentelor")
        # Tabel cu link-uri
        st.dataframe(
            df_filtrat,
            column_config={
                "Link URL": st.column_config.LinkColumn(
                    "Link Anunț", display_text="Vezi pe OLX"
                )
            },
            hide_index=True,
            use_container_width=True
        )

    with col2:
        st.subheader("Istoric Preț")
        if not df_filtrat.empty:
            # Dropdown doar cu ID-urile vizibile dupa filtrare
            apartament_selectat = st.selectbox(
                "Selectează ID-ul pentru grafic:",
                df_filtrat['ID']
            )

            # Desenam graficul
            df_istoric = load_price_history(apartament_selectat)
            df_istoric.set_index('Data', inplace=True)
            st.line_chart(df_istoric)
        else:
            st.info("Niciun apartament nu se potrivește filtrelor tale..️")

else:
    st.info("Baza de date este goala")