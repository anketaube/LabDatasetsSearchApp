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

    # Aufteilung in Sidebar und Main Panel
    sidebar, main_panel = st.columns([1, 3])  # Sidebar ist 1/4, Main Panel 3/4 der Breite

    with sidebar:
        st.header("Suchfilter")

        # Volltextsuche in der Beschreibung
        beschreibung_suchbegriff = st.text_input("Suche in Beschreibung")

        # Filter für jede Spalte
        datensetname_filter = st.multiselect("Datensetname", options=df['Datensetname'].unique())
        anzahl_datensätze_filter = st.multiselect("Anzahl Datensätze", options=df['Anzahl Datensätze'].unique())
        digitale_objekte_filter = st.multiselect("Digitale Objekte", options=df['Digitale Objekte '].unique())
        online_frei_verfügbar_filter = st.multiselect("Online frei verfügbar", options=df['Online frei verfügbar'].unique())
        download_filter = st.multiselect("Download", options=df['Download'].unique())
        schnittstelle_filter = st.multiselect("Schnittstelle", options=df['Schnittstelle'].unique())
        datenformat_filter = st.multiselect("Datenformat", options=df['Datenformat'].unique())
        download_größe_gb_filter = st.multiselect("Download Größe (GB)", options=df['Download Größe (GB)'].unique())
        art_des_inhalts_filter = st.multiselect("Art des Inhalts", options=df['Art des Inhalts'].unique())
        zeitraum_der_daten_filter = st.multiselect("Zeitraum der Daten", options=df['Zeitraum der Daten '].unique())
        aktualisierung_der_daten_filter = st.multiselect("Aktualisierung der Daten", options=df['Aktualisierung der Daten '].unique())
        kategorie_1_filter = st.multiselect("Kategorie 1", options=df['Kategorie 1'].unique())
        kategorie_2_filter = st.multiselect("Kategorie 2", options=df['Kategorie 2'].unique())
        kategorie_3_filter = st.multiselect("Kategorie 3", options=df['Kategorie 3'].unique())
        sammlung_im_katalog_filter = st.multiselect("Sammlung im Katalog", options=df['Sammlung im Katalog'].unique())

    # Daten filtern
    filtered_df = df.copy()

    # Volltextsuche in Beschreibung
    if beschreibung_suchbegriff:
        filtered_df = filtered_df[filtered_df['Beschreibung'].str.contains(beschreibung_suchbegriff, case=False, na=False)]

    # Filter anwenden
    if datensetname_filter:
        filtered_df = filtered_df[filtered_df['Datensetname'].isin(datensetname_filter)]
    if anzahl_datensätze_filter:
        filtered_df = filtered_df[filtered_df['Anzahl Datensätze'].isin(anzahl_datensätze_filter)]
    if digitale_objekte_filter:
        filtered_df = filtered_df[filtered_df['Digitale Objekte '].isin(digitale_objekte_filter)]
    if online_frei_verfügbar_filter:
        filtered_df = filtered_df[filtered_df['Online frei verfügbar'].isin(online_frei_verfügbar_filter)]
    if download_filter:
        filtered_df = filtered_df[filtered_df['Download'].isin(download_filter)]
    if schnittstelle_filter:
        filtered_df = filtered_df[filtered_df['Schnittstelle'].isin(schnittstelle_filter)]
    if datenformat_filter:
        filtered_df = filtered_df[filtered_df['Datenformat'].isin(datenformat_filter)]
    if download_größe_gb_filter:
        filtered_df = filtered_df[filtered_df['Download Größe (GB)'].isin(download_größe_gb_filter)]
    if art_des_inhalts_filter:
        filtered_df = filtered_df[filtered_df['Art des Inhalts'].isin(art_des_inhalts_filter)]
    if zeitraum_der_daten_filter:
        filtered_df = filtered_df[filtered_df['Zeitraum der Daten '].isin(zeitraum_der_daten_filter)]
    if aktualisierung_der_daten_filter:
        filtered_df = filtered_df[filtered_df['Aktualisierung der Daten '].isin(aktualisierung_der_daten_filter)]
    if kategorie_1_filter:
        filtered_df = filtered_df[filtered_df['Kategorie 1'].isin(kategorie_1_filter)]
    if kategorie_2_filter:
        filtered_df = filtered_df[filtered_df['Kategorie 2'].isin(kategorie_2_filter)]
    if kategorie_3_filter:
        filtered_df = filtered_df[filtered_df['Kategorie 3'].isin(kategorie_3_filter)]
    if sammlung_im_katalog_filter:
        filtered_df = filtered_df[filtered_df['Sammlung im Katalog'].isin(sammlung_im_katalog_filter)]

    with main_panel:
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
