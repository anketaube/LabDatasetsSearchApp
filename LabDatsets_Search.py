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

    # Harmonische Filter-Anordnung
    st.header("Suchfilter")
    col1, col2, col3, col4 = st.columns(4)
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

    col5, col6, col7, col8 = st.columns(4)
    with col5:
        bezugsweg_col = next((col for col in df.columns if 'bezugsweg' in col.lower()), None)
        st.session_state.bezugsweg = st.multiselect(
            "Bezugsweg",
            options=sorted(df[bezugsweg_col].dropna().unique()) if bezugsweg_col else [],
            default=st.session_state.bezugsweg
        )
    with col6:
        st.write("")  # Platzhalter
    with col7:
        st.write("")  # Platzhalter
    with col8:
        st.write("")  # Platzhalter

    # Dateiformat und Volltext-Verfügbarkeit nebeneinander als Checkbox-Gruppen
    col9, col10 = st.columns(2)
    with col9:
        st.markdown("**Dateiformat**")
        selected_dateiformate = []
        for val in dateiformat_werte:
            if st.checkbox(val, key="dateiformat_" + val, value=(val in st.session_state.dateiformat)):
                selected_dateiformate.append(val)
        st.session_state.dateiformat = selected_dateiformate

    with col10:
        st.markdown("**Volltext-Verfügbarkeit**")
        selected_volltext = []
        for val in volltext_werte:
            if st.checkbox(val, key="volltext_" + val, value=(val in st.session_state.volltext)):
                selected_volltext.append(val)
        st.session_state.volltext = selected_volltext

    # Apply-Button und Freitextsuche in einer Zeile
