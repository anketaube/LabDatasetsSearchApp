# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# 1. ERFORDERLICHE KORREKTUR: GitHub RAW-URL anpassen
GITHUB_EXCEL_URL = "https://raw.githubusercontent.com/IHR_BENUTZERNAME/IHR_REPO/main/Datensets_Suche_Test.xlsx"

def load_data():
    try:
        response = requests.get(GITHUB_EXCEL_URL)
        
        # 2. WICHTIGER FIX: Engine explizit angeben
        excel_data = pd.read_excel(
            BytesIO(response.content),
            engine='openpyxl',  # <-- Korrektur hier
            sheet_name='Tabelle2'
        )
        
        # 3. Datenbereinigung für fehlerhafte Zeitangaben
        excel_data['Zeitraum der Daten'] = excel_data['Zeitraum der Daten'].astype(str).str.replace('19:33', '1933')
        
        return excel_data
    except Exception as e:
        st.error(f"Technischer Fehler: {str(e)}")
        st.info("Bitte folgendes prüfen:")
        st.write("- RAW-URL der Excel-Datei in Zeile 7")
        st.write("- Sheet-Name muss 'Tabelle2' sein")
        return None

def main():
    st.set_page_config(page_title="DNB-Datenset-Suche", layout="wide")
    st.title("📚 Deutsche Nationalbibliothek - Datenset-Suche")

    df = load_data()
    if df is None:
        return

    with st.sidebar:
        st.header("Filteroptionen")
        freitext = st.text_input("Volltextsuche:")
        
        # Dynamische Filteroptionen
        kategorie_options = df['Kategorie 1'].dropna().unique().tolist()
        kategorie_filter = st.multiselect(
            "Kategorie 1:",
            options=kategorie_options
        )

        verfügbarkeit_options = ['Alle'] + df['Online frei verfügbar'].dropna().unique().tolist()
        verfügbarkeit_filter = st.selectbox(
            "Online verfügbar:",
            options=verfügbarkeit_options
        )

    # Filterlogik
    filtered_df = df.copy()
    
    if freitext:
        filtered_df = filtered_df[
            filtered_df.apply(lambda row: row.astype(str).str.contains(freitext, case=False).any(), axis=1)
        ]
    
    if kategorie_filter:
        filtered_df = filtered_df[filtered_df['Kategorie 1'].isin(kategorie_filter)]
    
    if verfügbarkeit_filter != 'Alle':
        filtered_df = filtered_df[filtered_df['Online frei verfügbar'] == verfügbarkeit_filter]

    # Ergebnisanzeige
    with st.expander("🔍 Suchresultate", expanded=True):
        st.write(f"**Gefundene Datensets:** {len(filtered_df)}")
        
        # Link-Generierung
        filtered_df['Link'] = filtered_df['Kurz URL'].apply(
            lambda x: f'<a href="{x}" target="_blank">🔗 Zum Katalog</a>' if pd.notnull(x) and x != 'Folgt…' else ''
        )

        # Tabellenformatierung
        st.write(
            filtered_df[['Datensetname', 'Art des Inhalts', 'Zeitraum der Daten', 
                        'Download Größe (GB)', 'Link']].to_html(escape=False, index=False), 
            unsafe_allow_html=True
        )

if __name__ == "__main__":
    main()
