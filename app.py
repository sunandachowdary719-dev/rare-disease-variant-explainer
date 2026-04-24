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

@media (max-width: 768px) {
    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        padding-top: 1.5rem !important;
    }
    .hero-title { font-size: 2.2rem !important; }
    .hero-line1, .hero-line2 { font-size: 0.9rem !important; }
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

/* Disclaimer modal */
.disclaimer-box {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 2rem;
    max-width: 520px;
    margin: 4rem auto;
    box-shadow: 0 8px 32px rgba(0,0,0,0.10);
    text-align: center;
}
.disclaimer-title {
    font-size: 1.2rem;
    font-weight: 700;
    color: #0F172A;
    margin-bottom: 0.8rem;
}
.disclaimer-text {
    font-size: 0.9rem;
    color: #64748B;
    line-height: 1.7;
    margin-bottom: 1.4rem;
}

/* Severity summary */
.severity-summary {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 0.9rem 1.2rem;
    margin-bottom: 1.2rem;
    font-size: 0.95rem;
    color: #1e293b;
    font-weight: 400;
    line-height: 1.6;
}

/* Gene info card */
.gene-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 1rem 1.3rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.gene-card-title {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #94A3B8;
    margin-bottom: 0.6rem;
}
.gene-card-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem 1.5rem;
    font-size: 0.85rem;
    color: #334155;
}
.gene-card-item-label {
    font-weight: 600;
    color: #64748B;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Citation line */
.citation-line {
    font-size: 0.75rem;
    color: #94A3B8;
    margin-top: 0.8rem;
    padding-top: 0.6rem;
    border-top: 1px solid #F1F5F9;
}

/* Recent searches */
.recent-label {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #94A3B8;
    margin-bottom: 0.4rem;
}
.recent-chip {
    display: inline-block;
    background: #F1F5F9;
    color: #334155;
    border-radius: 20px;
    padding: 0.25rem 0.75rem;
    font-size: 0.78rem;
    margin-right: 0.4rem;
    margin-bottom: 0.4rem;
    cursor: pointer;
    border: 1px solid #E2E8F0;
}
.recent-chip:hover { background: #E2E8F0; }

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
    margin-bottom: 0.6rem;
    font-size: 0.85rem;
    color: #64748B;
}
.dot-green { width:9px; height:9px; border-radius:50%; background:#16a34a; display:inline-block; }
.dot-amber { width:9px; height:9px; border-radius:50%; background:#d97706; display:inline-block; }
.dot-red   { width:9px; height:9px; border-radius:50%; background:#dc2626; display:inline-block; }
.confidence-tooltip {
    font-size: 0.72rem;
    color: #94A3B8;
    margin-bottom: 1.2rem;
    padding-left: 1.1rem;
}

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

/* Empty state */
.empty-state {
    text-align: center;
    padding: 3rem 1rem;
    color: #94A3B8;
}
.empty-state-icon { font-size: 2.5rem; margin-bottom: 0.8rem; }
.empty-state-text { font-size: 0.95rem; line-height: 1.6; }

/* Progress */
.progress-label {
    font-size: 0.85rem;
    color: #64748B;
    margin-bottom: 0.4rem;
}

/* More conditions box */
.more-box {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    padding: 0.6rem 0.8rem;
    margin-top: 0.4rem;
    margin-bottom: 0.8rem;
}
.more-box-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #94A3B8;
    margin-bottom: 0.5rem;
    padding: 0 0.2rem;
}

/* Global buttons */
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

.cat-btn > div > button {
    background: transparent !important;
    color: #1e293b !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 0.4rem 0.6rem !important;
    font-size: 0.87rem !important;
    font-weight: 500 !important;
    width: 100% !important;
    text-align: left !important;
    box-shadow: none !important;
}
.cat-btn > div > button:hover {
    background: #F1F5F9 !important;
    opacity: 1 !important;
}
.cat-btn-active > div > button {
    background: #F1F5F9 !important;
    color: #0f172a !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 0.4rem 0.6rem !important;
    font-size: 0.87rem !important;
    font-weight: 600 !important;
    width: 100% !important;
    text-align: left !important;
    box-shadow: none !important;
}

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

/* Inputs */
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
    line-height: 1.8;
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
defaults = {
    "show_more": False,
    "active_category": None,
    "selected_variant": "",
    "disclaimer_accepted": False,
    "search_history": [],
    "last_search_time": 0,
    "search_count": 0,
    "results": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

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

def sanitise_input(text):
    text = text.strip()
    text = text[:200]
    text = re.sub(r'[<>{};`]', '', text)
    return text

def looks_valid(text):
    if len(text) < 2:
        return False
    has_gene = bool(re.search(r'[A-Z]{2,}', text))
    has_variant = any(c in text for c in ["c.", "p.", "rs", "del", "dup", "ins", ">"])
    has_disease_words = len(text.split()) >= 2
    return has_gene or has_variant or has_disease_words

def search_clinvar(query):
    params = {"db":"clinvar","term":query,"retmode":"json","retmax":5}
    r = requests.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
        params=params, timeout=10
    )
    r.raise_for_status()
    return r.json()["esearchresult"]["idlist"]

def fetch_clinvar_record(uid):
    params = {"db":"clinvar","id":uid,"rettype":"vcv","retmode":"xml","from_esearch":"true"}
    r = requests.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
        params=params, timeout=10
    )
    r.raise_for_status()
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
    accession = va.attrib.get("Accession","N/A") if va is not None else "N/A"
    return {
        "variant_name": variant_name,
        "gene": gene,
        "accession": accession,
        "clinical_significance": txt(".//GermlineClassification/Description"),
        "review_status": txt(".//ReviewStatus"),
        "variant_type": txt(".//VariantType"),
        "conditions": conditions if conditions else ["Not specified"],
        "submission_count": len(root.findall(".//ClinicalAssertion")),
    }

def get_omim_summary(gene_symbol):
    try:
        params = {"search":gene_symbol,"format":"json","apiKey":OMIM_KEY,"limit":1,"include":"geneMap"}
        r = requests.get("https://api.omim.org/api/entry/search", params=params, timeout=10)
        r.raise_for_status()
        entries = r.json().get("omim",{}).get("searchResponse",{}).get("entryList",[])
        if not entries:
            return {"gene_symbol":gene_symbol,"gene_name":"Not found","diseases":["Not found"],"inheritance":"Not found","mim_number":"N/A"}
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
            "mim_number": entry.get("mimNumber","N/A"),
        }
    except Exception:
        return {"gene_symbol":gene_symbol,"gene_name":"Unavailable","diseases":["OMIM data unavailable"],"inheritance":"Not found","mim_number":"N/A"}

def explain_variant(clinvar, omim):
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1400,
        messages=[{"role":"user","content":f"""You are a genetics expert writing for a US clinical audience. Write four things. Use plain sentences only — no markdown, no bullet points, no headers, no bold, no dashes.

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

Write exactly four sections with these exact headers on their own line:

SEVERITY SUMMARY:
One plain sentence giving the bottom-line clinical significance in plain English. No jargon.

PATIENT EXPLANATION:
2-3 plain sentences. No jargon. What this means for their health.
End with exactly: Note: This is not medical advice.

PRIMARY CARE DOCTOR EXPLANATION:
3-4 plain sentences. Clinical context, inheritance pattern, recommended action for a US primary care physician.
End with exactly: Note: This is not medical advice.

GENETIC COUNSELLOR EXPLANATION:
4-5 plain sentences. Variant classification, evidence strength, molecular mechanism, family implications.
End with exactly: Note: This is not medical advice."""}]
    )
    return msg.content[0].text

def parse_explanations(text):
    sections = {"severity": "", "patient": "", "pcd": "", "counsellor": ""}
    current = None
    buffer = []
    for line in text.split("\n"):
        l = line.strip()
        if "SEVERITY SUMMARY" in l.upper():
            current = "severity"; buffer = []
        elif "PATIENT EXPLANATION" in l.upper():
            if current: sections[current] = clean_text(" ".join(buffer))
            current = "patient"; buffer = []
        elif "PRIMARY CARE" in l.upper():
            if current: sections[current] = clean_text(" ".join(buffer))
            current = "pcd"; buffer = []
        elif "GENETIC COUNSELLOR" in l.upper():
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
        return "green", "dot-green", "Pathogenic — reviewed by expert panel", "This variant has been reviewed and confirmed by a panel of genetics experts — the highest level of evidence available."
    elif "pathogenic" in sig and "conflicting" not in sig:
        return "amber", "dot-amber", "Pathogenic — limited review", "This variant is classified as disease-causing but has limited expert review. Classification may change as more evidence accumulates."
    else:
        return "red", "dot-red", "Uncertain or conflicting evidence", "There is not yet enough evidence to confirm whether this variant causes disease. This is common for newly discovered variants."

def add_to_history(variant):
    history = st.session_state.search_history
    if variant not in history:
        history.insert(0, variant)
        st.session_state.search_history = history[:5]

def render_output(clinvar, omim, sections):
    st.markdown('<span class="badge-done">Done</span>', unsafe_allow_html=True)

    color, dot_class, conf_label, conf_tooltip = get_confidence(
        clinvar["review_status"], clinvar["clinical_significance"]
    )

    # Severity summary
    if sections.get("severity"):
        st.markdown(f'<div class="severity-summary">🔍 <strong>Bottom line:</strong> {sections["severity"]}</div>', unsafe_allow_html=True)

    # Confidence badge + tooltip
    st.markdown(f'''
    <div class="confidence-row">
        <span class="{dot_class}"></span>
        <span>{conf_label}</span>
    </div>
    <div class="confidence-tooltip">ⓘ {conf_tooltip}</div>
    ''', unsafe_allow_html=True)

    # Gene info card
    st.markdown(f'''
    <div class="gene-card">
        <div class="gene-card-title">🧬 Gene Information</div>
        <div class="gene-card-grid">
            <div><div class="gene-card-item-label">Gene</div>{clinvar["gene"]}</div>
            <div><div class="gene-card-item-label">Gene name</div>{omim["gene_name"]}</div>
            <div><div class="gene-card-item-label">Inheritance</div>{omim["inheritance"]}</div>
            <div><div class="gene-card-item-label">Variant type</div>{clinvar["variant_type"]}</div>
            <div><div class="gene-card-item-label">Submissions</div>{clinvar["submission_count"]} ClinVar records</div>
            <div><div class="gene-card-item-label">OMIM</div>{omim["mim_number"]}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    with st.expander("▶ Raw clinical data"):
        st.json({"ClinVar": clinvar, "OMIM": omim})

    st.markdown('<hr class="hero-divider">', unsafe_allow_html=True)

    family_line = "This variant may be relevant for blood relatives — consider informing family members."
    card_border = f"card-{color}"
    disclaimer = "Note: This is not medical advice."

    tab1, tab2, tab3 = st.tabs([
        "🧑 For the Patient",
        "🩺 For the Primary Care Doctor",
        "🔬 For the Genetic Counsellor"
    ])

    patient_text = sections['patient']
    if disclaimer.lower() not in patient_text.lower():
        patient_text += f" {disclaimer}"

    pcd_text = sections['pcd']
    if disclaimer.lower() not in pcd_text.lower():
        pcd_text += f" {disclaimer}"

    counsellor_text = sections['counsellor']
    if disclaimer.lower() not in counsellor_text.lower():
        counsellor_text += f" {disclaimer}"

    citation = f"Sources: ClinVar {clinvar['accession']} · OMIM {omim['mim_number']} · {clinvar['submission_count']} submissions"

    with tab1:
        st.markdown(f"""
        <div class="card {card_border}">
            <div class="card-role">🧑 Patient</div>
            <div class="card-title">For the Patient</div>
            <div class="card-body">{patient_text}</div>
            <div class="family-line">👨‍👩‍👧 {family_line}</div>
            <div class="citation-line">{citation}</div>
        </div>
        """, unsafe_allow_html=True)

    with tab2:
        st.markdown(f"""
        <div class="card {card_border}">
            <div class="card-role">🩺 Primary Care</div>
            <div class="card-title">For the Primary Care Doctor</div>
            <div class="card-body">{pcd_text}</div>
            <div class="citation-line">{citation}</div>
        </div>
        """, unsafe_allow_html=True)

    with tab3:
        st.markdown(f"""
        <div class="card {card_border}">
            <div class="card-role">🔬 Specialist</div>
            <div class="card-title">For the Genetic Counsellor</div>
            <div class="card-body">{counsellor_text}</div>
            <div class="citation-line">{citation}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f'''
    <div class="footer-info">
        ⓘ Data sourced from ClinVar (NCBI) and OMIM. For educational purposes only — always consult a qualified healthcare professional.<br>
        This tool covers variants with ClinVar records (~7,000+ rare diseases). It may not support newly discovered or ultra-rare variants not yet submitted to clinical databases.<br>
        Session searches: {st.session_state.search_count}
    </div>
    ''', unsafe_allow_html=True)

# ── Disclaimer modal ───────────────────────────────────────
if not st.session_state.disclaimer_accepted:
    st.markdown('''
    <div class="disclaimer-box">
        <div class="disclaimer-title">⚕️ Before you continue</div>
        <div class="disclaimer-text">
            This tool is for <strong>educational purposes only</strong> and does not constitute medical advice.<br><br>
            Variant interpretations are sourced from ClinVar and OMIM — publicly available clinical databases.
            Always consult a qualified healthcare professional or genetic counsellor before making any
            clinical or personal health decisions based on genetic information.
        </div>
    </div>
    ''', unsafe_allow_html=True)
    _, center, _ = st.columns([2, 1, 2])
    with center:
        if st.button("I understand — continue"):
            st.session_state.disclaimer_accepted = True
            st.rerun()
    st.stop()

# ── Hero ───────────────────────────────────────────────────
st.markdown('''
<div class="hero-wrap">
    <div class="hero-title">Variant Explainer</div>
    <div class="hero-line1">Built for patients, clinicians, and genetic counsellors who need clear answers from complex genetic data.</div>
    <div class="hero-line2">Paste any genetic variant or disease name and get plain-English explanations instantly.</div>
</div>
<hr class="hero-divider">
''', unsafe_allow_html=True)

# ── Recent searches ────────────────────────────────────────
if st.session_state.search_history:
    st.markdown('<div class="recent-label">Recent searches</div>', unsafe_allow_html=True)
    cols = st.columns(len(st.session_state.search_history))
    for i, prev in enumerate(st.session_state.search_history):
        with cols[i]:
            if st.button(prev, key=f"recent_{i}"):
                st.session_state.selected_variant = prev
                st.rerun()

# ── Input row ──────────────────────────────────────────────
drop_col, more_col, spacer = st.columns([3, 1, 2])

with drop_col:
    selected = st.selectbox("Quick select a condition:", list(common_variants.keys()))
    if common_variants[selected]:
        st.session_state.selected_variant = common_variants[selected]

with more_col:
    st.markdown("<div style='margin-top:1.85rem'></div>", unsafe_allow_html=True)
    toggle_label = "✕ Close" if st.session_state.show_more else "More →"
    st.markdown('<div class="more-toggle">', unsafe_allow_html=True)
    if st.button(toggle_label, key="toggle_more"):
        st.session_state.show_more = not st.session_state.show_more
        st.session_state.active_category = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ── More conditions ────────────────────────────────────────
if st.session_state.show_more:
    box_col, _ = st.columns([1, 3])
    with box_col:
        st.markdown('<div class="more-box">', unsafe_allow_html=True)
        st.markdown('<div class="more-box-label">Browse by category</div>', unsafe_allow_html=True)

        for category, items in more_conditions.items():
            is_active = st.session_state.active_category == category
            arrow = "▾" if is_active else "›"
            btn_class = "cat-btn-active" if is_active else "cat-btn"

            st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
            if st.button(f"{arrow}  {category}", key=f"cat_{category}"):
                st.session_state.active_category = None if is_active else category
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

            if is_active:
                options = ["Select a condition..."] + list(items.keys())
                choice = st.selectbox(
                    label=f"{category} conditions",
                    options=options,
                    key=f"select_{category}",
                    label_visibility="collapsed"
                )
                if choice != "Select a condition...":
                    st.session_state.selected_variant = items[choice]
                    st.session_state.show_more = False
                    st.session_state.active_category = None
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

# ── Text input with keyboard submit ───────────────────────
if st.session_state.selected_variant:
    st.session_state["variant_input_field"] = st.session_state.selected_variant
    st.session_state.selected_variant = ""

variant_input = st.text_input(
    "Or type any variant or disease name:",
    placeholder="e.g. BRCA1 c.5266dupC or 'Huntington's disease'",
    key="variant_input_field"
)

# Keyboard Enter triggers run
st.markdown("""
<script>
const input = window.parent.document.querySelector('input[data-testid="stTextInput"]');
if (input) {
    input.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            const btn = window.parent.document.querySelector('button[kind="primary"]');
            if (btn) btn.click();
        }
    });
}
</script>
""", unsafe_allow_html=True)

run_col, _ = st.columns([2, 5])
with run_col:
    run_button = st.button("Explain this variant", type="primary")

# ── Empty state ────────────────────────────────────────────
if not run_button and not st.session_state.results:
    st.markdown('''
    <div class="empty-state">
        <div class="empty-state-icon">🧬</div>
        <div class="empty-state-text">
            Select a condition above or type a variant name.<br>
            Your explanation will appear here.
        </div>
    </div>
    ''', unsafe_allow_html=True)

# ── Run ────────────────────────────────────────────────────
if run_button:
    # Usage cap
    if st.session_state.search_count >= 10:
        st.warning("You've run 10 searches this session. Consider bookmarking your results. Refresh the page to continue.")
        st.stop()

    # Rate limiting
    now = time.time()
    if now - st.session_state.last_search_time < 3:
        st.warning("Please wait a moment before searching again.")
        st.stop()

    # Input validation
    clean_input = sanitise_input(variant_input)
    if not clean_input:
        st.warning("Please enter a variant or disease name.")
        st.stop()
    if not looks_valid(clean_input):
        st.warning("That doesn't look like a valid variant or disease name. Try something like 'BRCA1 c.5266dupC' or 'Huntington's disease'.")
        st.stop()

    st.session_state.last_search_time = now
    st.session_state.search_count += 1

    try:
        # Step 1
        st.markdown('<div class="progress-label">Step 1 of 3 — Looking up variant...</div>', unsafe_allow_html=True)
        with st.spinner(""):
            if is_disease_name(clean_input):
                client_temp = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
                conversion = client_temp.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=50,
                    messages=[{"role":"user","content":f"What is the most common clinically significant ClinVar searchable variant for '{clean_input}'? Reply with ONLY the variant string like 'BRCA1 c.5266dupC'. Nothing else."}]
                )
                resolved = conversion.content[0].text.strip()
                st.markdown(f'<div class="variant-chip">🔎 Found: <strong>{clean_input}</strong> → <strong>{resolved}</strong> (most common variant)</div>', unsafe_allow_html=True)
                clean_input = resolved
            time.sleep(0.3)

        # Step 2
        st.markdown('<div class="progress-label">Step 2 of 3 — Fetching clinical data...</div>', unsafe_allow_html=True)
        with st.spinner(""):
            uids = search_clinvar(clean_input)
            if not uids:
                st.error("We couldn't find this variant in ClinVar. Try checking the spelling or use a different format — e.g. 'BRCA1 c.5266dupC' or try a disease name like 'Huntington's disease'.")
                st.stop()
            time.sleep(0.4)
            clinvar = fetch_clinvar_record(uids[0])
            omim = get_omim_summary(clinvar["gene"])

        # Step 3
        st.markdown('<div class="progress-label">Step 3 of 3 — Generating explanations...</div>', unsafe_allow_html=True)
        with st.spinner(""):
            explanation = explain_variant(clinvar, omim)
            sections = parse_explanations(explanation)

        # Update browser title
        st.markdown(f"<script>window.parent.document.title = '{clinvar['gene']} — Variant Explainer';</script>", unsafe_allow_html=True)

        add_to_history(clean_input)
        st.session_state.results = {"clinvar": clinvar, "omim": omim, "sections": sections}
        st.markdown('<hr class="hero-divider">', unsafe_allow_html=True)
        render_output(clinvar, omim, sections)

    except requests.exceptions.Timeout:
        st.error("The request timed out. The clinical databases may be slow — please try again in a moment.")
    except requests.exceptions.ConnectionError:
        st.error("Connection error. Please check your internet connection and try again.")
    except Exception as e:
        st.error("Something went wrong while fetching data. Please try a different variant or try again shortly.")

elif st.session_state.results and not run_button:
    r = st.session_state.results
    st.markdown('<hr class="hero-divider">', unsafe_allow_html=True)
    render_output(r["clinvar"], r["omim"], r["sections"])
