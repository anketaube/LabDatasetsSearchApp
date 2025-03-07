# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# 1. KORREKTE RAW-URL FESTLEGEN (Beispiel-URL - muss angepasst werden!)
# Muss genau diesem Muster folgen:
GITHUB_EXCEL_URL = "https://raw.githubusercontent.com/[DEIN_BENUTZERNAME]/[DEIN_REPO]/[BRANCH]/Datensets_Suche_Test.xlsx"

def load_data():
    try:
        # 2. URL-Überprüfung
        if not GITHUB_EXCEL_URL.startswith("https://raw.githubusercontent.com/"):
            st.error("Falsche URL-Struktur! Muss mit 'https://raw.githubusercontent.com/' beginnen")
            return None

        response = requests.get(GITHUB_EXCEL_URL)
        
        # 3. HTTP-Status prüfen
        if response.status_code != 200:
            st.error(f"Datei nicht gefunden (HTTP-Status {response.status_code})")
            return None

        # 4. Dateiheader überprüfen
        content = response.content
        if len(content) < 4:
            st.error("Leere Datei erhalten")
            return None
            
        # 5. Magic Number für Excel prüfen (50 4B 03 04 = PK.. für ZIP)
        if content[0:4] != b'\x50\x4B\x03\x04':
            st.error("Keine gültige Excel-Datei (falscher Dateiheader)")
            st.write("Erhaltene Header-Bytes:", content[0:4])
            return None

        # 6. Mit beiden Engines versuchen
        try:
            return pd.read_excel(
                BytesIO(content),
                engine='openpyxl',
                sheet_name='Tabelle2'
            )
        except:
            return pd.read_excel(
                BytesIO(content),
                engine='xlrd',
                sheet_name='Tabelle2'
            )

    except Exception as e:
        st.error(f"Technischer Fehler: {str(e)}")
        st.markdown("""
        **Fehlerbehebung:**
        1. RAW-URL direkt im Browser testen
        2. Excel-Datei lokal mit LibreOffice öffnen/speichern
        3. GitHub-Link muss exakt sein (Groß-/Kleinschreibung!)
        """)
        return None

def main():
    st.set_page_config(page_title="DNB-Datensuche", layout="wide")
    st.title("📚 Deutsche Nationalbibliothek - Datenset-Suche")
    
    # Debug-Info
    with st.expander("🔧 Technische Prüfung"):
        st.write(f"GitHub-URL: `{GITHUB_EXCEL_URL}`")
        st.write(f"Python Version: {pd.__version__}")
    
    df = load_data()
    if df is None:
        st.warning("Bitte Dateizugang prüfen und Seite neu laden")
        return

    # Restlicher Code bleibt gleich...

if __name__ == "__main__":
    main()
