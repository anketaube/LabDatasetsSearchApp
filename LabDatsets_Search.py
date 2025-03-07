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

    # **Filterbereich oberhalb der Tabelle**
    st.header("Suchfilter")

    # Layout für die Filter
    col1, col2, col3 = st.columns(3)  # Drei Spalten für Filter

    # Volltextsuche in der Beschreibung
    beschreibung_suchbegriff = col1.text_input("Suche in Beschreibung")

    # Kombinierter Kategorien-Filter
    alle_kategorien = df['Kategorie 1'].dropna().unique().tolist() + \
                       df['Kategorie 2'].dropna().unique().tolist() + \
                       df['Kategorie 3'].dropna().unique().tolist()
    alle_kategorien = list(set(alle_kategorien))  # Duplikate entfernen
    kategorie_filter = col2.multiselect("Kategorien (1, 2, 3)", options=alle_kategorien)

    # Filter für andere Spalten (beispielhaft)
    datensetname_filter = col3.multiselect("Datensetname", options=df['Datensetname'].unique())
    anzahl_datensätze_filter = col1.multiselect("Anzahl Datensätze", options=df['Anzahl Datensätze'].unique())
    online_frei_verfügbar_filter = col2.multiselect("Online frei verfügbar", options=df['Online frei verfügbar'].unique())

    # Daten filtern
    filtered_df = df.copy()

    # Volltextsuche in Beschreibung
    if beschreibung_suchbegriff:
        filtered_df = filtered_df[filtered_df['Beschreibung'].str.contains(beschreibung_suchbegriff, case=False, na=False)]

    # Kategorien-Filter
    if kategorie_filter:
        filtered_df = filtered_df[
            filtered_df['Kategorie 1'].isin(kategorie_filter) |
            filtered_df['Kategorie 2'].isin(kategorie_filter) |
            filtered_df['Kategorie 3'].isin(kategorie_filter)
        ]

    # Andere Filter anwenden (beispielhaft)
    if datensetname_filter:
        filtered_df = filtered_df[filtered_df['Datensetname'].isin(datensetname_filter)]
    if anzahl_datensätze_filter:
        filtered_df = filtered_df[filtered_df['Anzahl Datensätze'].isin(anzahl_datensätze_filter)]
    if online_frei_verfügbar_filter:
        filtered_df = filtered_df[filtered_df['Online frei verfügbar'].isin(online_frei_verfügbar_filter)]

    # **Ergebnisanzeige**
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
