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
    kategorie_spalten = [col for col in df.columns if col.lower().startswith('kategorie')]
    kategorie_werte = set()
    for col in kategorie_spalten:
        kategorie_werte.update(df[col].dropna().unique())
    kategorie_werte = sorted([str(x) for x in kategorie_werte if str(x).strip() != ''])

    volltext_spalte = next((col for col in df.columns if 'volltext' in col.lower()), None)
    volltext_werte = extract_unique_multiselect_options(df[volltext_spalte]) if volltext_spalte else []

    # Session State für Filter initialisieren
    filter_keys = [
        'kategorie', 'zeitraum', 'metadatenformat', 'bezugsweg', 'volltext'
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

    # Filterzeile 2: Volltext-Verfügbarkeit, Suchfeld, Button
    col5, col6, col7 = st.columns([2, 6, 1])
    with col5:
        st.markdown("**Volltext-Verfügbarkeit**")
        selected_volltext = []
        for val in volltext_werte:
            if st.checkbox(val, key="volltext_" + val, value=(val in st.session_state.volltext)):
                selected_volltext.append(val)
        st.session_state.volltext = selected_volltext

    with col6:
        suchfeld = st.text_input("Suche in allen Feldern", key="suchfeld")

    with col7:
        # Lupensymbol als Button
        suchen = st.button("🔍", key="finden_button")

    # Filterung
    filtered_df = df.copy()

    # Kategorie-Filter (über alle Kategorie-Spalten)
    if st.session_state.kategorie:
        mask = filtered_df[kategorie_spalten].isin(st.session_state.kategorie).any(axis=1)
        filtered_df = filtered_df[mask]

    # Zeitraum
    if st.session_state.zeitraum and zeitraum_col:
        filtered_df =
