import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import io

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

def download_csv(df):
    """Generiert eine CSV-Datei und gibt einen Download-Button zurück."""
    csv = df.to_csv(index=False, encoding='utf-8')  # UTF-8 encoding
    b = io.BytesIO()
    b.write(csv.encode('utf-8'))
    return b

def main():
    st.title("DNB-Datenset-Suche")

    df = load_data()
    if df is None:
        st.stop()

    # Filterbereich oberhalb der Tabelle
    st.header("Suchfilter")

    # Layout für die Filter
    col1, col2 = st.columns([2, 1])  # Unterschiedliche Breiten

    # Zeile 1
    kategorie_filter = col1.multiselect("Kategorie", options=df['Kategorie 1'].dropna().unique())  # Kombinierter Filter
    datensetname_filter = col1.multiselect("Datensetname", options=df['Datensetname'].unique())  # Breite Spalte

    # Zeile 2
    art_des_inhalts_filter = col1.multiselect("Art des Inhalts", options=df['Art des Inhalts'].unique())
    zeitraum_der_daten_filter = col2.multiselect("Zeitraum der Daten", options=df['Zeitraum der Daten '].unique())

    # Zeile 3
    digitale_objekte_filter = col1.multiselect("Digitale Objekte", options=df['Digitale Objekte '].unique())
    online_frei_verfügbar_filter = col2.multiselect("Online frei verfügbar", options=df['Online frei verfügbar'].unique())
    anzahl_datensätze_filter = col1.multiselect("Anzahl Datensätze", options=df['Anzahl Datensätze'].unique())

    # Zeile 4
    datenformat_filter = col1.multiselect("Datenformat", options=df['Datenformat'].unique())
    download_filter = col2.multiselect("Download", options=df['Download'].unique())
    schnittstelle_filter = col1.multiselect("Schnittstelle", options=df['Schnittstelle'].unique())
    download_größe_gb_filter = col2.multiselect("Download Größe (GB)", options=df['Download Größe (GB)'].unique())

    # Datensetbeschreibung-Filter
    beschreibung_suchbegriff = st.text_input("Suche in Datensetbeschreibung")

    # Daten filtern
    filtered_df = df.copy()

    # Datensetbeschreibung
    if beschreibung_suchbegriff:
        filtered_df = filtered_df[filtered_df['Beschreibung'].str.contains(beschreibung_suchbegriff, case=False, na=False)]

    # Kategorien-Filter
    if kategorie_filter:
        filtered_df = filtered_df[
            filtered_df['Kategorie 1'].isin(kategorie_filter) |
            filtered_df['Kategorie 2'].isin(kategorie_filter) |
            filtered_df['Kategorie 3'].isin(kategorie_filter)
        ]

    # Andere Filter anwenden
    if datensetname_filter:
        filtered_df = filtered_df[filtered_df['Datensetname'].isin(datensetname_filter)]
    if art_des_inhalts_filter:
        filtered_df = filtered_df[filtered_df['Art des Inhalts'].isin(art_des_inhalts_filter)]
    if zeitraum_der_daten_filter:
        filtered_df = filtered_df[filtered_df['Zeitraum der Daten '].isin(zeitraum_der_daten_filter)]
    if digitale_objekte_filter:
        filtered_df = filtered_df[filtered_df['Digitale Objekte '].isin(digitale_objekte_filter)]
    if online_frei_verfügbar_filter:
        filtered_df = filtered_df[filtered_df['Online frei verfügbar'].isin(online_frei_verfügbar_filter)]
    if anzahl_datensätze_filter:
        filtered_df = filtered_df[filtered_df['Anzahl Datensätze'].isin(anzahl_datensätze_filter)]
    if datenformat_filter:
        filtered_df = filtered_df[filtered_df['Datenformat'].isin(datenformat_filter)]
    if download_filter:
        filtered_df = filtered_df[filtered_df['Download'].isin(download_filter)]
    if schnittstelle_filter:
        filtered_df = filtered_df[filtered_df['Schnittstelle'].isin(schnittstelle_filter)]
    if download_größe_gb_filter:
        filtered_df = filtered_df[filtered_df['Download Größe (GB)'].isin(download_größe_gb_filter)]

    # Ergebnisanzeige
    st.header("Suchergebnisse")
    st.write(f"Anzahl Ergebnisse: {len(filtered_df)}")
    st.dataframe(filtered_df)

    # Download-Button
    csv_file = download_csv(filtered_df)
    st.download_button(
        label="Ergebnisse als CSV herunterladen",
        data=csv_file,
        file_name="dnb_datensets.csv",
        mime="text/csv",
    )

if __name__ == "__main__":
    main()
