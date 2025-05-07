import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from dotenv import load_dotenv
load_dotenv()

import openai
import locale
from io import BytesIO
import datetime


from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    project=os.getenv("OPENAI_PROJECT_ID")
)




def tel_gebruik():
    bestand = 'slikky_log.csv'
    bestaat = os.path.isfile(bestand)
    tijdstip = datetime.datetime.now().strftime("%Y-%m-%d,%H:%M:%S")

    if bestaat:
        with open(bestand, 'r') as file:
            regels = file.readlines()
            gebruik_id = len(regels)
    else:
        gebruik_id = 1

    with open(bestand, 'a') as file:
        if not bestaat:
            file.write('Datum,Tijd,Gebruik_ID,Advies_Type\n')  # header
        file.write(f"{tijdstip.split(',')[0]},{tijdstip.split(',')[1]},{gebruik_id},Premium\n")




from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Image
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle

# Zet de Nederlandse tijdnotatie
try:
    locale.setlocale(locale.LC_TIME, 'nl_NL.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_TIME, '')

# ✅ Zet de OpenAI API key via Streamlit secrets
#openai.api_key = st.secrets["openai"]["api_key"]
if st.session_state.get("reset", False):
    st.session_state.update({
        "gender": "Dhr.",
        "naam": "",
        "geboortedatum": datetime.date(2000, 1, 1),
        "zorgorganisatie": "",
        "locatie": "",
        "advies_datum": datetime.date.today(),
        "geldigheid": "4 weken",
        "geldigheid_datum": datetime.date.today(),
        "auteur": "",
        "functie": "",
        "advies": "",
        "toezicht": None,
        "allergieën": "",
        "voorkeuren": "",
        "reset": False
    })
    st.rerun()

st.image("images/logo_slikky.png", width=150)
st.markdown("### Voedingsadvies bij slikproblemen")
st.write("Voer het logopedisch advies in, geef IDDSI-niveaus en specifieke voorkeuren op.")

st.subheader("🔒 Cliëntgegevens (worden niet opgeslagen)")
col1, col2, col3 = st.columns([1, 3, 2])
client_gender = col1.selectbox("Aanhef:", ["Dhr.", "Mevr.", "X"], key="gender")
client_naam = col2.text_input("Naam van de cliënt:", key="naam")
client_geboortedatum = col3.date_input("Geboortedatum:", format="DD/MM/YYYY", min_value=datetime.date(1933, 1, 1), max_value=datetime.date.today(), key="geboortedatum")

col_org1, col_org2 = st.columns([2, 2])
zorgorganisatie = col_org1.text_input("Zorgorganisatie:", key="zorgorganisatie")
locatie = col_org2.text_input("Locatie:", key="locatie")

col4, col5 = st.columns([2, 2])
advice_datum = col4.date_input("Datum aanmaak voedingsadvies:", format="DD/MM/YYYY", key="advies_datum")
geldigheid_optie = col5.selectbox("Geldig voor:", ["4 weken", "6 weken", "8 weken", "Anders"], key="geldigheid")

if geldigheid_optie == "Anders":
    col6, _ = st.columns([2, 2])
    geldigheid_datum = col6.date_input("Kies einddatum:", format="DD/MM/YYYY", key="geldigheid_datum")
else:
    geldigheid_datum = None

col_creator1, col_creator2 = st.columns([2, 2])
aangemaakt_door = col_creator1.text_input("Aangemaakt door:", key="auteur")
functie = col_creator2.text_input("Functie:", key="functie")

advies = st.text_area("📄 Logopedisch advies:", key="advies")
onder_toezicht_optie = st.radio(
    "🚨 Moet de cliënt eten onder toezicht?",
    options=["Ja", "Nee"],
    index=None,
    key="toezicht",
    help="Selecteer een van beide opties om verder te gaan."
)

if onder_toezicht_optie == "Ja":
    hulp_bij_eten_optie = st.radio(
        "👐 Moet de cliënt geholpen worden met eten?",
        options=["Ja", "Nee"],
        index=None,
        key="hulp_bij_eten_radio",
        help="Selecteer een van beide opties om verder te gaan."
    )
else:
    hulp_bij_eten_optie = None

st.write("---")
st.write("👇 Kies de gewenste consistentieniveaus:")

iddsi_vast = st.selectbox("🍽️ Niveau voor voedsel:", [
    "Niveau 3: Dik vloeibaar",
    "Niveau 4: Glad gemalen",
    "Niveau 5: Fijngemalen en smeuïg",
    "Niveau 6: Zacht & klein gesneden",
    "Niveau 7: Normaal - makkelijk te kauwen"
], index=4, key="iddsi_vast")

iddsi_vloeibaar = st.selectbox("🥣 Niveau voor vloeistof:", [
    "Niveau 0: Dun vloeibaar",
    "Niveau 1: Licht vloeibaar",
    "Niveau 2: Matig vloeibaar",
    "Niveau 3: Dik vloeibaar",
    "Niveau 4: Zeer dik vloeibaar"
], key="iddsi_vloeibaar")

allergieën = st.text_input("⚠️ Allergieën (optioneel, scheid met komma's):", key="allergie")
voorkeuren = st.text_input("✅ Voedselvoorkeuren (optioneel, scheid met komma's):", key="voorkeuren")

# --- Validatie op overlap tussen allergieën en voorkeuren ---
if allergieën.strip() and voorkeuren.strip():  # alleen controleren als beide velden niet leeg zijn
    allergie_lijst = [a.strip().lower() for a in allergieën.split(',')]
    voorkeur_lijst = [v.strip().lower() for v in voorkeuren.split(',')]
    overlap = set(allergie_lijst) & set(voorkeur_lijst)
    if overlap:
        overlappende_term = ', '.join(overlap)
        st.error(f"⚠️ Let op: het volgende komt zowel voor bij allergieën als bij voorkeuren: {overlappende_term}. Pas je invoer aan.")
        st.stop()

st.write("### 🔍 Voedingsmiddelenfilter (optioneel)")

# Groep 1: Allergieën & intoleranties
toon_allergie_filter = st.checkbox("Sluit de volgende *intoleranties of allergenen* uit:")

uitsluitingen = []

if toon_allergie_filter:
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.checkbox("Amandelen"): uitsluitingen.append("amandelen")
        if st.checkbox("Gluten"): uitsluitingen.append("gluten")
        if st.checkbox("Koemelk"): uitsluitingen.append("koemelk")
        if st.checkbox("Kippenei"): uitsluitingen.append("kippenei")
        if st.checkbox("Lactose"): uitsluitingen.append("lactose")
    with col2:
        if st.checkbox("Lupine"): uitsluitingen.append("lupine")
        if st.checkbox("Mosterd"): uitsluitingen.append("mosterd")
        if st.checkbox("Noten"): uitsluitingen.append("noten")
        if st.checkbox("Pinda’s"): uitsluitingen.append("pinda’s")
        if st.checkbox("Schaal-/schelpdieren"): uitsluitingen.append("schaal-/schelpdieren")
    with col3:
        if st.checkbox("Sesamzaad"): uitsluitingen.append("sesamzaad")
        if st.checkbox("Soja"): uitsluitingen.append("soja")
        if st.checkbox("Sulfiet"): uitsluitingen.append("sulfiet")
        if st.checkbox("Tarwe"): uitsluitingen.append("tarwe")
        if st.checkbox("Vis"): uitsluitingen.append("vis")

# Groep 2: Dieet-/levensstijl gerelateerd
toon_dieet_filter = st.checkbox("Sluit de volgende *dieet- of levensstijlgerelateerde* voedingsmiddelen uit:")

if toon_dieet_filter:
    col4, col5, col6 = st.columns(3)
    with col4:
        if st.checkbox("Alcohol"): uitsluitingen.append("alcohol")
        if st.checkbox("E-nummers"): uitsluitingen.append("E-nummers")
        if st.checkbox("Kunstmatige zoetstoffen"): uitsluitingen.append("kunstmatige zoetstoffen")
    with col5:
        if st.checkbox("Rauw voedsel"): uitsluitingen.append("rauw voedsel")
        if st.checkbox("Suiker"): uitsluitingen.append("suiker")
        if st.checkbox("Vegetarisch"): uitsluitingen.append("vegetarisch")
    with col6:
        if st.checkbox("Veganistisch"): uitsluitingen.append("veganistisch")
        if st.checkbox("Varkensvlees"): uitsluitingen.append("varkensvlees")
        if st.checkbox("Zout / natrium"): uitsluitingen.append("zout/natrium")
        anders = st.text_input("Anders, namelijk:")
        if anders:
            uitsluitingen.append(anders)

uitsluit_tekst = ", ".join(uitsluitingen) if uitsluitingen else "Geen extra uitsluitingen opgegeven."
# === Toon gekozen uitsluitingen in 3 kolommen, volledig alfabetisch ===
if uitsluitingen:
    uitsluitingen = sorted(uitsluitingen, key=lambda x: x.lower())  # Volledig alfabetisch sorteren
    kolom_lengte = (len(uitsluitingen) + 2) // 3

    kolom1 = uitsluitingen[:kolom_lengte]
    kolom2 = uitsluitingen[kolom_lengte:2*kolom_lengte]
    kolom3 = uitsluitingen[2*kolom_lengte:]

    def maak_lijst(kolom):
        if kolom:
            return "<ul>" + "".join(f"<li>{item.capitalize()}</li>" for item in kolom) + "</ul>"
        else:
            return ""

    st.markdown(
        f"""
        <div style="background-color: #e6f4ea; padding: 20px; border-radius: 10px;
                    animation: fadeIn 0.5s ease-in;">
            <h4 style="color: #1a7f37;">Geselecteerde uitsluitingen:</h4>
            <div style="display: flex;">
                <div style="flex: 1;">{maak_lijst(kolom1)}</div>
                <div style="flex: 1;">{maak_lijst(kolom2)}</div>
                <div style="flex: 1;">{maak_lijst(kolom3)}</div>
            </div>
        </div>
        <style>
        @keyframes fadeIn {{
            0% {{ opacity: 0; }}
            100% {{ opacity: 1; }}
        }}
        </style>
        <div style="margin-bottom: 30px;"></div>
        """,
        unsafe_allow_html=True
    )


# === Alleen als de knop is ingedrukt, voer de rest uit ===
if st.button("🎯 Genereer Voedingsprogramma"):

    if not advies:
        st.warning("⚠️ Voer eerst een logopedisch advies in.")
    elif onder_toezicht_optie not in ["Ja", "Nee"]:
        st.warning("⚠️ Kies of de cliënt onder toezicht moet eten.")
    elif onder_toezicht_optie == "Ja" and hulp_bij_eten_optie not in ["Ja", "Nee"]:
        st.warning("⚠️ Kies of de cliënt geholpen moet worden met eten.")
    else:
        st.success("✅ Alles correct ingevuld. Hier komt je advies...")
        toezicht_tekst = "De cliënt moet eten onder toezicht." if onder_toezicht_optie == "Ja" else ""
        hulp_tekst = "De cliënt moet geholpen worden met eten." if hulp_bij_eten_optie == "Ja" else ""
        advies_datum = st.session_state["advies_datum"]
        geldigheid_tekst = geldigheid_datum.strftime('%d/%m/%Y') if geldigheid_datum else f"{geldigheid_optie} vanaf {advies_datum.strftime('%d/%m/%Y')}"
        uitsluit_tekst = ", ".join(uitsluitingen) if uitsluitingen else "Geen extra uitsluitingen opgegeven."

        golden_prompt = f"""Je bent een AI-diëtist die voedingsprogramma's opstelt op basis van logopedisch advies. Je houdt strikt rekening met de vermelde IDDSI-niveaus, allergieën, voorkeuren en eventuele voedselbeperkingen.

Toon deze regels vetgedrukt bovenaan het advies:
**Dit voedingsadvies is bedoeld voor {client_gender} {client_naam} ({client_geboortedatum}).**
**Geldig tot: {geldigheid_tekst}**
**Zorgorganisatie: {zorgorganisatie} | Locatie: {locatie}**
**Aangemaakt door: {aangemaakt_door} ({functie})**

**1. Logopedisch advies**  
Herhaal beknopt het ingevoerde advies.

**2. Vertaling naar voedingsplan**  
Leg in 2-4 zinnen uit hoe je dit advies vertaalt naar een passend voedingsplan op basis van IDDSI.

**3. Belangrijke gegevens**  
- IDDSI niveau voedsel: {iddsi_vast}  
- IDDSI niveau vloeistof: {iddsi_vloeibaar}  
- Uitsluitingen: {uitsluit_tekst}  
- Allergieën: {allergieën}  
- Voorkeuren: {voorkeuren}  
- {toezicht_tekst}  
- {hulp_tekst}

**4. Concreet voedingsprogramma**  
- Geef exact 3 tot 5 aanbevolen voedingsmiddelen per categorie. Noem er nooit meer dan 5:  
  - *Vast voedsel*: bijvoorbeeld aardappel, vlees, groenten  
  - *Vloeibaar voedsel*: bijvoorbeeld soep, vla, dranken  
- Geef maximaal 5 voedingsmiddelen die moeten worden vermeden, met toelichting (bv. "ivm allergie" of "ivm verhoogde slikrisico’s")  
- Geef een realistisch voorbeeld dagmenu (ontbijt, lunch, diner, tussendoor), met 1 voorstel per maaltijdmoment, afgestemd op het IDDSI-niveau  
- Geef maximaal 5 alternatieven op basis van opgegeven voorkeuren of allergieën

Je doel is om veilige, praktische en gevarieerde suggesties te geven die volledig voldoen aan de opgegeven IDDSI-niveaus voor vast en vloeibaar voedsel.

Belangrijke instructies:
- Houd je strikt aan bestaande, veilige voedingsmiddelen die passen bij het opgegeven IDDSI-niveau.
- Structureer je antwoord altijd in twee secties: één voor vast voedsel, één voor vloeibaar voedsel.
- Geef per sectie maximaal 5 duidelijke suggesties in korte, heldere bulletpoints.
- Zorg dat de suggesties gevarieerd, realistisch en haalbaar zijn (geen exotische of moeilijk verkrijgbare producten).
- Als er allergieën zijn opgegeven (zoals noten, gluten of koemelk), **moet je strikt alle voedingsmiddelen uitsluiten die deze stoffen bevatten of kunnen bevatten**.  
  Bijvoorbeeld:  
  - Bij **koemelkallergie**: géén melk, yoghurt, vla, boter, kaas, roomijs of andere zuivelproducten.  
  - Bij **notenallergie**: géén pindakaas, notenpasta’s of producten met hazelnoot, amandel of walnoot.  
  Geef uitsluitend **volwaardige en veilige alternatieven** die géén sporen bevatten van het opgegeven allergeen.  
  Vermijd twijfelgevallen of samengestelde producten waarvan de samenstelling niet zeker is.
- Bied bij elke allergie of intolerantie minimaal twee geschikte alternatieve voedingsopties aan.
- Vermijd dubbele of herhaalde adviezen binnen dezelfde sectie.
- Als hetzelfde voedingsmiddel zowel als *allergie* als als *voorkeur* is opgegeven, meld dan:
  *Let op: het opgegeven voedingsmiddel staat zowel bij allergieën als bij voorkeuren. Wijzig de invoer om verder te gaan.*
  Geef in dat geval géén voedingsadvies.
- Sluit het advies af met een korte, vriendelijke en bemoedigende zin voor het zorgteam.
- Geef daaronder **altijd** als laatste regel, losstaand onderaan het document:  
  *Bij twijfel over veiligheid of toepassing: raadpleeg een logopedist of diëtist.*

Focuspunten:
- Veiligheid, toepasbaarheid en duidelijkheid zijn belangrijker dan creativiteit.
- Schrijf beknopt en begrijpelijk, afgestemd op gebruik door zorgprofessionals en het cliëntdossier.
- Houd je strikt aan de gevraagde aantallen. Laat geen extra opties of herhalingen zien buiten de genoemde limieten.
- Antwoord altijd in de Nederlandse taal.
"""

        try:
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Je bent een AI gespecialiseerd in voedingsadvies voor cliënten met slikproblemen."},
                    {"role": "user", "content": golden_prompt}
                ]
            )
            advies_output = response.choices[0].message.content

            st.subheader("🚨 Belangrijke waarschuwing")
            if onder_toezicht_optie == "Ja":
                st.markdown(
                    '<div style="background-color:#ffcccc;padding:15px;border-radius:10px;color:#990000;font-weight:bold;">🚨 Deze persoon mag alleen eten onder toezicht!</div>',
                    unsafe_allow_html=True
                )
            if hulp_bij_eten_optie == "Ja":
                st.markdown(
                    '<div style="background-color:#ffcccc;padding:15px;border-radius:10px;color:#990000;font-weight:bold;">⚠️ Deze persoon moet geholpen worden met eten!</div>',
                    unsafe_allow_html=True
                )

            st.subheader("📋 Voedingsadvies:")
            st.markdown(advies_output)

            # PDF EXPORT
            try:
                buffer = BytesIO()
                pdf = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)

                elements = []
                styles = getSampleStyleSheet()
                styles.add(ParagraphStyle(name='Body', fontSize=11, leading=16, alignment=TA_LEFT))
                styles.add(ParagraphStyle(name='BoldBox', fontSize=12, leading=16, alignment=TA_LEFT, textColor=colors.red))
                styles.add(ParagraphStyle(name='BoldBody', fontSize=11, leading=16, alignment=TA_LEFT, fontName='Helvetica-Bold'))

                try:
                    logo = Image("images/logo_slikky.png", width=3.5*cm, height=1*cm)
                    elements.append(logo)
                except Exception as e:
                    elements.append(Paragraph("⚠️ Logo niet gevonden: " + str(e), styles['Body']))

                elements.append(Spacer(1, 12))
                elements.append(Paragraph("---", styles['Body']))
                elements.append(Paragraph("Deze app slaat géén cliëntgegevens op.", styles['Body']))
                elements.append(Paragraph("---", styles['Body']))
                elements.append(Spacer(1, 12))

                if onder_toezicht_optie == "Ja":
                    toezicht_box = Paragraph("\U0001F6A8 Deze persoon mag alleen eten onder toezicht!", styles["BoldBox"])
                    elements.append(toezicht_box)
                    elements.append(Spacer(1, 12))

                if hulp_bij_eten_optie == "Ja":
                    hulp_box = Paragraph("\u26A0\ufe0f Deze persoon moet geholpen worden met eten!", styles["BoldBox"])
                    elements.append(hulp_box)
                    elements.append(Spacer(1, 12))

                for regel in advies_output.split("\n"):
                    if regel.strip() != "":
                        if regel.strip().startswith("**") and regel.strip().endswith("**"):
                            tekst_zonder_sterren = regel.strip().strip("*")
                            elements.append(Paragraph(tekst_zonder_sterren, styles['BoldBody']))
                        else:
                            elements.append(Paragraph(regel.strip(), styles['Body']))
                        elements.append(Spacer(1, 6))

                elements.append(Spacer(1, 60))
                elements.append(Paragraph("SLIKKY is een officieel geregistreerd merk (Benelux, 2025)", styles['Body']))
                elements.append(Spacer(1, 40))

                try:
                    merkbadge = Image("images/logo_slikky.png", width=3.5*cm, height=1*cm)
                    merkbadge.hAlign = 'CENTER'
                    elements.append(merkbadge)
                except Exception as e:
                    elements.append(Paragraph("⚠️ Merkbadge niet gevonden: " + str(e), styles['Body']))

                def header_footer(canvas, doc):
                    canvas.saveState()
                    canvas.setFont('Helvetica', 9)
                    titel = f"Voedingsadvies voor {client_gender} {client_naam} ({client_geboortedatum.strftime('%d/%m/%Y')})"
                    canvas.drawString(2 * cm, A4[1] - 1.5 * cm, titel)
                    page_num = f"Pagina {doc.page}"
                    canvas.drawRightString(A4[0] - 2 * cm, 1.5 * cm, page_num)
                    canvas.restoreState()

                pdf.build(elements, onFirstPage=header_footer, onLaterPages=header_footer)
                buffer.seek(0)

                tel_gebruik()

                st.download_button(
                    label="💾 Opslaan als PDF",
                    data=buffer,
                    file_name=f"Slikky_voedingsadvies_{client_naam.strip().replace(' ', '_')}_{client_geboortedatum.strftime('%d-%m-%Y')}.pdf",
                    mime="application/pdf"
                )

            except Exception as e:
                st.error(f"❌ Er ging iets mis bij het genereren van de PDF: {e}")

        except Exception as e:
            st.error(f"❌ Er ging iets mis bij het ophalen van het advies: {e}")

# === EINDE BLOK ===

if st.button("🔁 Herstel alle velden"):
    st.session_state["reset"] = True
    st.rerun()
    
def footer():
    st.markdown("---")
    st.markdown("<sub><i>SLIKKY® Premium v2025.05.2</i></sub>", unsafe_allow_html=True)

footer()