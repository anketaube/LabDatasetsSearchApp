import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import io

# URL anpassen
GITHUB_EXCEL_URL = "https://raw.githubusercontent.com/anketaube/LabDatasetsSearchApp/main/Datensets_Suche_Test.xlsx"

def load_data():
    try:
        st.info(f"Lade Daten von: `{GITHUB_EXCEL_URL}`")
        response = requests.get(GITHUB_EXCEL_URL)
        response.raise_for_status()
        excel_file = BytesIO(response.content)
        df = pd.read_excel(excel_file, engine='openpyxl', sheet_name='Tabelle2')
        df = df.replace('', pd.NA)
        return df
    except requests.exceptions.RequestException as e:
        st.error(f"Verbindungsfehler: {e}")
        return None
    except Exception as e:
        st.error(f"Fehler beim Laden der Excel-Datei: {e}")
        st.info("Stellen Sie sicher, dass die Datei eine gültige Excel-Datei ist und das Format .xlsx hat.")
        return None

def download_csv(df):
    csv = df.to_csv(index=False, encoding='utf-8')
    b = io.BytesIO()
    b.write(csv.encode('utf-8'))
    return b

def main():
    st.set_page_config(layout="wide")
    st.title("📚 DNBLab Datensetsuche")
    df = load_data()
    if df is None:
        st.stop()

    # Kategorie-Spalten identifizieren
    kategorie_spalten = [col for col in df.columns if 'Kategorie' in col]
    
    # Eindeutige Werte aus allen Kategorie-Spalten sammeln
    kategorie_werte = []
    for col in kategorie_spalten:
        kategorie_werte.extend(df[col].dropna().unique())
    kategorie_werte = list(set(kategorie_werte))  # Duplikate entfernen

    # Filterbereich
    st.header("Suchfilter")
    col1, col2, col3 = st.columns(3)

    # Kategorie-Filter (alle Kategorie-Spalten)
    kategorie_filter = col1.multiselect("Kategorie", options=kategorie_werte)

    # Andere Filter
    datensetname_filter = col2.multiselect("Datensetname", options=df['Datensetname'].dropna().unique())
    art_des_inhalts_filter = col3.multiselect("Art des Inhalts", options=df['Art des Inhalts'].dropna().unique())

    # Freitextsuche
    beschreibung_suchbegriff = st.text_input("Suche in Datensetbeschreibung")

    # Daten filtern
    filtered_df = df.copy()

    # Datensetbeschreibung
    if beschreibung_suchbegriff:
        filtered_df = filtered_df[filtered_df['Beschreibung'].str.contains(beschreibung_suchbegriff, case=False, na=False)]

    # Kategorie-Filter anwenden
    if kategorie_filter:
        # Zeilen behalten, wenn irgendeine der Kategorie-Spalten den Wert enthält
        filtered_df = filtered_df[filtered_df[kategorie_spalten].isin(kategorie_filter).any(axis=1)]

    # Andere Filter anwenden
    if datensetname_filter:
        filtered_df = filtered_df[filtered_df['Datensetname'].isin(datensetname_filter)]
    if art_des_inhalts_filter:
        filtered_df = filtered_df[filtered_df['Art des Inhalts'].isin(art_des_inhalts_filter)]

    # Ergebnisanzeige
    st.header("Suchergebnisse")
    st.write(f"Anzahl Ergebnisse: {len(filtered_df)}")
    st.dataframe(filtered_df, use_container_width=True)

    # Download-Button
    csv_file = download_csv(filtered_df)
    st.download_button(
        label="Ergebnisse als CSV herunterladen",
        data=csv_file,
        file_name="dnb_datensets.csv",
        mime="text/csv"
    )

if __name__ == "__main__":
    main()
