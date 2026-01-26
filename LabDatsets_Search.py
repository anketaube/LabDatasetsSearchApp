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
    """CSV 100% Excel-kompatibel: Semikolon + UTF-8-BOM + Sonderzeichen bereinigt"""
    df_clean = df.copy()
    for col in df_clean.columns:
        df_clean[col] = df_clean[col].astype(str).str.replace('\u00A0', ' ', regex=False)
        df_clean[col] = df_clean[col].str.replace('\u2009', ' ', regex=False)
        df_clean[col] = df_clean[col].str.replace('\u202F', ' ', regex=False)
        df_clean[col] = df_clean[col].str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('ascii')
    
    csv = df_clean.to_csv(sep=';', index=False, encoding='utf-8-sig', na_rep='')
    b = io.BytesIO()
    b.write(csv.encode('utf-8-sig'))
    b.seek(0)
    return b.getvalue()

def extract_unique_multiselect_options(series):
    """Extrahiert einzigartige Werte aus komma-getrennten Feldern"""
    unique_values = set()
    for entry in series.dropna():
        for value in str(entry).split(','):
            unique_values.add(value.strip())
    return sorted(unique_values)

def clean_zeitraum_entry(entry):
    """Bereinigt Zeiträume aggressiv für saubere Anzeige"""
    if pd.isna(entry):
        return entry
    s = str(entry)
    s = s.replace('\u00A0', ' ').replace('\u2009', ' ').replace('\u202F', ' ')
    s = re.sub(r'[^\d\s\-\–—]', '', s)
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'[-–—]\s*', '-', s)
    s = s.strip()
    return s if s else pd.NA

def get_zeitraum_options(df, zeitraum_col):
    """Erstellt saubere Auswahl: 1913- (ab), exakte Zeiträume wie 1913-1918"""
    if not zeitraum_col:
        return []
    
    clean_zeitraeume = df[zeitraum_col].dropna().map(clean_zeitraum_entry).astype(str).unique()
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
    """Filtert '1913-' alle ab 1913, '1913-1918' exakt diesen Zeitraum"""
    if not selected_options:
        return df
    
    df_clean = df.copy()
    df_clean[zeitraum_col] = df_clean[zeitraum_col].map(clean_zeitraum_entry)
    mask = pd.Series([False] * len(df_clean))
    
    for option in selected_options:
        if option.endswith('-'):
            start_jahr = option[:-1]
            jahres_mask = df_clean[zeitraum_col].astype(str).str.startswith(start_jahr)
            mask = mask | jahres_mask
        else:
            exact_mask = df_clean[zeitraum_col].astype(str) == option
            mask = mask | exact_mask
    
    return df_clean[mask]

def robust_text_search(df, such_text):
    """Erweiterte Textsuche: case-insensitive, Teilstrings, alle Spalten"""
    if not such_text or not such_text.strip():
        return pd.Series([True] * len(df), index=df.index)
    
    such_worte = [w.strip().lower() for w in such_text.split() if w.strip()]
    mask = pd.Series([True] * len(df), index=df.index)
    
    for wort in such_worte:
        # FIX: .values für pure Boolean-Array ohne Index-Probleme
        wort_mask = df.astype(str).apply(
            lambda row: row.str.lower().str.contains(wort, na=False, regex=False).any(), 
            axis=1
        ).reindex(df.index, fill_value=False)
        mask = mask & wort_mask
    
    return mask

def main():
    st.set_page_config(layout="wide")
    
    cols = st.columns([1, 6])
    with cols[0]:
        st.markdown("""
            <div style="display: flex; align-items: center; height: 80px;">
                <img src="https://portal.dnb.de/static/bilder/logo.gif" style="height: 75px; margin-right: 5px;">
            </div>
        """, unsafe_allow_html=True)
    with cols[1]:
        st.markdown('<h1 style="margin: 0; line-height: 80px;">DNBLab Datensetsuche</h1>', unsafe_allow_html=True)
    
    # Daten laden
    if 'original_df' not in st.session_state:
        with st.spinner("Daten laden..."):
            df = load_data()
        if df is None:
            st.stop()
        st.session_state.original_df = df
    else:
        df = st.session_state.original_df
    
    # Spalten identifizieren
    kategorie_spalten = [col for col in df.columns if col.lower().startswith('kategorie')]
    zeitraum_col = next((col for col in df.columns if 'zeitraum' in col.lower()), None)
    meta_col = next((col for col in df.columns if 'metadatenformat' in col.lower()), None)
    bezugsweg_col = next((col for col in df.columns if 'bezugsweg' in col.lower()), None)
    volltext_spalte = next((col for col in df.columns if 'volltext' in col.lower()), None)
    dateiformat_spalte = next((col for col in df.columns if 'dateiformat' in col.lower()), None)
    
    # Filteroptionen vorbereiten
    kategorie_werte = sorted(set(str(x) for x in df[kategorie_spalten].stack().dropna()) if kategorie_spalten else [])
    volltext_werte = extract_unique_multiselect_options(df[volltext_spalte]) if volltext_spalte else []
    dateiformat_werte = extract_unique_multiselect_options(df[dateiformat_spalte]) if dateiformat_spalte else []
    meta_werte = extract_unique_multiselect_options(df[meta_col]) if meta_col else []
    bezugsweg_werte = extract_unique_multiselect_options(df[bezugsweg_col]) if bezugsweg_col else []
    zeitraum_options = get_zeitraum_options(df, zeitraum_col)
    
    st.header("Suchfilter")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.multiselect("Kategorie", options=kategorie_werte, key='kategorie', placeholder="Option wählen...")
    with col2:
        st.multiselect("Zeitraum der Daten", options=zeitraum_options, key='zeitraum', placeholder="Option wählen...")
    with col3:
        st.multiselect("Metadatenformat", options=meta_werte, key='metadatenformat', placeholder="Option wählen...")
    with col4:
        st.multiselect("Bezugsweg", options=bezugsweg_werte, key='bezugsweg', placeholder="Option wählen...")
    
    col5, col6, col7 = st.columns([2, 3, 7])
    with col5:
        st.markdown("**Volltext-Verfügbarkeit**")
        for val in volltext_werte:
            st.checkbox(val, key=f'volltext_{val}')
    with col6:
        st.multiselect("Dateiformat der verlinkten Werke", options=dateiformat_werte, key='dateiformat', placeholder="Option wählen...")
    with col7:
        st.text_input("Suche in allen Feldern", key='suchfeld', placeholder="Suche eingeben...")
    
    # Filter anwenden (FIX: Immer mit korrektem Index arbeiten)
    filtered_df = df.copy()
    
    # 1. Kategorie - FIX: reset_index für saubere Boolean-Masks
    selected_kat = st.session_state.get('kategorie', [])
    if selected_kat and kategorie_spalten:
        mask_kategorie = filtered_df[kategorie_spalten].astype(str).isin(selected_kat).any(axis=1)
        filtered_df = filtered_df[mask_kategorie].reset_index(drop=True)
    
    # 2. Zeitraum
    selected_zeitraum = st.session_state.get('zeitraum', [])
    if selected_zeitraum and zeitraum_col and len(filtered_df) > 0:
        zeit_df = filter_by_zeitraum(filtered_df, zeitraum_col, selected_zeitraum)
        filtered_df = filtered_df[filtered_df.index.isin(zeit_df.index)].reset_index(drop=True)
    
    # 3. Metadatenformat
    selected_meta = st.session_state.get('metadatenformat', [])
    if selected_meta and meta_col and len(filtered_df) > 0:
        def meta_match(cell):
            cell_values = [v.strip().lower() for v in str(cell).split(',')]
            return any(sel.strip().lower() in cell_values for sel in selected_meta)
        mask_meta = filtered_df[meta_col].apply(meta_match)
        filtered_df = filtered_df[mask_meta].reset_index(drop=True)
    
    # 4. Bezugsweg
    selected_bezugsweg = st.session_state.get('bezugsweg', [])
    if selected_bezugsweg and bezugsweg_col and len(filtered_df) > 0:
        def bezugsweg_match(cell):
            cell_values = [v.strip().lower() for v in str(cell).split(',')]
            return any(sel.strip().lower() in cell_values for sel in selected_bezugsweg)
        mask_bezugsweg = filtered_df[bezugsweg_col].apply(bezugsweg_match)
        filtered_df = filtered_df[mask_bezugsweg].reset_index(drop=True)
    
    # 5. Volltext
    selected_volltext = [v for v in volltext_werte if st.session_state.get(f'volltext_{v}', False)]
    if selected_volltext and volltext_spalte and len(filtered_df) > 0:
        def volltext_match(cell):
            return all(v.strip() in str(cell).split(',') for v in selected_volltext)
        mask_volltext = filtered_df[volltext_spalte].apply(volltext_match)
        filtered_df = filtered_df[mask_volltext].reset_index(drop=True)
    
    # 6. Dateiformat
    selected_dateiformat = st.session_state.get('dateiformat', [])
    if selected_dateiformat and dateiformat_spalte and len(filtered_df) > 0:
        def dateiformat_match(cell):
            cell_values = [v.strip().lower() for v in str(cell).split(',')]
            return any(sel.strip().lower() in cell_values for sel in selected_dateiformat)
        mask_dateiformat = filtered_df[dateiformat_spalte].apply(dateiformat_match)
        filtered_df = filtered_df[mask_dateiformat].reset_index(drop=True)
    
    # 7. Textsuche - FIX: Korrekte Index-Ausrichtung
    such_text = st.session_state.get('suchfeld', '').strip()
    if len(filtered_df) > 0:
        mask_suche = robust_text_search(filtered_df, such_text)
        filtered_df = filtered_df[mask_suche].reset_index(drop=True)
    
    # Ergebnisse anzeigen
    display_df = filtered_df.drop(columns=kategorie_spalten, errors='ignore')
    
    st.header("Suchergebnisse")
    st.write(f"Anzahl Ergebnisse: {len(filtered_df)}")
    
    # URL-Spalte für Links konfigurieren
    url_spalte = next((col for col in display_df.columns if 'url' in col.lower()), None)
    column_config = {}
    for col in display_df.columns:
        if col != url_spalte:
            column_config[col] = st.column_config.Column(width='medium')
    if url_spalte:
        column_config[url_spalte] = st.column_config.LinkColumn("URL", width='large', help="Auf Datensatz-Seite gehen")
    
    st.dataframe(
        display_df,
        use_container_width=True,
        height=600,
        column_config=column_config,
        hide_index=True
    )
    
    # CSV-Download (Excel-optimiert)
    csv_file = download_csv(filtered_df)
    st.download_button(
        label="📥 Ergebnisse als CSV herunterladen",
        data=csv_file,
        file_name="dnb_datensets.csv",
        mime="text/csv"
    )

if __name__ == "__main__":
    main()


