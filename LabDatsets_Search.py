import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import io

GITHUB_EXCEL_URL = "https://raw.githubusercontent.com/anketaube/LabDatasetsSearchApp/main/Datensets_Filter.xlsx"

def load_data():
    try:
        response = requests.get(GITHUB_EXCEL_URL)
        response.raise_for_status()
        excel_file = BytesIO(response.content)
        df = pd.read_excel(excel_file, engine='openpyxl', sheet_name='Tabelle2')
        df = df.replace('', pd.NA)
        df.columns = df.columns.str.strip()
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
    unique_values = set()
    for entry in series.dropna():
        for value in str(entry).split(','):
            unique_values.add(value.strip())
    return sorted(unique_values)

def main():
    st.set_page_config(layout="wide")
    col1, col2 = st.columns([1, 6])

    with col1:
        st.markdown(
            """
            <div style="display: flex; align-items: center; height: 100%;">
                <img src="https://www.dnb.de/SiteGlobals/Frontend/DNBWeb/Images/logo.svg?__blob=normal&v=3" width="80" style="margin-right: 10px;">
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <h1 style="margin: 0; line-height: 80px;">DNBLab Datensetsuche</h1>
            """,
            unsafe_allow_html=True,
        )


    # Daten laden
    if 'original_df' not in st.session_state:
        df = load_data()
        if df is None:
            st.stop()
        st.session_state.original_df = df
    else:
        df = st.session_state.original_df

    # Spaltennamen dynamisch finden
    kategorie_spalten = [col for col in df.columns if col.lower().startswith('kategorie')]
    kategorie_werte = set()
    for col in kategorie_spalten:
        kategorie_werte.update(df[col].dropna().unique())
    kategorie_werte = sorted([str(x) for x in kategorie_werte if str(x).strip() != ''])

    volltext_spalte = next((col for col in df.columns if 'volltext' in col.lower()), None)
    dateiformat_spalte = next((col for col in df.columns if 'dateiformat' in col.lower()), None)

    volltext_werte = extract_unique_multiselect_options(df[volltext_spalte]) if volltext_spalte else []
    dateiformat_werte = extract_unique_multiselect_options(df[dateiformat_spalte]) if dateiformat_spalte else []

    # Session State für Filter initialisieren
    filter_keys = [
        'kategorie', 'zeitraum', 'metadatenformat', 'bezugsweg', 'volltext', 'dateiformat'
    ]
    for key in filter_keys:
        if key not in st.session_state:
            st.session_state[key] = []

    # Filterzeile 1
    st.header("Suchfilter")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.session_state.kategorie = st.multiselect(
            "Kategorie",
            options=kategorie_werte,
            default=st.session_state.kategorie
        )

    with col2:
        zeitraum_col = next((col for col in df.columns if 'zeitraum' in col.lower()), None)
        st.session_state.zeitraum = st.multiselect(
            "Zeitraum der Daten",
            options=sorted(df[zeitraum_col].dropna().unique()) if zeitraum_col else [],
            default=st.session_state.zeitraum
        )

    with col3:
        meta_col = next((col for col in df.columns if 'metadatenformat' in col.lower()), None)
        st.session_state.metadatenformat = st.multiselect(
            "Metadatenformat",
            options=sorted(df[meta_col].dropna().unique()) if meta_col else [],
            default=st.session_state.metadatenformat
        )

    with col4:
        bezugsweg_col = next((col for col in df.columns if 'bezugsweg' in col.lower()), None)
        st.session_state.bezugsweg = st.multiselect(
            "Bezugsweg",
            options=sorted(df[bezugsweg_col].dropna().unique()) if bezugsweg_col else [],
            default=st.session_state.bezugsweg
        )

    # Filterzeile 2
    col5, col6, col7, col8 = st.columns([2, 3, 4, 1])

    with col5:
        st.markdown("**Volltext-Verfügbarkeit** ℹ️", unsafe_allow_html=True)
        selected_volltext = []
        for val in volltext_werte:
            if st.checkbox(val, key="volltext_" + val, value=(val in st.session_state.volltext)):
                selected_volltext.append(val)
        st.session_state.volltext = selected_volltext

    with col6:
        st.session_state.dateiformat = st.multiselect(
            "Dateiformat der verlinkten Werke",
            options=dateiformat_werte,
            default=st.session_state.dateiformat
        )

    with col7:
        suchfeld = st.text_input("Suche in allen Feldern", key="suchfeld")

    with col8:
        suchen = st.button("🔍", key="finden_button")

    # Filterung
    filtered_df = df.copy()

    if st.session_state.kategorie:
        mask = filtered_df[kategorie_spalten].isin(st.session_state.kategorie).any(axis=1)
        filtered_df = filtered_df[mask]

    if st.session_state.zeitraum and zeitraum_col:
        filtered_df = filtered_df[filtered_df[zeitraum_col].isin(st.session_state.zeitraum)]

    if st.session_state.metadatenformat and meta_col:
        filtered_df = filtered_df[filtered_df[meta_col].isin(st.session_state.metadatenformat)]

    if st.session_state.bezugsweg and bezugsweg_col:
        filtered_df = filtered_df[filtered_df[bezugsweg_col].isin(st.session_state.bezugsweg)]

    if st.session_state.volltext and volltext_spalte:
        def all_volltext_selected(cell):
            cell_values = [v.strip() for v in str(cell).split(',')]
            return all(vt in cell_values for vt in st.session_state.volltext)
        mask = filtered_df[volltext_spalte].apply(all_volltext_selected)
        filtered_df = filtered_df[mask]

    if st.session_state.dateiformat and dateiformat_spalte:
        def has_any_format(cell):
            cell_values = [v.strip() for v in str(cell).split(',')]
            return any(fmt in cell_values for fmt in st.session_state.dateiformat)
        mask = filtered_df[dateiformat_spalte].apply(has_any_format)
        filtered_df = filtered_df[mask]

    if suchen and suchfeld:
        suchwoerter = [w.strip() for w in suchfeld.split() if w.strip()]
        for wort in suchwoerter:
            mask = filtered_df.apply(lambda row: row.astype(str).str.contains(wort, case=True, na=False).any(), axis=1)
            filtered_df = filtered_df[mask]

    # Ergebnisse anzeigen
    st.header("Suchergebnisse")
    st.write(f"Anzahl Ergebnisse: {len(filtered_df)}")
    st.dataframe(filtered_df, use_container_width=True, height=400)

    csv_file = download_csv(filtered_df)
    st.download_button(
        label="Ergebnisse als CSV herunterladen",
        data=csv_file,
        file_name="dnb_datensets.csv",
        mime="text/csv",
    )

if __name__ == "__main__":
    main()




