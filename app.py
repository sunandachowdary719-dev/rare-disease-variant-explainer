import streamlit as st
import requests
import xml.etree.ElementTree as ET
import anthropic
import time
import re

st.set_page_config(
    page_title="Variant Explainer",
    page_icon="🧬",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Inter', 'Segoe UI', sans-serif;
    background-color: #F9FAFB;
    color: #0F172A;
}
.main { background-color: #F9FAFB; }
.block-container {
    padding-top: 3rem;
    padding-left: 4rem;
    padding-right: 4rem;
    max-width: 100%;
}

.hero-wrap { text-align: center; margin-bottom: 1rem; }
.hero-title {
    font-size: 3.8rem;
    font-weight: 700;
    color: #0F172A;
    letter-spacing: -0.04em;
    line-height: 1.1;
    margin-bottom: 0.8rem;
}
.hero-line1 {
    font-size: 1rem;
    color: #64748B;
    line-height: 1.5;
    font-weight: 400;
    max-width: 580px;
    margin: 0 auto 0.3rem auto;
}
.hero-line2 {
    font-size: 1rem;
    color: #64748B;
    line-height: 1.5;
    font-weight: 400;
    max-width: 580px;
    margin: 0 auto;
}
.hero-divider {
    border: none;
    border-top: 1px solid #E2E8F0;
    margin: 1.2rem 0;
}

.badge-done {
    display: inline-block;
    background: #16a34a;
    color: white;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 2px 10px;
    border-radius: 12px;
    margin-bottom: 1rem;
    letter-spacing: 0.03em;
}
.confidence-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1.2rem;
    font-size: 0.85rem;
    color: #64748B;
}
.dot-green { width:9px; height:9px; border-radius:50%; background:#16a34a; display:inline-block; }
.dot-amber { width:9px; height:9px; border-radius:50%; background:#d97706; display:inline-block; }
.dot-red   { width:9px; height:9px; border-radius:50%; background:#dc2626; display:inline-block; }

.card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 1.8rem 2rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    height: auto !important;
    min-height: 0 !important;
    max-height: none !important;
    overflow: visible !important;
    margin-bottom: 1rem;
}
.card-green { border-left: 3px solid #16a34a; }
.card-amber { border-left: 3px solid #d97706; }
.card-red   { border-left: 3px solid #dc2626; }
.card-role {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #94A3B8;
    margin-bottom: 0.4rem;
}
.card-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #0F172A;
    margin-bottom: 0.8rem;
}
.card-body {
    font-size: 0.95rem;
    line-height: 1.8;
    color: #334155;
    font-weight: 400;
    word-wrap: break-word;
    overflow-wrap: break-word;
    white-space: normal;
    overflow: visible !important;
    height: auto !important;
    max-height: none !important;
}
.family-line {
    font-size: 0.81rem;
    color: #94A3B8;
    font-style: italic;
    margin-top: 0.9rem;
    padding-top: 0.7rem;
    border-top: 1px solid #F1F5F9;
    word-wrap: break-word;
}

.variant-chip {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 10px;
    padding: 0.65rem 1rem;
    color: #1d4ed8;
    font-size: 0.86rem;
    margin-bottom: 1rem;
}

/* More conditions box */
.more-box {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.10);
    padding: 0.4rem 0;
    margin-top: 0.4rem;
    margin-bottom: 0.8rem;
    max-width: 280px;
}
.more-box-cat {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.52rem 1rem;
    font-size: 0.88rem;
    font-weight: 500;
    color: #1e293b;
    cursor: pointer;
    border-radius: 6px;
    margin: 0 0.3rem;
    transition: background 0.1s;
}
.more-box-cat:hover { background: #F8FAFC; }
.more-box-cat-active {
    background: #F1F5F9;
    color: #0f172a;
    font-weight: 600;
}
.more-box-arrow { color: #94A3B8; font-size: 0.75rem; }
.more-box-item {
    padding: 0.42rem 1rem 0.42rem 1.6rem;
    font-size: 0.83rem;
    color: #2563eb;
    cursor: pointer;
    border-radius: 6px;
    margin: 0 0.3rem;
}
.more-box-item:hover { background: #EFF6FF; }
.more-box-divider {
    border: none;
    border-top: 1px solid #F1F5F9;
    margin: 0.2rem 0.8rem;
}

/* Buttons */
.stTextInput > div > div > input {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 10px !important;
    color: #0F172A !important;
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Inter', sans-serif !important;
    font-size: 0.95rem !important;
    padding: 0.7rem 1rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: #2563eb !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.1) !important;
}
.stSelectbox > div > div {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 10px !important;
    color: #0F172A !important;
}
.stButton > button {
    background: #0f172a !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.62rem 1.6rem !important;
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Inter', sans-serif !important;
    font-size: 0.92rem !important;
    font-weight: 500 !important;
    transition: opacity 0.15s !important;
}
.stButton > button:hover { opacity: 0.84 !important; }

/* Category row buttons — invisible style */
.cat-row-btn > div > button {
    background: transparent !important;
    color: #1e293b !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 0.45rem 0.8rem !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    width: 100% !important;
    text-align: left !important;
    box-shadow: none !important;
    justify-content: flex-start !important;
}
.cat-row-btn > div > button:hover {
    background: #F8FAFC !important;
    opacity: 1 !important;
}
.cat-row-btn-active > div > button {
    background: #F1F5F9 !important;
    color: #0f172a !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 0.45rem 0.8rem !important;
    font-size: 0.88rem !important;
    width: 100% !important;
    text-align: left !important;
    box-shadow: none !important;
}

/* Condition item buttons */
.cond-item > div > button {
    background: transparent !important;
    color: #2563eb !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 0.38rem 0.8rem 0.38rem 1.8rem !important;
    font-size: 0.83rem !important;
    font-weight: 400 !important;
    width: 100% !important;
    text-align: left !important;
    box-shadow: none !important;
}
.cond-item > div > button:hover {
    background: #EFF6FF !important;
    opacity: 1 !important;
}

/* More toggle */
.more-toggle > div > button {
    background: #0f172a !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.5rem 1.1rem !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    width: auto !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    border-bottom: 2px solid #E2E8F0;
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border: none !important;
    border-radius: 8px 8px 0 0 !important;
    padding: 0.6rem 1.2rem !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    color: #64748B !important;
}
.stTabs [aria-selected="true"] {
    background: #FFFFFF !important;
    color: #0F172A !important;
    border-bottom: 2px solid #0f172a !important;
    font-weight: 600 !important;
}
.stTabs [data-baseweb="tab-panel"] {
    padding: 1.2rem 0 0 0 !important;
}

.footer-info {
    font-size: 0.76rem;
    color: #94A3B8;
    text-align: center;
    margin-top: 2.5rem;
    padding-top: 1.2rem;
    border-top: 1px solid #E2E8F0;
    line-height: 1.6;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ── Keys ───────────────────────────────────────────────────
ANTHROPIC_KEY = st.secrets["ANTHROPIC_KEY"]
OMIM_KEY = st.secrets["OMIM_KEY"]

# ── Session state ──────────────────────────────────────────
if "show_more" not in st.session_state:
    st.session_state.show_more = False
if "active_category" not in st.session_state:
    st.session_state.active_category = None
if "selected_variant" not in st.session_state:
    st.session_state.selected_variant = ""

# ── Data ───────────────────────────────────────────────────
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

more_conditions = {
    "Cancer Risk": {
        "BRCA1 c.5266dupC": "BRCA1 c.5266dupC",
        "BRCA2 c.5946delT": "BRCA2 c.5946delT",
        "MLH1 c.1852_1853delAAinsGC": "MLH1 c.1852_1853delAAinsGC",
        "TP53 c.817C>T": "TP53 c.817C>T",
    },
    "Cardiac": {
        "MYBPC3 c.2905+1G>A": "MYBPC3 c.2905+1G>A",
        "SCN5A c.4900G>A": "SCN5A c.4900G>A",
        "LDLR c.1646G>A": "LDLR c.1646G>A",
    },
    "Neurological": {
        "Huntington's Disease": "HTT c.54GCA",
        "Parkinson's LRRK2": "LRRK2 c.6055G>A",
        "Fragile X": "FMR1 c.1A>G",
    },
    "Metabolic": {
        "PKU": "PAH c.1066-11G>A",
        "Gaucher Disease": "GBA c.1226A>G",
        "Tay-Sachs": "HEXA c.1274_1277dupTATC",
    },
    "Other": {
        "Cystic Fibrosis": "CFTR c.1521_1523delCTT",
        "Marfan Syndrome": "FBN1 c.1453C>T",
        "Ehlers-Danlos Syndrome": "COL5A1 c.1867C>T",
    },
}

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
        messages=[{"role":"user","content":f"""You are a genetics expert. Write three plain-English explanations. Use plain sentences only — no markdown, no bullet points, no headers, no bold, no dashes.

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

Write exactly three sections with these exact headers on their own line:

PATIENT EXPLANATION:
2-3 plain sentences. No jargon.
End with exactly: Note: This is not medical advice.

GP EXPLANATION:
3-4 plain sentences. Clinical context, inheritance, recommended action.
End with exactly: Note: This is not medical advice.

GENETIC COUNSELLOR EXPLANATION:
4-5 plain sentences. Classification, evidence, mechanism, family implications.
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

def render_output(clinvar, omim, sections):
    st.markdown('<span class="badge-done">Done</span>', unsafe_allow_html=True)
    color, dot_class, conf_label = get_confidence(
        clinvar["review_status"], clinvar["clinical_significance"]
    )
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

    tab1, tab2, tab3 = st.tabs([
        "🧑 For the Patient",
        "🩺 For the GP",
        "🔬 For the Genetic Counsellor"
    ])

    with tab1:
        st.markdown(f"""
        <div class="card {card_border}">
            <div class="card-role">🧑 Patient</div>
            <div class="card-title">For the Patient</div>
            <div class="card-body">{sections['patient']}</div>
            <div class="family-line">👨‍👩‍👧 {family_line}</div>
        </div>
        """, unsafe_allow_html=True)

    with tab2:
        st.markdown(f"""
        <div class="card {card_border}">
            <div class="card-role">🩺 Clinician</div>
            <div class="card-title">For the GP</div>
            <div class="card-body">{sections['gp']}</div>
        </div>
        """, unsafe_allow_html=True)

    with tab3:
        st.markdown(f"""
        <div class="card {card_border}">
            <div class="card-role">🔬 Specialist</div>
            <div class="card-title">For the Genetic Counsellor</div>
            <div class="card-body">{sections['counsellor']}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('''
    <div class="footer-info">
        ⓘ Data sourced from ClinVar (NCBI) and OMIM. For educational purposes only — always consult a qualified healthcare professional.
    </div>
    ''', unsafe_allow_html=True)

# ── Hero ───────────────────────────────────────────────────
st.markdown('''
<div class="hero-wrap">
    <div class="hero-title">Variant Explainer</div>
    <div class="hero-line1">Built for patients, clinicians, and genetic counsellors who need clear answers from complex genetic data.</div>
    <div class="hero-line2">Paste any genetic variant or disease name and get three tailored plain-English explanations instantly.</div>
</div>
<hr class="hero-divider">
''', unsafe_allow_html=True)

# ── Input row ──────────────────────────────────────────────
drop_col, more_col, spacer = st.columns([3, 1, 2])

with drop_col:
    selected = st.selectbox("Quick select a condition:", list(common_variants.keys()))
    if common_variants[selected]:
        st.session_state.selected_variant = common_variants[selected]

with more_col:
    st.markdown("<div style='margin-top:1.85rem'></div>", unsafe_allow_html=True)
    toggle_label = "✕ Close" if st.session_state.show_more else "More conditions →"
    st.markdown('<div class="more-toggle">', unsafe_allow_html=True)
    if st.button(toggle_label, key="toggle_more"):
        st.session_state.show_more = not st.session_state.show_more
        st.session_state.active_category = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ── Compact inline more-conditions box ────────────────────
if st.session_state.show_more:
    box_col, _ = st.columns([1, 3])
    with box_col:
        st.markdown('<div class="more-box">', unsafe_allow_html=True)

        categories = list(more_conditions.keys())
        for idx, category in enumerate(categories):
            is_active = st.session_state.active_category == category
            cat_class = "cat-row-btn-active" if is_active else "cat-row-btn"
            arrow = "▾" if is_active else "›"
            label = f"{arrow}  {category}"

            st.markdown(f'<div class="{cat_class}">', unsafe_allow_html=True)
            if st.button(label, key=f"cat_{category}"):
                if st.session_state.active_category == category:
                    st.session_state.active_category = None
                else:
                    st.session_state.active_category = category
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

            # Inline expanded conditions
            if is_active:
                for label_cond, variant in more_conditions[category].items():
                    st.markdown('<div class="cond-item">', unsafe_allow_html=True)
                    if st.button(f"  {label_cond}", key=f"cond_{variant}"):
                        st.session_state.selected_variant = variant
                        st.session_state.show_more = False
                        st.session_state.active_category = None
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

            # Divider between categories (not after last)
            if idx < len(categories) - 1:
                st.markdown('<hr class="more-box-divider">', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

# ── Text input ─────────────────────────────────────────────
variant_input = st.text_input(
    "Or type any variant or disease name:",
    value=st.session_state.selected_variant,
    placeholder="e.g. BRCA1 c.5266dupC or 'cystic fibrosis'"
)

run_col, _ = st.columns([2, 5])
with run_col:
    run_button = st.button("Explain this variant")

# ── Run ────────────────────────────────────────────────────
if run_button:
    if not variant_input.strip():
        st.warning("Please enter a variant or disease name.")
    else:
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
