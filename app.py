import streamlit as st
import requests
import xml.etree.ElementTree as ET
import anthropic
import time
import re

st.set_page_config(
    page_title="Variant Explainer",
    page_icon="🧬",
    layout="centered"
)

# ── Dark mode toggle ───────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

col_toggle1, col_toggle2 = st.columns([6, 1])
with col_toggle2:
    if st.button("🌙" if not st.session_state.dark_mode else "☀️"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

dark = st.session_state.dark_mode

# ── CSS ────────────────────────────────────────────────────
bg          = "#0E1117" if dark else "#F9FAFB"
bg2         = "#1C1C1E" if dark else "#FFFFFF"
text        = "#F0F0F0" if dark else "#0F172A"
subtext     = "#A0A0A8" if dark else "#64748B"
border      = "#2C2C2E" if dark else "#E2E8F0"
input_bg    = "#1C1C1E" if dark else "#FFFFFF"
card_shadow = "0 1px 6px rgba(0,0,0,0.18)" if dark else "0 1px 4px rgba(0,0,0,0.08)"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {{
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Inter', 'Segoe UI', sans-serif;
    background-color: {bg};
    color: {text};
}}
.main {{ background-color: {bg}; }}
.block-container {{
    padding-top: 1.5rem;
    max-width: 860px;
    margin: 0 auto;
}}

/* Hero */
.hero-title {{
    font-size: 2.4rem;
    font-weight: 700;
    color: {text};
    letter-spacing: -0.03em;
    margin-bottom: 0.6rem;
    line-height: 1.15;
}}
.hero-desc {{
    font-size: 0.97rem;
    color: {subtext};
    line-height: 1.7;
    font-weight: 400;
    max-width: 600px;
    margin-bottom: 1.8rem;
}}
.hero-divider {{
    border: none;
    border-top: 1px solid {border};
    margin: 1.5rem 0 1.8rem 0;
}}

/* Badges */
.badge-done {{
    display: inline-block;
    background: #16a34a;
    color: white;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 2px 10px;
    border-radius: 12px;
    margin-bottom: 1rem;
    letter-spacing: 0.03em;
}}
.confidence-row {{
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1.2rem;
    font-size: 0.85rem;
    color: {subtext};
}}
.dot-green {{ width:9px; height:9px; border-radius:50%; background:#16a34a; display:inline-block; }}
.dot-amber {{ width:9px; height:9px; border-radius:50%; background:#d97706; display:inline-block; }}
.dot-red   {{ width:9px; height:9px; border-radius:50%; background:#dc2626; display:inline-block; }}

/* Cards */
.card {{
    background: {bg2};
    border: 1px solid {border};
    border-radius: 14px;
    padding: 1.3rem 1.4rem 1rem 1.4rem;
    box-shadow: {card_shadow};
    height: 100%;
    position: relative;
}}
.card-green {{ border-left: 3px solid #16a34a; }}
.card-amber {{ border-left: 3px solid #d97706; }}
.card-red   {{ border-left: 3px solid #dc2626; }}

.card-role {{
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: {subtext};
    margin-bottom: 0.5rem;
}}
.card-title {{
    font-size: 1rem;
    font-weight: 600;
    color: {text};
    margin-bottom: 0.7rem;
}}
.card-body {{
    font-size: 0.91rem;
    line-height: 1.72;
    color: {"#C8C8D0" if dark else "#334155"};
    font-weight: 400;
}}
.family-line {{
    font-size: 0.82rem;
    color: {"#7878A0" if dark else "#94a3b8"};
    font-style: italic;
    margin-top: 0.8rem;
    padding-top: 0.7rem;
    border-top: 1px solid {border};
}}

/* Section label */
.section-label {{
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 0.25rem 0.7rem;
    border-radius: 20px;
    display: inline-block;
    margin-bottom: 1rem;
}}
.label-example {{ background: {"#1e3a2f" if dark else "#f0fdf4"}; color: {"#4ade80" if dark else "#16a34a"}; }}

/* Ghost button */
.ghost-btn {{
    display: inline-block;
    font-size: 0.8rem;
    color: {subtext};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 0.3rem 0.8rem;
    cursor: pointer;
    background: transparent;
    margin-bottom: 1.2rem;
    font-family: inherit;
}}

/* Input */
.stTextInput > div > div > input {{
    background-color: {input_bg} !important;
    border: 1px solid {border} !important;
    border-radius: 10px !important;
    color: {text} !important;
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Inter', sans-serif !important;
    font-size: 0.95rem !important;
    padding: 0.7rem 1rem !important;
}}
.stTextInput > div > div > input:focus {{
    border-color: #2563eb !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.12) !important;
}}

/* Selectbox */
.stSelectbox > div > div {{
    background-color: {input_bg} !important;
    border: 1px solid {border} !important;
    border-radius: 10px !important;
    color: {text} !important;
}}

/* Button */
.stButton > button {{
    background: {"#F0F0F0" if dark else "#0f172a"} !important;
    color: {"#0f172a" if dark else "#ffffff"} !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.6rem 1.4rem !important;
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    transition: opacity 0.15s !important;
}}
.stButton > button:hover {{ opacity: 0.85 !important; }}

/* Footer */
.footer-info {{
    font-size: 0.76rem;
    color: {subtext};
    text-align: center;
    margin-top: 2.5rem;
    padding-top: 1.2rem;
    border-top: 1px solid {border};
    line-height: 1.6;
}}

/* Variant found chip */
.variant-chip {{
    background: {"#1e3050" if dark else "#eff6ff"};
    border: 1px solid {"#2a4a7a" if dark else "#bfdbfe"};
    border-radius: 10px;
    padding: 0.65rem 1rem;
    color: {"#60a5fa" if dark else "#1d4ed8"};
    font-size: 0.86rem;
    margin-bottom: 1rem;
}}

#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
header {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)

# ── Keys ───────────────────────────────────────────────────
ANTHROPIC_KEY = st.secrets["ANTHROPIC_KEY"]
OMIM_KEY = st.secrets["OMIM_KEY"]

# ── Helpers ────────────────────────────────────────────────
def is_disease_name(text):
    return not any(c in text for c in ["c.", "p.", "rs", "del", "dup", "ins", ">"])

def clean_text(text):
    text = re.sub(r'#{1,6}\s?', '', text)
    text = text.replace("---", "").replace("**", "").replace("--", "").strip()
    return text

def search_clinvar(query):
    params = {"db":"clinvar","term":query,"retmode":"json","retmax":5}
    r = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi", params=params)
    return r.json()["esearchresult"]["idlist"]

def fetch_clinvar_record(uid):
    params = {"db":"clinvar","id":uid,"rettype":"vcv","retmode":"xml","from_esearch":"true"}
    r = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi", params=params)
    root = ET.fromstring(r.content)
    def txt(path):
        el = root.find(path)
        return el.text.strip() if el is not None and el.text else "Not found"
    va = root.find(".//VariationArchive")
    variant_name = va.attrib.get("VariationName","Not found") if va is not None else "Not found"
    gene_el = root.find(".//Gene")
    gene = gene_el.attrib.get("Symbol","Not found") if gene_el is not None else "Not found"
    conditions = []
    seen = set()
    for trait in root.findall(".//TraitSet/Trait"):
        name_el = trait.find(".//Name/ElementValue[@Type='Preferred']")
        if name_el is not None and name_el.text:
            val = name_el.text.strip()
            if val.lower() not in ("not provided","not specified") and val not in seen:
                seen.add(val)
                conditions.append(val)
    return {
        "variant_name": variant_name,
        "gene": gene,
        "clinical_significance": txt(".//GermlineClassification/Description"),
        "review_status": txt(".//ReviewStatus"),
        "variant_type": txt(".//VariantType"),
        "conditions": conditions if conditions else ["Not specified"],
        "submission_count": len(root.findall(".//ClinicalAssertion")),
    }

def get_omim_summary(gene_symbol):
    params = {"search":gene_symbol,"format":"json","apiKey":OMIM_KEY,"limit":1,"include":"geneMap"}
    r = requests.get("https://api.omim.org/api/entry/search", params=params)
    entries = r.json().get("omim",{}).get("searchResponse",{}).get("entryList",[])
    if not entries:
        return {"gene_symbol":gene_symbol,"gene_name":"Not found","diseases":["Not found"],"inheritance":"Not found"}
    entry = entries[0]["entry"]
    gene_map = entry.get("geneMap",{})
    phenotype_list = gene_map.get("phenotypeMapList",[])
    diseases = []
    inheritance_set = set()
    for item in phenotype_list:
        p = item.get("phenotypeMap",{})
        d = p.get("phenotype","")
        d = d.replace("{","").replace("}","").strip()
        inh = p.get("phenotypeInheritance","")
        if d and "?" not in d:
            diseases.append(d)
        if inh:
            inheritance_set.add(inh)
    return {
        "gene_symbol": gene_symbol,
        "gene_name": gene_map.get("geneName","Not found"),
        "diseases": diseases[:3] if diseases else ["Not found"],
        "inheritance": ", ".join(inheritance_set) if inheritance_set else "Not found",
    }

def explain_variant(clinvar, omim):
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1200,
        messages=[{"role":"user","content":f"""You are a genetics expert. Write three plain-English explanations. Use plain sentences only — no markdown, no bullet points, no ## headers, no bold, no dashes.

CLINVAR DATA:
- Variant: {clinvar['variant_name']}
- Gene: {clinvar['gene']}
- Clinical significance: {clinvar['clinical_significance']}
- Review status: {clinvar['review_status']}
- Conditions: {', '.join(clinvar['conditions'][:5])}
- Submissions: {clinvar['submission_count']}

OMIM DATA:
- Gene name: {omim['gene_name']}
- Diseases: {', '.join(omim['diseases'])}
- Inheritance: {omim['inheritance']}

Write exactly three sections. Use these exact headers on their own line:

PATIENT EXPLANATION:
2-3 plain sentences. No jargon. What this means for their health.
End with exactly: Note: This is not medical advice.

GP EXPLANATION:
3-4 plain sentences. Clinical context, inheritance pattern, recommended action.
End with exactly: Note: This is not medical advice.

GENETIC COUNSELLOR EXPLANATION:
4-5 plain sentences. Variant classification, evidence strength, molecular mechanism, family implications.
End with exactly: Note: This is not medical advice."""}]
    )
    return msg.content[0].text

def parse_explanations(text):
    sections = {"patient": "", "gp": "", "counsellor": ""}
    current = None
    buffer = []
    for line in text.split("\n"):
        l = line.strip()
        if "PATIENT EXPLANATION" in l.upper():
            current = "patient"; buffer = []
        elif "GP EXPLANATION" in l.upper():
            if current: sections[current] = clean_text(" ".join(buffer))
            current = "gp"; buffer = []
        elif "GENETIC COUNSELLOR EXPLANATION" in l.upper():
            if current: sections[current] = clean_text(" ".join(buffer))
            current = "counsellor"; buffer = []
        elif current and l:
            buffer.append(l)
    if current:
        sections[current] = clean_text(" ".join(buffer))
    return sections

def get_confidence(review_status, significance):
    rs = review_status.lower()
    sig = significance.lower()
    if "expert panel" in rs or "practice guideline" in rs:
        return "green", "dot-green", "Pathogenic — reviewed by expert panel"
    elif "pathogenic" in sig and "conflicting" not in sig:
        return "amber", "dot-amber", "Pathogenic — limited review"
    else:
        return "red", "dot-red", "Uncertain or conflicting evidence"

def render_output(clinvar, omim, sections, is_example=False):
    if is_example:
        st.markdown('<span class="section-label label-example">Example output — BRCA1 c.5266dupC</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge-done">Done</span>', unsafe_allow_html=True)

    color, dot_class, conf_label = get_confidence(clinvar["review_status"], clinvar["clinical_significance"])
    st.markdown(f'''
    <div class="confidence-row">
        <span class="{dot_class}"></span>
        <span>{conf_label}</span>
    </div>
    ''', unsafe_allow_html=True)

    with st.expander("▶ Raw clinical data"):
        st.json({"ClinVar": clinvar, "OMIM": omim})

    st.markdown('<hr class="hero-divider">', unsafe_allow_html=True)

    family_line = "This variant may be relevant for blood relatives — consider informing family members."
    card_border = f"card-{color}"

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="card {card_border}">
            <div class="card-role">🧑 Patient</div>
            <div class="card-title">For the Patient</div>
            <div class="card-body">{sections['patient']}</div>
            <div class="family-line">👨‍👩‍👧 {family_line}</div>
        </div>
        """, unsafe_allow_html=True)
        st.code(sections['patient'], language=None)

    with c2:
        st.markdown(f"""
        <div class="card {card_border}">
            <div class="card-role">🩺 Clinician</div>
            <div class="card-title">For the GP</div>
            <div class="card-body">{sections['gp']}</div>
        </div>
        """, unsafe_allow_html=True)
        st.code(sections['gp'], language=None)

    with c3:
        st.markdown(f"""
        <div class="card {card_border}">
            <div class="card-role">🔬 Specialist</div>
            <div class="card-title">For the Genetic Counsellor</div>
            <div class="card-body">{sections['counsellor']}</div>
        </div>
        """, unsafe_allow_html=True)
        st.code(sections['counsellor'], language=None)

    st.markdown(f'''
    <div class="footer-info">
        ⓘ Data sourced from ClinVar (NCBI) and OMIM. For educational purposes only — always consult a qualified healthcare professional.
    </div>
    ''', unsafe_allow_html=True)

# ── Hero ───────────────────────────────────────────────────
st.markdown('<p class="hero-title">Variant Explainer</p>', unsafe_allow_html=True)
st.markdown('''<p class="hero-desc">
    Built for patients, clinicians, and genetic counsellors who need clear answers from complex genetic data.<br>
    Paste any genetic variant or disease name. Get three tailored explanations — instantly.<br>
    Data pulled live from ClinVar and OMIM, translated into plain English.
</p>''', unsafe_allow_html=True)
st.markdown('<hr class="hero-divider">', unsafe_allow_html=True)

# ── Input ──────────────────────────────────────────────────
common_variants = {
    "Select a condition...": "",
    "Breast/Ovarian Cancer (BRCA1)": "BRCA1 c.5266dupC",
    "Cystic Fibrosis (CFTR)": "CFTR c.1521_1523delCTT",
    "Huntington's Disease": "HTT c.54GCA",
    "Hereditary Breast Cancer (BRCA2)": "BRCA2 c.5946delT",
    "Lynch Syndrome": "MLH1 c.1852_1853delAAinsGC",
    "Sickle Cell Anaemia": "HBB c.20A>T",
    "Marfan Syndrome": "FBN1 c.1453C>T",
    "Familial Hypercholesterolaemia": "LDLR c.1646G>A",
    "Fragile X Syndrome": "FMR1 c.1A>G",
    "Tay-Sachs Disease": "HEXA c.1274_1277dupTATC",
}

with st.expander("More conditions →"):
    st.markdown("**Cancer Risk**")
    st.code("BRCA1 c.5266dupC | BRCA2 c.5946delT | MLH1 c.1852_1853delAAinsGC | TP53 c.817C>T")
    st.markdown("**Cardiac**")
    st.code("MYBPC3 c.2905+1G>A | SCN5A c.4900G>A | LDLR c.1646G>A")
    st.markdown("**Neurological**")
    st.code("HTT c.54GCA | FMR1 c.1A>G | LRRK2 c.6055G>A")
    st.markdown("**Metabolic**")
    st.code("CFTR c.1521_1523delCTT | HBB c.20A>T | HEXA c.1274_1277dupTATC")
    st.markdown("**Other**")
    st.code("FBN1 c.1453C>T | PTEN c.388C>T")

selected = st.selectbox("Quick select a condition:", list(common_variants.keys()))
default_variant = common_variants[selected]
variant_input = st.text_input(
    "Or type any variant or disease name:",
    value=default_variant,
    placeholder="e.g. BRCA1 c.5266dupC or 'cystic fibrosis'"
)

run_col, _ = st.columns([2, 4])
with run_col:
    run_button = st.button("Explain this variant")

# ── Example on first load ──────────────────────────────────
if "example_shown" not in st.session_state:
    st.session_state.example_shown = False

if not run_button and not st.session_state.example_shown:
    st.markdown('<hr class="hero-divider">', unsafe_allow_html=True)
    example_clinvar = {
        "variant_name": "NM_007294.4(BRCA1):c.5266dupC (p.Gln1756ProfsTer25)",
        "gene": "BRCA1",
        "clinical_significance": "Pathogenic",
        "review_status": "reviewed by expert panel",
        "variant_type": "Duplication",
        "conditions": ["Hereditary breast ovarian cancer syndrome", "Familial cancer of breast"],
        "submission_count": 94,
    }
    example_omim = {
        "gene_symbol": "BRCA1",
        "gene_name": "BRCA1 DNA repair-associated protein",
        "diseases": ["Breast-ovarian cancer, familial 1", "Pancreatic cancer, susceptibility to, 4"],
        "inheritance": "Autosomal dominant",
    }
    example_sections = {
        "patient": "You have a change in your BRCA1 gene that significantly increases your lifetime risk of breast and ovarian cancer. This change is well-studied and classified as disease-causing by leading genetics experts. Your doctor will discuss screening options and preventive measures with you. Note: This is not medical advice.",
        "gp": "This patient carries a pathogenic frameshift variant in BRCA1 (c.5266dupC), classified as disease-causing by expert panel review across 94 ClinVar submissions. BRCA1-related cancer predisposition follows autosomal dominant inheritance, meaning first-degree relatives have a 50% chance of carrying the variant. Referral to clinical genetics and discussion of enhanced surveillance or risk-reduction options is recommended. Note: This is not medical advice.",
        "counsellor": "The variant NM_007294.4(BRCA1):c.5266dupC introduces a frameshift causing premature protein truncation (p.Gln1756ProfsTer25), classified Pathogenic with expert panel review across 94 submissions — the highest ClinVar evidence tier. Loss of BRCA1 function impairs homologous recombination DNA repair, conferring substantially elevated lifetime risk for breast (~70%) and ovarian (~44%) cancer. Inheritance is autosomal dominant; cascade testing of first-degree relatives is indicated. Discuss PARP inhibitor eligibility and surgical risk-reduction options as appropriate. Note: This is not medical advice.",
    }
    render_output(example_clinvar, example_omim, example_sections, is_example=True)

# ── Run ────────────────────────────────────────────────────
if run_button:
    if not variant_input.strip():
        st.warning("Please enter a variant or disease name.")
    else:
        st.session_state.example_shown = True
        with st.spinner("Looking up variant..."):
            if is_disease_name(variant_input):
                client_temp = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
                conversion = client_temp.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=50,
                    messages=[{"role":"user","content":f"What is the most common clinically significant ClinVar searchable variant for '{variant_input}'? Reply with ONLY the variant string like 'BRCA1 c.5266dupC'. Nothing else."}]
                )
                variant_input = conversion.content[0].text.strip()
                st.markdown(f'<div class="variant-chip">🔎 Most common variant identified: <strong>{variant_input}</strong></div>', unsafe_allow_html=True)

        with st.spinner("Fetching ClinVar data..."):
            uids = search_clinvar(variant_input)
            if not uids:
                st.error("No ClinVar record found. Try a different variant.")
                st.stop()
            time.sleep(0.4)
            clinvar = fetch_clinvar_record(uids[0])

        with st.spinner("Fetching OMIM data..."):
            omim = get_omim_summary(clinvar["gene"])

        with st.spinner("Generating explanations..."):
            explanation = explain_variant(clinvar, omim)
            sections = parse_explanations(explanation)

        st.markdown('<hr class="hero-divider">', unsafe_allow_html=True)
        render_output(clinvar, omim, sections)
