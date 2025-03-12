import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import io

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
    
    # Daten laden
    if 'original_df' not in st.session_state:
        df = load_data()
        if df is None:
            st.stop()
        st.session_state.original_df = df
    else:
        df = st.session_state.original_df

    # Session State für Filter initialisieren
    filter_keys = [
        'datensetname', 'zeitraum', 'aktualisierung',
        'datenformat', 'digitale_objekte', 'online_frei',
        'download_größe', 'schnittstelle'
    ]
    for key in filter_keys:
        if key not in st.session_state:
            st.session_state[key] = []

    # Filterbereich
    st.header("Suchfilter")
    
    # Erste Filterzeile
    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state.datensetname = st.multiselect(
            "Datensetname",
            options=df['Datensetname'].dropna().unique(),
            default=st.session_state.datensetname
        )
    with col2:
        st.session_state.zeitraum = st.multiselect(
            "Zeitraum der Daten",
            options=df['Zeitraum der Daten '].dropna().unique(),
            default=st.session_state.zeitraum
        )
    with col3:
        st.session_state.aktualisierung = st.multiselect(
            "Aktualisierung der Daten",
            options=df['Aktualisierung der Daten '].dropna().unique(),
            default=st.session_state.aktualisierung
        )

    # Zweite Filterzeile
    col4, col5, col6 = st.columns(3)
    with col4:
        st.session_state.datenformat = st.multiselect(
            "Datenformat",
            options=df['Datenformat'].dropna().unique(),
            default=st.session_state.datenformat
        )
    with col5:
        st.session_state.digitale_objekte = st.multiselect(
            "Digitale Objekte",
            options=df['Digitale Objekte '].dropna().unique(),
            default=st.session_state.digitale_objekte
        )
    with col6:
        st.session_state.online_frei = st.multiselect(
            "Online frei verfügbar",
            options=df['Online frei verfügbar'].dropna().unique(),
            default=st.session_state.online_frei
        )

    # Dritte Filterzeile
    col7, col8, _ = st.columns(3)
    with col7:
        st.session_state.download_größe = st.multiselect(
            "Download Größe (GB)",
            options=df['Download Größe (GB)'].dropna().unique(),
            default=st.session_state.download_größe
        )
    with col8:
        st.session_state.schnittstelle = st.multiselect(
            "Schnittstelle",
            options=df['Schnittstelle'].dropna().unique(),
            default=st.session_state.schnittstelle
        )

    # Apply-Button
    apply_filter = st.button("Übernehmen")

    # Freitextsuche unterhalb des Buttons
    beschreibung_suchbegriff = st.text_input("Suche in Datensetbeschreibung")

    # Filterung nur bei Button-Klick oder Suchbegriff-Änderung
    filtered_df = df.copy()
    
    if apply_filter or beschreibung_suchbegriff:
        filter_conditions = {
            'Datensetname': st.session_state.datensetname,
            'Zeitraum der Daten ': st.session_state.zeitraum,
            'Aktualisierung der Daten ': st.session_state.aktualisierung,
            'Datenformat': st.session_state.datenformat,
            'Digitale Objekte ': st.session_state.digitale_objekte,
            'Online frei verfügbar': st.session_state.online_frei,
            'Download Größe (GB)': st.session_state.download_größe,
            'Schnittstelle': st.session_state.schnittstelle
        }

        for column, values in filter_conditions.items():
            if values:
                filtered_df = filtered_df[filtered_df[column].isin(values)]

        if beschreibung_suchbegriff:
            filtered_df = filtered_df[filtered_df['Beschreibung'].str.contains(
                beschreibung_suchbegriff, case=False, na=False
            )]

    # Ergebnisse anzeigen
    st.header("Suchergebnisse")
    st.write(f"Anzahl Ergebnisse: {len(filtered_df)}")
    st.dataframe(filtered_df, use_container_width=True)

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
