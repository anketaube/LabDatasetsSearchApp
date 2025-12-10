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
    """Extrahiert einzigartige Werte aus kommagetrennten Feldern"""
    unique_values = set()
    for entry in series.dropna():
        for value in str(entry).split(','):
            unique_values.add(value.strip())
    return sorted(unique_values)

def clean_zeitraum_entry(entry):
    """Bereinigt Zeiträume: entfernt alle Whitespaces um '-', Non-breaking spaces, etc."""
    if pd.isna(entry):
        return entry
    s = str(entry)
    s = s.replace('\u00A0', ' ').replace('\u2009', ' ').replace('\t', ' ')
    s = re.sub(r'\s*-\s*', '-', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def get_zeitraum_options(df, zeitraum_col):
    """Erstellt saubere Auswahl: 1913- (ab) + exakte Zeiträume wie 1913-1918"""
    clean_zeitraeume = df[zeitraum_col].dropna().map(clean_zeitraum_entry).unique()
    
    ab_jahre = set()
    exakte_zeitraeume = set()
    
    for z in clean_zeitraeume:
        z_str = str(z).strip()
        if z_str.endswith('-'):  
            ab_jahre.add(z_str)
        elif '-' in z_str and len(z_str.split('-')) == 2:  
            exakte_zeitraeume.add(z_str)
    
    ab_options = sorted(list(ab_jahre), key=lambda x: int(x[:-1]))
    exakt_options = sorted(list(exakte_zeitraeume), key=lambda x: int(x.split('-')[0]))
    
    return list(dict.fromkeys(ab_options + exakt_options))

def filter_by_zeitraum(df, zeitraum_col, selected_options):
    """Filtert: '1913-' = alle ab 1913, '1913-1918' = exakt diesen Zeitraum"""
    if not selected_options:
        return df
    
    df_clean = df.copy()
    df_clean[zeitraum_col] = df_clean[zeitraum_col].map(clean_zeitraum_entry)
    
    mask = pd.Series([False] * len(df_clean))
    
    for option in selected_options:
        if option.endswith('-'):  
            start_jahr = option[:-1]
            jahres_mask = df_clean[zeitraum_col].astype(str).apply(
                lambda x: str(x).startswith(start_jahr)
            )
            mask = mask | jahres_mask
        else:  
            exact_mask = df_clean[zeitraum_col].astype(str) == option
            mask = mask | exact_mask
    
    return df_clean[mask]

def robust_text_search(df, suchtext):
    """Erweiterte Textsuche: case-insensitive, Teilstrings, alle Spalten"""
    if not suchtext or not suchtext.strip():
        return pd.Series([True] * len(df))
    
    suchworte = [w.strip().lower() for w in suchtext.split() if w.strip()]
    mask = pd.Series([True] * len(df))
    
    for wort in suchworte:
        wort_mask = df.astype(str).apply(
            lambda row: row.str.lower().str.contains(wort, na=False, regex=False).any(), 
            axis=1
        )
        mask = mask & wort_mask
    
    return mask

def main():
    st.set_page_config(layout="wide")
    cols = st.columns([1, 6])

    with cols[0]:
        st.markdown(
            """
            <div style="display: flex; align-items: center; height: 80px;">
                <img src="https://portal.dnb.de/static/bilder/logo.gif" style="height: 75px; margin-right: 5px;">
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

    # Spalten identifizieren
    kategorie_spalten = [col for col in df.columns if col.lower().startswith("kategorie")]
    zeitraum_col = next((col for col in df.columns if "zeitraum" in col.lower()), None)
    meta_col = next((col for col in df.columns if "metadatenformat" in col.lower()), None)
    bezugsweg_col = next((col for col in df.columns if "bezugsweg" in col.lower()), None)
    volltext_spalte = next((col for col in df.columns if "volltext" in col.lower()), None)
    dateiformat_spalte = next((col for col in df.columns if "dateiformat" in col.lower()), None)

    # Filteroptionen vorbereiten
    kategorie_werte = sorted(set([str(x) for x in df[kategorie_spalten].stack().dropna() if str(x).strip() != ""]))
    volltext_werte = extract_unique_multiselect_options(df[volltext_spalte]) if volltext_spalte else []
    dateiformat_werte = extract_unique_multiselect_options(df[dateiformat_spalte]) if dateiformat_spalte else []
    bezugsweg_werte = extract_unique_multiselect_options(df[bezugsweg_col]) if bezugsweg_col else []
    meta_werte = extract_unique_multiselect_options(df[meta_col]) if meta_col else []
    zeitraum_options = get_zeitraum_options(df, zeitraum_col) if zeitraum_col else []

   # Filterbereich
    st.header("Suchfilter")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.multiselect("Kategorie", options=kategorie_werte, key="kategorie", placeholder="Option wählen...")

    with col2:
        st.multiselect("Zeitraum der Daten", options=zeitraum_options, key="zeitraum", placeholder="Option wählen...")

    with col3:
        st.multiselect("Metadatenformat", options=meta_werte, key="metadatenformat", placeholder="Option wählen...")  # Saubere Einzelwerte

    with col4:
        
       st.multiselect("Bezugsweg", options=bezugsweg_werte, key="bezugsweg", placeholder="Option wählen...")  # Saubere Einzelwerte)
       
    with col5:
        st.markdown("**Volltext-Verfügbarkeit** [ℹ️](https://www.dnb.de/SharedDocs/Downloads/DE/Professionell/Services/downloadObjekte.pdf?__blob=publicationFile&v=4)", unsafe_allow_html=True)
        for val in volltext_werte:
            st.checkbox(val, key=f"volltext_{val}")

    with col6:
        st.multiselect("Dateiformat der verlinkten Werke", options=dateiformat_werte, key="dateiformat", placeholder="Option wählen...")  # Saubere Einzelwerte

    with col7:
        st.text_input("Suche in allen Feldern", key="suchfeld", placeholder="Suche eingeben...")

    # **KORRIGIERTE FILTERLOGIK MIT BOOL. MASKEN**
    filtered_df = df.copy()

    # 1. Kategorie-Maske
    selected_kat = st.session_state.get("kategorie", [])
    mask_kategorie = (filtered_df[kategorie_spalten].astype(str).isin(selected_kat).any(axis=1) 
                     if selected_kat else pd.Series([True]*len(filtered_df)))

    # 2. Zeitraum-Maske
    selected_zeitraum = st.session_state.get("zeitraum", [])
    if selected_zeitraum and zeitraum_col:
        zeit_df = filter_by_zeitraum(filtered_df, zeitraum_col, selected_zeitraum)
        mask_zeitraum = filtered_df.index.isin(zeit_df.index)
    else:
        mask_zeitraum = pd.Series([True]*len(filtered_df))

    # 3. **METADATENFORMAT: OR innerhalb der Zelle (flac, MP3 → flac ODER MP3)**
    selected_meta = st.session_state.get("metadatenformat", [])
    if selected_meta and meta_col:
        def meta_match(cell):
            cell_values = [v.strip().lower() for v in str(cell).split(",")]
            return any(sel.strip().lower() in cell_values for sel in selected_meta)
        mask_metadatenformat = filtered_df[meta_col].apply(meta_match)
    else:
        mask_metadatenformat = pd.Series([True]*len(filtered_df))

    # 4. Bezugsweg-Maske
    selected_bezugsweg = st.session_state.get("bezugsweg", [])
    mask_bezugsweg = (filtered_df[bezugsweg_col].astype(str).isin(selected_bezugsweg) 
                     if selected_bezugsweg and bezugsweg_col else pd.Series([True]*len(filtered_df)))

    # 5. Volltext-Maske (ALL - UND innerhalb der Auswahl)
    selected_volltext = [v for v in volltext_werte if st.session_state.get(f"volltext_{v}")]
    if selected_volltext and volltext_spalte:
        def volltext_match(cell):
            return all(v.strip() in str(cell).split(",") for v in selected_volltext)
        mask_volltext = filtered_df[volltext_spalte].apply(volltext_match)
    else:
        mask_volltext = pd.Series([True]*len(filtered_df))

    # 6. **DATEIFORMAT: OR innerhalb der Zelle (flac, MP3 → flac ODER MP3)**
    selected_dateiformat = st.session_state.get("dateiformat", [])
    if selected_dateiformat and dateiformat_spalte:
        def dateiformat_match(cell):
            cell_values = [v.strip().lower() for v in str(cell).split(",")]
            return any(sel.strip().lower() in cell_values for sel in selected_dateiformat)
        mask_dateiformat = filtered_df[dateiformat_spalte].apply(dateiformat_match)
    else:
        mask_dateiformat = pd.Series([True]*len(filtered_df))

    # 7. TEXTSUCHE
    suchtext = st.session_state.get("suchfeld", "").strip()
    mask_suche = robust_text_search(filtered_df, suchtext)

    # **ALLE FILTER MIT UND KOMBINIEREN**
    final_mask = (mask_kategorie & mask_zeitraum & mask_metadatenformat & 
                  mask_bezugsweg & mask_volltext & mask_dateiformat & mask_suche)
    
    filtered_df = df[final_mask].copy()

    # KATEGORIE-SPALTEN AUS ANZEIGE ENTFERNEN
    display_df = filtered_df.drop(columns=kategorie_spalten, errors='ignore')

    st.header("Suchergebnisse")
    st.write(f"Anzahl Ergebnisse: {len(filtered_df)}")
    
    # DEBUG-INFO für Exil-Suche
    if suchtext.lower() == "exil":
        st.info(f"🔍 **Exil-Suche Debug:** {len(df[robust_text_search(df, 'exil')])} Treffer in Originaldaten")
    
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











