import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import io

GITHUB_EXCEL_URL = "https://raw.githubusercontent.com/anketaube/LabDatasetsSearchApp/main/Datensets_Suche_Test_neu.xlsx"

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
        'datensetname', 'kategorie', 'zeitraum',
        'metadatenformat', 'bezugsweg'
    ]
    for key in filter_keys:
        if key not in st.session_state:
            st.session_state[key] = []

    # Kategorie-Spalten identifizieren
    kategorie_spalten = [col for col in df.columns if col.lower().startswith('kategorie')]

    # Eindeutige Werte aus allen Kategorie-Spalten sammeln (Duplikate entfernen)
    kategorie_werte = []
    for col in kategorie_spalten:
        kategorie_werte.extend(df[col].dropna().unique())
    kategorie_werte = list(set(kategorie_werte))

    # Filterbereich
    st.header("Suchfilter")
    with st.container():
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.session_state.datensetname = st.multiselect(
                "Datensetname",
                options=df['Datensetname'].dropna().unique(),
                default=st.session_state.datensetname
            )
        with col2:
            st.session_state.kategorie = st.multiselect(
                "Kategorie",
                options=kategorie_werte,
                default=st.session_state.kategorie
            )
        with col3:
            st.session_state.zeitraum = st.multiselect(
                "Zeitraum der Daten",
                options=df['Zeitraum der Daten'].dropna().unique(),
                default=st.session_state.zeitraum
            )
        with col4:
            st.session_state.metadatenformat = st.multiselect(
                "Metadatenformat",
                options=df['Metadatenformat'].dropna().unique(),
                default=st.session_state.metadatenformat
            )
        with col5:
            st.session_state.bezugsweg = st.multiselect(
                "Bezugsweg",
                options=df['Bezugsweg'].dropna().unique(),
                default=st.session_state.bezugsweg
            )

    # Apply-Button
    apply_filter = st.button("Übernehmen")

    # Freitextsuche unterhalb des Buttons
    beschreibung_suchbegriff = st.text_input("Suche in Datensetbeschreibung")

    # Filterung
    filtered_df = df.copy()
    if apply_filter or beschreibung_suchbegriff:
        # Kategorie-Filter (über alle Kategorie-Spalten)
        if st.session_state.kategorie:
            mask = filtered_df[kategorie_spalten].isin(st.session_state.kategorie).any(axis=1)
            filtered_df = filtered_df[mask]

        # Weitere Filter
        if st.session_state.datensetname:
            filtered_df = filtered_df[filtered_df['Datensetname'].isin(st.session_state.datensetname)]
        if st.session_state.zeitraum:
            filtered_df = filtered_df[filtered_df['Zeitraum der Daten'].isin(st.session_state.zeitraum)]
        if st.session_state.metadatenformat:
            filtered_df = filtered_df[filtered_df['Metadatenformat'].isin(st.session_state.metadatenformat)]
        if st.session_state.bezugsweg:
            filtered_df = filtered_df[filtered_df['Bezugsweg'].isin(st.session_state.bezugsweg)]

        # Freitextsuche in Beschreibung
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
