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
        'kategorie', 'zeitraum',
        'metadatenformat', 'bezugsweg', 'volltext'
    ]
    for key in filter_keys:
        if key not in st.session_state:
            st.session_state[key] = []

    # Harmonische Filter-Anordnung
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

    col5, col6 = st.columns(2)

    with col5:
        st.write("")  # Platzhalter für Layout

    with col6:
        st.write("")  # Platzhalter für Layout

    # Dateiformat und Volltext-Verfügbarkeit nebeneinander als Checkbox-Gruppen
    col7, col8 = st.columns(2)

    with col7:
        st.markdown("**Volltext-Verfügbarkeit**")
        selected_volltext = []
        for val in volltext_werte:
            if st.checkbox(val, key="volltext_" + val, value=(val in st.session_state.volltext)):
                selected_volltext.append(val)
        st.session_state.volltext = selected_volltext

    # Apply-Button und Freitextsuche in einer Zeile
    col9, col10 = st.columns([3, 1])

    with col9:
        beschreibung_col = next((col for col in df.columns if 'beschreibung' in col.lower()), None)
        beschreibung_suchbegriff = st.text_input("Suche in Datensetbeschreibung")

    with col10:
        apply_filter = st.button("Finden")

    # Filterung
    filtered_df = df.copy()

    # Kategorie-Filter (über alle Kategorie-Spalten)
    if st.session_state.kategorie:
        mask = filtered_df[kategorie_spalten].isin(st.session_state.kategorie).any(axis=1)
        filtered_df = filtered_df[mask]

    # Zeitraum
    if st.session_state.zeitraum and zeitraum_col:
        filtered_df = filtered_df[filtered_df[zeitraum_col].isin(st.session_state.zeitraum)]

    # Metadatenformat
    if st.session_state.metadatenformat and meta_col:
        filtered_df = filtered_df[filtered_df[meta_col].isin(st.session_state.metadatenformat)]

    # Bezugsweg
    if st.session_state.bezugsweg and bezugsweg_col:
        filtered_df = filtered_df[filtered_df[bezugsweg_col].isin(st.session_state.bezugsweg)]

    # Volltext-Verfügbarkeit (kommagetrennte Inhalte, UND-Verknüpfung)
    if st.session_state.volltext and volltext_spalte:
        def all_volltext_selected(cell):
            cell_values = [v.strip() for v in str(cell).split(',')]
            return all(vt in cell_values for vt in st.session_state.volltext)
        mask = filtered_df[volltext_spalte].apply(all_volltext_selected)
        filtered_df = filtered_df[mask]

    # Freitextsuche in Beschreibung
    if apply_filter or beschreibung_suchbegriff:
        if beschreibung_suchbegriff and beschreibung_col:
            suchwoerter = [w.strip() for w in beschreibung_suchbegriff.split() if w.strip()]
            for wort in suchwoerter:
                mask = filtered_df.apply(lambda row: row.astype(str).str.contains(wort, case=True, na=False).any(), axis=1)
                filtered_df = filtered_df[mask]

    # Ergebnisse anzeigen
    st.header("Suchergebnisse")
    st.write(f"Anzahl Ergebnisse: {len(filtered_df)}")
    st.dataframe(filtered_df, use_container_width=True, height=400)

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
