import streamlit as st
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Configurare pagina
st.set_page_config(page_title="Flip Finder Bacau", layout="wide")
st.title("Radar Imobiliar - Flip Finder Bacău")
st.markdown("Monitorizează piața, descoperă scăderile de preț și găsește oportunități de investiții.")


# Extragerea si Transformarea Datelor
@st.cache_data(ttl=3600)
def incarca_date():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()

    # Aducem pretul initial si pretul actual folosind functii SQL
    query = """
    WITH IstoricOrdonat AS (
        SELECT 
            id_apartament, pret,
            ROW_NUMBER() OVER(PARTITION BY id_apartament ORDER BY data_inregistrarii ASC) as rn_asc,
            ROW_NUMBER() OVER(PARTITION BY id_apartament ORDER BY data_inregistrarii DESC) as rn_desc
        FROM istoric_preturi
    ),
    PreturiInitiale AS (
        SELECT id_apartament, pret as pret_initial FROM IstoricOrdonat WHERE rn_asc = 1
    ),
    PreturiActuale AS (
        SELECT id_apartament, pret as pret_actual FROM IstoricOrdonat WHERE rn_desc = 1
    )
    SELECT 
        a.id_apartament, a.url_anunt, a.cartier, a.suprafata_mp,
        pi.pret_initial, pa.pret_actual
    FROM apartamente a
    JOIN PreturiInitiale pi ON a.id_apartament = pi.id_apartament
    JOIN PreturiActuale pa ON a.id_apartament = pa.id_apartament
    """

    cur.execute(query)
    coloane = [desc[0] for desc in cur.description]
    date = cur.fetchall()

    df = pd.DataFrame(date, columns=coloane)
    cur.close()
    conn.close()

    df = df[df['suprafata_mp'] > 0] # Evitam impartirea cu 0

    # Calcule pentru analiza pietei
    df['pret_pe_mp'] = (df['pret_actual'] / df['suprafata_mp']).round(0)
    df['medie_cartier_mp'] = df.groupby('cartier')['pret_pe_mp'].transform('mean').round(0)
    df['reducere_euro'] = df['pret_initial'] - df['pret_actual']

    # Identificam oportunitatile (cu cel putin 15% sub media cartierului)
    def status_oportunitate(row):
        # Ignoram cartierele necunoscute
        if row['cartier'] == 'Necunoscut':
            return "Normal"

        if row['pret_pe_mp'] < (row['medie_cartier_mp'] * 0.85):
            return "Oportunitate"

        return "Normal"

    df['status'] = df.apply(status_oportunitate, axis=1)

    return df

df = incarca_date()

# Metrice Rapide
st.markdown("Pulsul Pieței")
col1, col2, col3, col4 = st.columns(4)

total_oferte = len(df)
pret_mediu_oras = int((df['pret_actual'].sum() / df['suprafata_mp'].sum()))
cea_mai_mare_reducere = int(df['reducere_euro'].max())
oportunitati_azi = len(df[df['status'] == "Oportunitate"])

col1.metric("Total Oferte Active", f"{total_oferte}")
col2.metric("Preț Mediu / mp (Oraș)", f"{pret_mediu_oras} €")
col3.metric("Cea Mai Mare Reducere", f"- {cea_mai_mare_reducere} €")
col4.metric("Oportunități Detectate", f"{oportunitati_azi}")

st.divider()

# Top scaderi de pret
st.markdown("### Top Scăderi de Preț")
df_reduceri = df[df['reducere_euro'] > 0].sort_values(by='reducere_euro', ascending=False)

if not df_reduceri.empty:
    st.dataframe(
        df_reduceri[['cartier', 'suprafata_mp', 'pret_initial', 'pret_actual', 'reducere_euro', 'url_anunt']],
        column_config={
            "url_anunt": st.column_config.LinkColumn("Link Anunț"),
            "pret_initial": st.column_config.NumberColumn("Preț Vechi (€)"),
            "pret_actual": st.column_config.NumberColumn("Preț Nou (€)"),
            "reducere_euro": st.column_config.NumberColumn("Scădere (€)")
        },
        hide_index=True,
        use_container_width=True
    )
else:
    st.info("Nu există nicio scădere de preț înregistrată momentan.")

st.divider()

# 5. Radarul Complet (Tabelul principal)
st.markdown("### Toate Ofertele (Analiză pe Cartier)")

# Filtre
col_filtru1, col_filtru2 = st.columns(2)
cartiere_selectate = col_filtru1.multiselect("Filtrează după Cartier:", options=df['cartier'].unique())
pret_maxim = col_filtru2.number_input("Preț Maxim (€):", min_value=0, value=250000, step=1000)

# Aplicam filtrele
df_filtrat = df.copy()
if cartiere_selectate:
    df_filtrat = df_filtrat[df_filtrat['cartier'].isin(cartiere_selectate)]
df_filtrat = df_filtrat[df_filtrat['pret_actual'] <= pret_maxim]

# Sortam oportunitatile primele
df_filtrat = df_filtrat.sort_values(by=['status', 'pret_pe_mp'], ascending=[False, True])

st.dataframe(
    df_filtrat[['status', 'cartier', 'suprafata_mp', 'pret_actual', 'pret_pe_mp', 'medie_cartier_mp', 'url_anunt']],
    column_config={
        "status": "Evaluare",
        "url_anunt": st.column_config.LinkColumn("Deschide Anunț"),
        "pret_actual": st.column_config.NumberColumn("Preț (€)"),
        "pret_pe_mp": st.column_config.NumberColumn("Preț/mp"),
        "medie_cartier_mp": st.column_config.NumberColumn("Medie Cartier/mp")
    },
    hide_index=True,
    use_container_width=True
)