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
        df.columns = df.columns.str.strip()  # Spaltennamen bereinigen
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

def extract_unique_multiselect_options(series):
    """Extrahiert alle einzigartigen Werte aus einer kommagetrennten Series."""
    unique_values = set()
    for entry in series.dropna():
        for value in str(entry).split(','):
            unique_values.add(value.strip())
    return sorted(unique_values)

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

    # Spaltennamen dynamisch finden
    col_names = {col.lower(): col for col in df.columns}
    # Kategorie-Spalten dynamisch suchen
    kategorie_spalten = [col for col in df.columns if col.lower().startswith('kategorie')]

    # Eindeutige Werte für Kategorie
    kategorie_werte = set()
    for col in kategorie_spalten:
        kategorie_werte.update(df[col].dropna().unique())
    kategorie_werte = sorted([str(x) for x in kategorie_werte if str(x).strip() != ''])

    # Für kommagetrennte Spalten
    dateiformat_spalte = next((col for col in df.columns if 'dateiformat' in col.lower()), None)
    volltext_spalte = next((col for col in df.columns if 'volltext' in col.lower()), None)

    dateiformat_werte = extract_unique_multiselect_options(df[dateiformat_spalte]) if dateiformat_spalte else []
    volltext_werte = extract_unique_multiselect_options(df[volltext_spalte]) if volltext_spalte else []

    # Session State für Filter initialisieren
    filter_keys = [
        'datensetname', 'kategorie', 'zeitraum',
        'metadatenformat', 'bezugsweg', 'dateiformat', 'volltext'
    ]
    for key in filter_keys:
        if key not in st.session_state:
            st.session_state[key] = []

    # Filterbereich
    st.header("Suchfilter")
    with st.container():
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            dsname_col = next((col for col in df.columns if 'datensetname' in col.lower()), None)
            st.session_state.datensetname = st.multiselect(
                "Datensetname",
                options=sorted(df[dsname_col].dropna().unique()) if dsname_col else [],
                default=st.session_state.datensetname
            )
        with col2:
            st.session_state.kategorie = st.multiselect(
                "Kategorie",
                options=kategorie_werte,
                default=st.session_state.kategorie
            )
        with col3:
            zeitraum_col = next((col for col in df.columns if 'zeitraum' in col.lower()), None)
            st.session_state.zeitraum = st.multiselect(
                "Zeitraum der Daten",
                options=sorted(df[zeitraum_col].dropna().unique()) if zeitraum_col else [],
                default=st.session_state.zeitraum
            )
        with col4:
            meta_col = next((col for col in df.columns if 'metadatenformat' in col.lower()), None)
            st.session_state.metadatenformat = st.multiselect(
                "Metadatenformat",
                options=sorted(df[meta_col].dropna().unique()) if meta_col else [],
                default=st.session_state.metadatenformat
            )
        with col5:
            bezugsweg_col = next((col for col in df.columns if 'bezugsweg' in col.lower()), None)
            st.session_state.bezugsweg = st.multiselect(
                "Bezugsweg",
                options=sorted(df[bezugsweg_col].dropna().unique()) if bezugsweg_col else [],
                default=st.session_state.bezugsweg
            )

    # Zweite Filterzeile für Dateiformat und Volltext-Verfügbarkeit
    col6, col7 = st.columns(2)
    with col6:
        st.session_state.dateiformat = st.multiselect(
            "Dateiformat",
            options=dateiformat_werte,
            default=st.session_state.dateiformat
        )
    with col7:
        st.session_state.volltext = st.multiselect(
            "Volltext-Verfügbarkeit",
            options=volltext_werte,
            default=st.session_state.volltext
        )

    # Apply-Button
    apply_filter = st.button("Übernehmen")

    # Freitextsuche unterhalb des Buttons
    beschreibung_col = next((col for col in df.columns if 'beschreibung' in col.lower()), None)
    beschreibung_suchbegriff = st.text_input("Suche in Datensetbeschreibung")

    # Filterung
    filtered_df = df.copy()
    if apply_filter or beschreibung_suchbegriff:
        # Kategorie-Filter (über alle Kategorie-Spalten)
        if st.session_state.kategorie:
            mask = filtered_df[kategorie_spalten].isin(st.session_state.kategorie).any(axis=1)
            filtered_df = filtered_df[mask]

        # Datensetname
        if st.session_state.datensetname and dsname_col:
            filtered_df = filtered_df[filtered_df[dsname_col].isin(st.session_state.datensetname)]
        # Zeitraum
        if st.session_state.zeitraum and zeitraum_col:
            filtered_df = filtered_df[filtered_df[zeitraum_col].isin(st.session_state.zeitraum)]
        # Metadatenformat
        if st.session_state.metadatenformat and meta_col:
            filtered_df = filtered_df[filtered_df[meta_col].isin(st.session_state.metadatenformat)]
        # Bezugsweg
        if st.session_state.bezugsweg and bezugsweg_col:
            filtered_df = filtered_df[filtered_df[bezugsweg_col].isin(st.session_state.bezugsweg)]

        # Dateiformat (kommagetrennte Inhalte)
        if st.session_state.dateiformat and dateiformat_spalte:
            mask = filtered_df[dateiformat_spalte].dropna().apply(
                lambda x: any(fmt.strip() in st.session_state.dateiformat for fmt in str(x).split(','))
            )
            filtered_df = filtered_df[mask]
        # Volltext-Verfügbarkeit (kommagetrennte Inhalte)
        if st.session_state.volltext and volltext_spalte:
            mask = filtered_df[volltext_spalte].dropna().apply(
                lambda x: any(vt.strip() in st.session_state.volltext for vt in str(x).split(','))
            )
            filtered_df = filtered_df[mask]

        # Freitextsuche in Beschreibung
        if beschreibung_suchbegriff and beschreibung_col:
            filtered_df = filtered_df[filtered_df[beschreibung_col].str.contains(
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
