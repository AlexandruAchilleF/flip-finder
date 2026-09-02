import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    # Conectare la baza de date
    return psycopg2.connect(os.getenv("DATABASE_URL"))


def setup_database():
    conn = get_connection()
    cursor = conn.cursor()

    print("Stergem tabelele vechi ...")
    cursor.execute("DROP TABLE IF EXISTS istoric_preturi CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS apartamente CASCADE;")

    # Creare tabel static apartamente
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS apartamente (
            id_apartament SERIAL PRIMARY KEY,
            id_anunt_original VARCHAR(100) UNIQUE NOT NULL,
            url_anunt TEXT NOT NULL,
            oras VARCHAR(50),
            cartier VARCHAR(50),
            suprafata_mp INTEGER
        );
    """)

    # Creare tabel istoric pret
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS istoric_preturi (
            id_istoric SERIAL PRIMARY KEY,
            id_apartament INTEGER REFERENCES apartamente(id_apartament),
            pret NUMERIC NOT NULL,
            data_inregistrarii TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Creare tabel abonati telegram
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS abonati_telegram (
            chat_id BIGINT PRIMARY KEY
        );
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("Baza de date initializata cu succes!")


if __name__ == "__main__":
    setup_database()