# Flip Finder - Radar Imobiliar Bacău

Un sistem automatizat end-to-end de tip ETL (Extract, Transform, Load) conceput pentru a monitoriza piața imobiliară din Bacău. Proiectul extrage date zilnic de pe OLX, urmărește fluctuațiile de preț pentru fiecare apartament și trimite alerte automate, oferind în același timp un dashboard interactiv în cloud pentru analiză.

## Arhitectura Sistemului

Proiectul este împărțit în 4 componente principale:

1. **Extract (Extragere):** Un scraper Python care interoghează API-ul OLX, navighează prin pagini (pagination) și extrage anunțurile imobiliare.
2. **Transform (Curățare):** Folosind Pandas, datele sunt curățate, prețurile sunt standardizate în Euro (se aplică filtre de corecție pentru erorile utilizatorilor), iar cartierele sunt mapate.
3. **Load (Stocare):** Datele sunt încărcate într-o bază de date relațională serverless (Neon PostgreSQL), menținând un istoric al prețurilor.
4. **Visualize & Alert (Prezentare):** 
   - Un Dashboard interactiv construit cu Streamlit, publicat în cloud.
   - Un Bot de Telegram care trimite un raport zilnic detaliat cu prețurile care au crescut sau au scăzut.

## Tehnologii Folosite

* **Limbaj:** Python 3.14
* **Manipulare Date:** Pandas, Requests
* **Bază de Date:** PostgreSQL (găzduit pe Neon.tech), Psycopg2
* **Frontend:** Streamlit, Streamlit Cloud
* **Automatizare (CI/CD):** GitHub Actions (Cron Jobs)
* **Notificări:** Telegram Bot API

## Funcționalități Cheie

* **Urmărire Istoric Prețuri:** Baza de date face legătura între ID-ul apartamentului și fluctuațiile sale de preț în timp.
* **Filtre Interactive:** Dashboard-ul permite filtrarea dinamică a celor peste 700 de oferte pe cartiere și plafoane de preț.
* **Execuție Automată:** Sistemul rulează automat în fiecare dimineață la 08:17 prin GitHub Actions.
* **Securitate:** Parolarea bazei de date și a bot-ului de Telegram se face strict prin Variabile de Mediu (`.env` local, GitHub Secrets în cloud).

## Instrucțiuni de Configurare (Local)

Pentru a rula acest proiect:

1. **Clonează repository-ul:**
   ```bash
   git clone https://github.com/AlexandruAchilleF/flip-finder.git
   cd flip-finder
   ```

2. **Instalează dependențele:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setează variabilele de mediu:**
   Creează un fișier `.env` în folderul principal și adaugă următoarele credențiale:
   ```text
   DATABASE_URL=...
   TELEGRAM_TOKEN=...
   TELEGRAM_CHAT_ID=...
   ```

4. **Rulează scraper-ul manual:**
   ```bash
   python scraper.py
   ```

5. **Pornește Dashboard-ul local:**
   ```bash
   streamlit run dashboard.py
   ```

## Configurare GitHub Actions (Cloud)
Pentru automatizarea zilnică, asigură-te că ai adăugat cele 3 variabile din fișierul `.env` în secțiunea **Settings > Secrets and variables > Actions > Repository secrets** din repository-ul tău GitHub.
