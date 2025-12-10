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
    
    # CSS für deutschen "Option auswählen" Platzhalter in Auswahlfeldern
    st.markdown(
        """
        <style>
        /* Platzhalter in Selectbox-/Multiselect-Eingaben auf Deutsch */
        div[data-baseweb="select"] span[data-baseweb="tag"] ~ div input::placeholder {
            color: #888888;
        }
        div[data-baseweb="select"] div[aria-label="select"] div div div::before {
            content: "Option auswählen";
        }
        div[role="combobox"] div div div::before {
            content: "Option auswählen";
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    cols = st.columns([1, 6])
    with cols[0]:
        st.markdown(
            """
            <div style="display: flex; align-items: center;">
                <h2 style="margin-right: 8px;">DNB Lab Datensets</h2>
                <a href="chrome-extension://oemmndcbldboiebfnladdacbdfmadadm/https://www.dnb.de/SharedDocs/Downloads/DE/Professionell/Services/downloadObjekte.pdf?__blob=publicationFile&v=4"
                   target="_blank"
                   style="text-decoration: none; color: inherit;">
                    <span style="
                        display: inline-flex;
                        justify-content: center;
                        align-items: center;
                        width: 22px;
                        height: 22px;
                        border-radius: 50%;
                        border: 1px solid #888;
                        font-size: 14px;
                        font-weight: bold;
                        line-height: 22px;
                        text-align: center;
                        cursor: pointer;"
                        title="Informationen zum Download von Objekten (öffnet in neuem Tab)">
                        i
                    </span>
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )

    with cols[1]:
        st.write("")  # kleiner Abstand

    st.markdown("Diese Anwendung ermöglicht die Filterung und Suche in DNBLab Datensets.")

    df = load_data()
    if df is None:
        return

    # Spaltennamen anpassen, falls nötig
    expected_columns = [
        "Titel", "Beschreibung", "Typ", "Format", "Sprache",
        "Lizenz", "Zeitraum", "Schlagwörter", "URL"
    ]
    for col in expected_columns:
        if col not in df.columns:
            pass

    st.sidebar.header("Filter")

    text_filter = st.sidebar.text_input(
        "Volltextsuche in allen Feldern",
        placeholder="Suchbegriff(e) eingeben …"
    )

    typ_options = extract_unique_multiselect_options(df["Typ"])
    selected_typ = st.sidebar.multiselect(
        "Datensatztyp",
        options=typ_options,
        default=[]
    )

    format_options = extract_unique_multiselect_options(df["Format"])
    selected_format = st.sidebar.multiselect(
        "Format",
        options=format_options,
        default=[]
    )

    sprache_options = extract_unique_multiselect_options(df["Sprache"])
    selected_sprache = st.sidebar.multiselect(
        "Sprache",
        options=sprache_options,
        default=[]
    )

    lizenz_options = extract_unique_multiselect_options(df["Lizenz"])
    selected_lizenz = st.sidebar.multiselect(
        "Lizenz",
        options=lizenz_options,
        default=[]
    )

    if "Zeitraum" in df.columns:
        zeitraum_options = get_zeitraum_options(df, "Zeitraum")
        selected_zeitraum = st.sidebar.multiselect(
            "Zeitraum",
            options=zeitraum_options,
            default=[]
        )
    else:
        selected_zeitraum = []

    filtered_df = df.copy()

    text_mask = robust_text_search(filtered_df, text_filter)
    filtered_df = filtered_df[text_mask]

    if selected_typ:
        filtered_df = filtered_df[
            filtered_df["Typ"].astype(str).apply(
                lambda x: any(t in [v.strip() for v in x.split(",")] for t in selected_typ)
            )
        ]

    if selected_format:
        filtered_df = filtered_df[
            filtered_df["Format"].astype(str).apply(
                lambda x: any(f in [v.strip() for v in x.split(",")] for f in selected_format)
            )
        ]

    if selected_sprache:
        filtered_df = filtered_df[
            filtered_df["Sprache"].astype(str).apply(
                lambda x: any(s in [v.strip() for v in x.split(",")] for s in selected_sprache)
            )
        ]

    if selected_lizenz:
        filtered_df = filtered_df[
            filtered_df["Lizenz"].astype(str).apply(
                lambda x: any(l in [v.strip() for v in x.split(",")] for l in selected_lizenz)
            )
        ]

    if selected_zeitraum and "Zeitraum" in filtered_df.columns:
        filtered_df = filter_by_zeitraum(filtered_df, "Zeitraum", selected_zeitraum)

    st.markdown(f"**Gefundene Datensätze:** {len(filtered_df)}")

    if not filtered_df.empty:
        st.dataframe(filtered_df, use_container_width=True)

        csv_buffer = download_csv(filtered_df)
        st.download_button(
            label="Gefilterte Datensätze als CSV herunterladen",
            data=csv_buffer,
            file_name="dnb_lab_datensets_gefiltet.csv",
            mime="text/csv"
        )
    else:
        st.info("Keine Datensätze für die aktuelle Filterkombination gefunden.")

if __name__ == "__main__":
    main()
