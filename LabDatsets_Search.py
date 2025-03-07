import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# 1. URL anpassen (Beispiel - ersetzen!)
GITHUB_EXCEL_URL = "https://raw.githubusercontent.com/anketaube/LabDatasetsSearchApp/main/Datensets_Suche_Test.xlsx"

def load_data():
    try:
        st.info(f"Lade Daten von: `{GITHUB_EXCEL_URL}`")  # URL anzeigen
        response = requests.get(GITHUB_EXCEL_URL)
        response.raise_for_status()  # Fehler bei HTTP-Fehlern

        excel_file = BytesIO(response.content)
        df = pd.read_excel(excel_file, engine='openpyxl', sheet_name='Tabelle2')
        return df

    except requests.exceptions.RequestException as e:
        st.error(f"Verbindungsfehler: {e}")
        return None
    except Exception as e:
        st.error(f"Fehler beim Laden der Excel-Datei: {e}")
        st.info("Stellen Sie sicher, dass die Datei eine gültige Excel-Datei ist und das Format .xlsx hat.")
        return None

def main():
    st.title("DNB-Datenset-Suche")

    df = load_data()
    if df is None:
        st.stop()

    # Filter-Sidebar
    with st.sidebar:
        st.header("Filter")
        
        # Freitextsuche
        suchbegriff = st.text_input("Suchbegriff")

        # Kategorie 1 Filter
        kategorie1_filter = st.multiselect("Kategorie 1", options=df['Kategorie 1'].unique())

        # Verfügbarkeit Filter
        verfuegbarkeit_filter = st.selectbox("Online verfügbar", options=['Alle'] + list(df['Online frei verfügbar'].unique()))

    # Daten filtern
    filtered_df = df.copy()

    if suchbegriff:
        filtered_df = filtered_df[filtered_df.astype(str).apply(lambda row: row.str.contains(suchbegriff, case=False).any(), axis=1)]

    if kategorie1_filter:
        filtered_df = filtered_df[filtered_df['Kategorie 1'].isin(kategorie1_filter)]

    if verfuegbarkeit_filter != 'Alle':
        filtered_df = filtered_df[filtered_df['Online frei verfügbar'] == verfuegbarkeit_filter]

    # Ergebnisanzeige
    st.header("Ergebnisse")
    st.write(f"Anzahl Ergebnisse: {len(filtered_df)}")
    st.dataframe(filtered_df)

if __name__ == "__main__":
    main()
