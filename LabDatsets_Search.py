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
            jahres_mask = df_clean[zeitraum_col].astype(str).apply(lambda x: str(x).startswith(start_jahr))
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
        wort_mask = df.astype(str).apply(lambda row: row.str.lower().str.contains(wort, na=False, regex=False).any(), axis=1)
        mask = mask & wort_mask
    return mask

def main():
    st.set_page_config(layout="wide")
    
    cols = st.columns([1, 6])
    with cols[0]:
        st.markdown("# DNB Lab Datensets")
    
    df = load_data()
    if df is None:
        return

    # Sidebar mit deutschen Texten (Änderung 1)
    st.sidebar.header("🔍 Filter")
    
    # Freitextsuche
    suchtext = st.sidebar.text_input("Freitextsuche", placeholder="Begriffe in allen Feldern")
    
    # Zeitraum - EXAKTER Spaltenname aus Excel
    zeitraum_options = get_zeitraum_options(df, "Zeitraum der Daten")
    selected_zeitraeume = st.sidebar.multiselect(
        "Zeitraum", 
        options=zeitraum_options, 
        default=[], 
        placeholder="Zeitraum wählen"
    )
    
    # Metadatenformat - EXAKTER Spaltenname
    metadatenformat_options = extract_unique_multiselect_options(df["Metadatenformat"])
    selected_metadatenformat = st.sidebar.multiselect(
        "Metadatenformat", 
        options=metadatenformat_options, 
        default=[], 
        placeholder="Formate wählen"
    )
    
    # Bezugsweg - EXAKTER Spaltenname (Änderung 4)
    bezugsweg_options = extract_unique_multiselect_options(df["Bezugsweg"])
    selected_bezugsweg = st.sidebar.multiselect(
        "Bezugsweg", 
        options=bezugsweg_options, 
        default=[], 
        placeholder="Wege wählen"
    )
    
    # Filterlogik
    df_gefiltert = df.copy()
    
    # Freitext
    text_mask = robust_text_search(df_gefiltert, suchtext)
    df_gefiltert = df_gefiltert[text_mask]
    
    # Zeitraum
    df_gefiltert = filter_by_zeitraum(df_gefiltert, "Zeitraum der Daten", selected_zeitraeume)
    
    # Metadatenformat
    if selected_metadatenformat:
        mask_metadaten = df_gefiltert["Metadatenformat"].astype(str).apply(
            lambda x: any(opt in [v.strip() for v in str(x).split(",")] for opt in selected_metadatenformat)
        )
        df_gefiltert = df_gefiltert[mask_metadaten]
    
    # Bezugsweg
    if selected_bezugsweg:
        mask_bezugsweg = df_gefiltert["Bezugsweg"].astype(str).apply(
            lambda x: any(opt in [v.strip() for v in str(x).split(",")] for opt in selected_bezugsweg)
        )
        df_gefiltert = df_gefiltert[mask_bezugsweg]
    
    # Ergebnis (Änderungen 2+3)
    st.subheader("Gefilterte Datensätze")
    st.dataframe(df_gefiltert, use_container_width=True, height=600)
    
    st.download_button(
        "📥 CSV herunterladen", 
        data=download_csv(df_gefiltert), 
        file_name="dnblab_datensets.csv", 
        mime="text/csv"
    )

if __name__ == "__main__":
    main()
