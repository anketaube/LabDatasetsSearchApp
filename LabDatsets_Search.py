# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# GitHub RAW URL der Excel-Datei (ändern Sie diesen Link!)
GITHUB_EXCEL_URL = "https://raw.githubusercontent.com/IHR_BENUTZERNAME/IHR_REPO/main/Datensets_Suche_Test.xlsx"

def load_data():
    try:
        response = requests.get(GITHUB_EXCEL_URL)
        excel_data = pd.read_excel(BytesIO(response.content), sheet_name='Tabelle2')
        return excel_data
    except Exception as e:
        st.error(f"Fehler beim Laden der Daten: {e}")
        return None

def main():
    st.set_page_config(page_title="DNB-Datenset-Suche", layout="wide")
    st.title("📚 Deutsche Nationalbibliothek - Datenset-Suche")

    # Daten laden
    df = load_data()
    if df is None:
        return

    # Sidebar-Filter
    with st.sidebar:
        st.header("Filteroptionen")
        
        # Freitextsuche
        freitext = st.text_input("Volltextsuche (z.B. in Beschreibungen):")

        # Standardisierte Filter
        kategorie_filter = st.multiselect(
            "Kategorie 1 auswählen:",
            options=df['Kategorie 1'].dropna().unique()
        )

        verfügbarkeit_filter = st.selectbox(
            "Online verfügbar:",
            options=['Alle'] + list(df['Online frei verfügbar'].dropna().unique())
        )

    # Filter anwenden
    filtered_df = df.copy()
    
    if freitext:
        filtered_df = filtered_df[
            filtered_df.apply(lambda row: row.astype(str).str.contains(freitext, case=False).any(), axis=1)
        ]

    if kategorie_filter:
        filtered_df = filtered_df[filtered_df['Kategorie 1'].isin(kategorie_filter)]

    if verfügbarkeit_filter != 'Alle':
        filtered_df = filtered_df[filtered_df['Online frei verfügbar'] == verfügbarkeit_filter]

    # Ergebnisse anzeigen
    with st.expander("🔍 Suchresultate", expanded=True):
        col1, col2, col3 = st.columns(3)
        col1.metric("Gefundene Datensets", len(filtered_df))
        col2.metric("Durchschn. Größe", f"{filtered_df['Download Größe (GB)'].mean():.1f} GB")
        col3.metric("Ältester Datensatz", filtered_df['Zeitraum der Daten'].min())

        # Link-Spalte hinzufügen
        filtered_df['Link'] = filtered_df['Kurz URL'].apply(
            lambda x: f'<a href="{x}" target="_blank">🔗 Zum Katalog</a>' if pd.notnull(x) else ''
        )

        # DataFrame mit ausgewählten Spalten anzeigen
        st.write(
            filtered_df[['Datensetname', 'Art des Inhalts', 'Zeitraum der Daten', 
                        'Download Größe (GB)', 'Link']].to_html(escape=False), 
            unsafe_allow_html=True
        )

if __name__ == "__main__":
    main()
