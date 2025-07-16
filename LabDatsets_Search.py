import streamlit as st
import pandas as pd
import os
import io

st.set_page_config(page_title='Klick-Test neuer DNB Katalog')

st.markdown("# Klick-Test neuer DNB Katalog")

# Alter
st.subheader("Wie alt bist Du?")
alter = st.number_input("Wie alt bist Du?", min_value=0, max_value=120, key="alter")

# Kenntnis DNB
st.subheader("Kennst Du die Deutsche Nationalbibliothek (DNB)?")
dnb_kenntnis = st.slider("Antwort 0 bis 5 (0 = gar nicht, 5 = sehr gut)", 0, 5, 3, key="dnb_kenntnis")

# Nutzung Katalog
st.subheader("Hast Du schon mal im Katalog der DNB auf [portal.dnb.de](https://portal.dnb.de) recherchiert?")
dnb_katalog_nutzung = st.slider("Antwort 0 bis 5 (0 = nie, 5 = sehr oft)", 0, 5, 0, key="dnb_katalog_nutzung")

# Mit welchem Gerät testest Du?
st.subheader("Mit welchem Gerät testest Du?")
geraet = st.radio(
    "Bitte wähle Dein Testgerät aus:",
    ("Desktop", "Laptop", "Tablet", "Smartphone"),
    key="geraet"
)

# Test wiederholt?
st.subheader("Führst Du den Test wiederholt mit einem anderen Gerät durch?")
wiederholung = st.radio(
    "",  # Kein zusätzliches Label
    ("Ja", "Nein"),
    key="wiederholung",
    index=1   # Standardmäßig "Nein" (=Index 1)
)

# Testbeschreibung
st.title("Testbeschreibung")
st.write("""
Im Folgenden möchten wir wissen, wie Du den neuen Katalog der DNB wahrnimmst und welche Erfahrungen Du bei bestimmten Aufgaben machst. Bitte beschreibe Deine Klickwege, Gedanken und gib uns Feedback zu den einzelnen Schritten.
Starte den Test mit dieser Beispielseite eines Datensatzes im neuen Katalog (das Hinweisfenster bitte über das X einfach schließen):
[https://preview-dnbportal.dnb.de.test/static/katalogsuche-detailansicht-erste-seite.html](https://preview-dnbportal.dnb.de.test/static/katalogsuche-detailansicht-erste-seite.html)
Deine Antworten helfen uns, die Benutzungsführung zu verbessern. Vielen Dank für Deine Unterstützung!
""")

# 1. Testaufgabe: Online-Ausgabe aufrufen
st.subheader("1. Testaufgabe: Du bist zuhause und möchtest die Online-Ausgabe aufrufen.")
st.write("Wie gehst Du vor?")
klickpfad_digital_a = st.text_area("a) Beschreibe Deinen genauen Weg zum Ziel:", key="klickpfad_digital_a")
gedanken_digital_b = st.text_area("b) Beschreibe Deine Gedanken bei Deinem Vorgehen:", key="gedanken_digital_b")
zufriedenheit_digital_c = st.radio("c) Bist Du zufrieden mit der Benutzungsführung?", ("Ja", "Nein", "Teils"), key="zufriedenheit_digital_c")
aenderung_digital_d = st.text_area("d) Was würdest Du anders machen/erwarten?", key="aenderung_digital_d")

# 2. Testaufgabe: Medium als Buch einsehen
st.subheader("2. Testaufgabe: Du wohnst in Berlin und möchtest das gleiche Medium nun als Buch einsehen.")
st.write("Wie gehst Du vor?")
klickpfad_physisch_a = st.text_area("a) Beschreibe Deinen genauen Weg zum Ziel:", key="klickpfad_physisch_a")
gedanken_physisch_b = st.text_area("b) Beschreibe Deine Gedanken bei Deinem Vorgehen:", key="gedanken_physisch_b")
zufriedenheit_physisch_c = st.radio("c) Bist Du zufrieden mit der Benutzungsführung?", ("Ja", "Nein", "Teils"), key="zufriedenheit_physisch_c")
aenderung_physisch_d = st.text_area("d) Was würdest Du anders machen/erwarten?", key="aenderung_physisch_d")

# 3. Testaufgabe: Buch in Frankfurt einsehen
st.subheader("3. Testaufgabe: Kannst Du das Buch in Frankfurt einsehen?")
st.write("Wie gehst Du vor?")
klickpfad_frankfurt_a = st.text_area("a) Beschreibe Deinen genauen Weg zum Ziel:", key="klickpfad_frankfurt_a")
gedanken_frankfurt_b = st.text_area("b) Beschreibe Deine Gedanken bei Deinem Vorgehen:", key="gedanken_frankfurt_b")
zufriedenheit_frankfurt_c = st.radio("c) Bist Du zufrieden mit der Benutzungsführung?", ("Ja", "Nein", "Teils"), key="zufriedenheit_frankfurt_c")
aenderung_frankfurt_d = st.text_area("d) Was würdest Du anders machen/erwarten?", key="aenderung_frankfurt_d")

if st.button("Absenden"):
    data = {
        "Alter": alter,
        "DNB Kenntnis": dnb_kenntnis,
        "DNB Katalog Nutzung": dnb_katalog_nutzung,
        "Testgerät": geraet,
        "Mehrfachtest": wiederholung,  # <- neue Spalte
        # Digital
        "Klickpfad Digital": klickpfad_digital_a,
        "Gedanken Digital": gedanken_digital_b,
        "Zufriedenheit Digital": zufriedenheit_digital_c,
        "Aenderung Digital": aenderung_digital_d,
        # Physisch
        "Klickpfad Physisch": klickpfad_physisch_a,
        "Gedanken Physisch": gedanken_physisch_b,
        "Zufriedenheit Physisch": zufriedenheit_physisch_c,
        "Aenderung Physisch": aenderung_physisch_d,
        # Frankfurt
        "Klickpfad Frankfurt": klickpfad_frankfurt_a,
        "Gedanken Frankfurt": gedanken_frankfurt_b,
        "Zufriedenheit Frankfurt": zufriedenheit_frankfurt_c,
        "Aenderung Frankfurt": aenderung_frankfurt_d,
    }
    df = pd.DataFrame([data])
    if os.path.exists("dnb_umfrage.csv"):
        existing_data = pd.read_csv("dnb_umfrage.csv")
        df = pd.concat([existing_data, df], ignore_index=True)
    df.to_csv("dnb_umfrage.csv", index=False, encoding="utf-8")
    st.success("Daten erfolgreich gespeichert!")

def group_percent(df, group_col, value_col):
    """Gibt eine Kreuztabelle mit Prozentverteilung der Zufriedenheit je Gruppierung zurück"""
    ctab = pd.crosstab(df[group_col], df[value_col], normalize='index') * 100
    ctab = ctab.round(1).astype(str) + '%'
    return ctab

with st.expander("Admin: Daten löschen und Download"):
    delete_password = st.text_input("Passwort:", type="password")
    if delete_password == "dnb":
        if os.path.exists("dnb_umfrage.csv"):
            df = pd.read_csv("dnb_umfrage.csv")
            # Altersgruppen bilden
            bins = [0, 19, 29, 39, 49, 59, 69, 120]
            labels = ['<20', '20-29', '30-39', '40-49', '50-59', '60-69', '70+']
            df['Altersgruppe'] = pd.cut(df['Alter'], bins=bins, labels=labels, right=True, include_lowest=True)
            # Zufriedenheiten
            zuf_cols = [
                ("Zufriedenheit Digital", "Aufgabe 1"),
                ("Zufriedenheit Physisch", "Aufgabe 2"),
                ("Zufriedenheit Frankfurt", "Aufgabe 3"),
            ]
            # Auswertungen
            auswertungen = [
                ("Zufriedenheit nach Altersgruppe", 'Altersgruppe'),
                ("Zufriedenheit nach Testgerät", 'Testgerät'),
                ("Zufriedenheit nach DNB Kenntnis", 'DNB Kenntnis'),
                ("Zufriedenheit nach Katalog Nutzung", 'DNB Katalog Nutzung'),
            ]
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                # Rohdaten
                df.to_excel(writer, index=False, sheet_name="Antworten")
                # Für jede Auswertung und Aufgabe ein Tab
                for auswertung_name, group_col in auswertungen:
                    for zuf_col, aufgabe in zuf_cols:
                        tab_name = f"{aufgabe} ({auswertung_name.split()[-1]})"
                        ctab = group_percent(df, group_col, zuf_col)
                        sheet_name = tab_name[:31]
                        ctab.to_excel(writer, sheet_name=sheet_name)
            excel_buffer.seek(0)
            st.download_button(
                label="Excel-Tabelle herunterladen",
                data=excel_buffer,
                file_name="dnb_umfrage_auswertung.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            if st.button("Daten wirklich löschen"):
                try:
                    os.remove("dnb_umfrage.csv")
                    st.success("Daten erfolgreich gelöscht!")
                except FileNotFoundError:
                    st.warning("Keine Daten zum Löschen gefunden.")
        else:
            st.info("Noch keine Daten zum Download vorhanden.")
    else:
        st.warning("Bitte gültiges Passwort eingeben, um Daten einzusehen oder zu löschen.")
