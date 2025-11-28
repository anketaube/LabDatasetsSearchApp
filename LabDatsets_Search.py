import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import io
import re

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

def parse_zeitraum_options(zeitraum_series):
    """Zeitraum-Optionen chronologisch parsen und gruppieren"""
    zeitraum_set = set()
    
    for entry in zeitraum_series.dropna():
        entry_str = str(entry).strip()
        # Regex für Zeiträume wie "1913", "1913-1918", "1913-"
        match = re.match(r'^(\d{4})(-\d{4})?(-)?$', entry_str)
        if match:
            start = int(match.group(1))
            zeitraum_set.add(entry_str)
    
    # Chronologisch sortieren
    zeitraum_list = sorted(list(zeitraum_set), key=lambda x: int(re.match(r'^(\d{4})', x).group(1)))
    
    # Gruppierte Optionen erstellen
    grouped_options = []
    current_decade = None
    
    for z in zeitraum_list:
        start_year = int(re.match(r'^(\d{4})', z).group(1))
        decade = (start_year // 10) * 10
        
        if decade != current_decade:
            grouped_options.append(f"{decade}s")
            current_decade = decade
        
        grouped_options.append(z)
    
    return grouped_options

def main():
    st.set_page_config(layout="wide")
    cols = st.columns([1, 6])

    with cols[0]:
        st.markdown(
            """
            <div style="display: flex; align-items: center; height: 80px;">
                <img src="https://www.dnb.de/SiteGlobals/Frontend/DNBWeb/Images/logo.svg?__blob=normal&v=3" style="height: 75px; margin-right: 5px;">
            </div>
            """,
            unsafe_allow_html=True,
        )

    with cols[1]:
        st.markdown(
            """
            <h1 style="margin: 0; line-height: 80px;">DNBLab Datensetsuche</h1>
            """,
            unsafe_allow_html=True,
        )

    # Daten laden
    if "original_df" not in st.session_state:
        df = load_data()
        if df is None:
            st.stop()
        st.session_state.original_df = df
    else:
        df = st.session_state.original_df

    # Kategorie-Spalten identifizieren (für Filterung, aber NICHT anzeigen)
    kategorie_spalten = [col for col in df.columns if col.lower().startswith("kategorie")]
    kategorie_werte = set()
    for col in kategorie_spalten:
        kategorie_werte.update(df[col].dropna().unique())
    kategorie_werte = sorted([str(x) for x in kategorie_werte if str(x).strip() != ""])

    volltext_spalte = next((col for col in df.columns if "volltext" in col.lower()), None)
    dateiformat_spalte = next((col for col in df.columns if "dateiformat" in col.lower()), None)

    volltext_werte = extract_unique_multiselect_options(df[volltext_spalte]) if volltext_spalte else []
    dateiformat_werte = extract_unique_multiselect_options(df[dateiformat_spalte]) if dateiformat_spalte else []

    # **ZEITRAUM CHRONOLOGISCH GESORTIERT UND GRUPPIERT**
    zeitraum_col = next((col for col in df.columns if "zeitraum" in col.lower()), None)
    zeitraum_options = parse_zeitraum_options(df[zeitraum_col]) if zeitraum_col else []

    # Filterbereich
    st.header("Suchfilter")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.multiselect(
            "Kategorie",
            options=kategorie_werte,
            key="kategorie"
        )

    with col2:
        st.multiselect(
            "Zeitraum der Daten",
            options=zeitraum_options,  # Chronologisch sortiert + gruppiert
            key="zeitraum"
        )

    with col3:
        meta_col = next((col for col in df.columns if "metadatenformat" in col.lower()), None)
        st.multiselect(
            "Metadatenformat",
            options=sorted(df[meta_col].dropna().unique()) if meta_col else [],
            key="metadatenformat"
        )

    with col4:
        bezugsweg_col = next((col for col in df.columns if "bezugsweg" in col.lower()), None)
        st.multiselect(
            "Bezugsweg",
            options=sorted(df[bezugsweg_col].dropna().unique()) if bezugsweg_col else [],
            key="bezugsweg"
        )

    col5, col6, col7 = st.columns([2, 3, 7])

    with col5:
        st.markdown(
            "**Volltext-Verfügbarkeit** "
            "[ℹ️](https://github.com/deutsche-nationalbibliothek/dnblab/blob/main/DownloadObjekte.pdf)", 
            unsafe_allow_html=True
        )
        for val in volltext_werte:
            st.checkbox(val, key=f"volltext_{val}")

    with col6:
        st.multiselect(
            "Dateiformat der verlinkten Werke",
            options=dateiformat_werte,
            key="dateiformat"
        )

    with col7:
        suchfeld = st.text_input(
            "Suche in allen Feldern",
            key="suchfeld",
            placeholder="Suche eingeben..."
        )

    # Filterlogik
    filtered_df = df.copy()

    # Kategorie (Filterung JA, Anzeige NEIN)
    selected_kat = st.session_state.get("kategorie", [])
    if selected_kat:
        mask = filtered_df[kategorie_spalten].isin(selected_kat).any(axis=1)
        filtered_df = filtered_df[mask]

    # **ZEITRAUM-FILTERUNG (exakte Matches)**
    if zeitraum_col and st.session_state.get("zeitraum"):
        selected_zeitraeume = st.session_state.zeitraum
        mask = filtered_df[zeitraum_col].astype(str).isin(selected_zeitraeume)
        filtered_df = filtered_df[mask]

    # Metadatenformat
    if meta_col and st.session_state.get("metadatenformat"):
        filtered_df = filtered_df[filtered_df[meta_col].isin(st.session_state.metadatenformat)]

    # Bezugsweg
    if bezugsweg_col and st.session_state.get("bezugsweg"):
        filtered_df = filtered_df[filtered_df[bezugsweg_col].isin(st.session_state.bezugsweg)]

    # Volltext
    selected_volltext = [v for v in volltext_werte if st.session_state.get(f"volltext_{v}")]
    if selected_volltext and volltext_spalte:
        def all_selected(cell):
            return all(v in str(cell).split(",") for v in selected_volltext)
        filtered_df = filtered_df[filtered_df[volltext_spalte].apply(all_selected)]

    # Dateiformat
    if dateiformat_spalte and st.session_state.get("dateiformat"):
        def has_any(cell):
            return any(fmt in str(cell).split(",") for fmt in st.session_state.dateiformat)
        filtered_df = filtered_df[filtered_df[dateiformat_spalte].apply(has_any)]

    # Suche bei Text-Eingabe
    if st.session_state.suchfeld and st.session_state.suchfeld.strip():
        suchworte = [w.strip() for w in st.session_state.suchfeld.split() if w.strip()]
        for wort in suchworte:
            mask = filtered_df.apply(
                lambda row: row.astype(str).str.contains(wort, case=True, na=False).any(),
                axis=1,
            )
            filtered_df = filtered_df[mask]

    # KATEGORIE-SPALTEN AUS DATAFRAME ENTFERNEN
    display_df = filtered_df.drop(columns=kategorie_spalten, errors='ignore')

    st.header("Suchergebnisse")
    st.write(f"Anzahl Ergebnisse: {len(filtered_df)}")
    
    # DATAFRAME MIT BLAUEN URL-LINKS
    url_spalte = next((col for col in display_df.columns if col.lower() == 'url'), None)
    
    column_config = {
        **{col: st.column_config.Column(width="medium") for col in display_df.columns if col != url_spalte},
    }
    
    if url_spalte:
        column_config[url_spalte] = st.column_config.LinkColumn(
            "URL",
            width="large",
            help="Auf Datensatz-Seite gehen"
        )

    st.dataframe(
        display_df, 
        use_container_width=True, 
        height=600,
        column_config=column_config,
        hide_index=True
    )

    csv_file = download_csv(filtered_df)
    st.download_button(
        label="Ergebnisse als CSV herunterladen",
        data=csv_file,
        file_name="dnb_datensets.csv",
        mime="text/csv",
    )

if __name__ == "__main__":
    main()
