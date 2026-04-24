import streamlit as st
import requests
import xml.etree.ElementTree as ET
import anthropic
import time

# ── Page config must be first ──────────────────────────────
st.set_page_config(
    page_title="Variant Explainer",
    page_icon="🧬",
    layout="centered"
)

# ── Custom CSS ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0a0f1e;
    color: #e8eaf0;
}

.main { background-color: #0a0f1e; }

.hero-title {
    font-family: 'DM Serif Display', serif;
    font-size: 3.2rem;
    line-height: 1.15;
    color: #ffffff;
    margin-bottom: 0.3rem;
}

.hero-subtitle {
    font-size: 1.05rem;
    color: #8892a4;
    font-weight: 300;
    margin-bottom: 2.5rem;
    line-height: 1.6;
}

.section-card {
    background: #111827;
    border: 1px solid #1e2d45;
    border-radius: 16px;
    padding: 1.8rem 2rem;
    margin-bottom: 1.2rem;
}

.section-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 0.6rem;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    display: inline-block;
}

.label-patient {
    background: #0d2137;
    color: #38bdf8;
}

.label-gp {
    background: #0d2b1e;
    color: #34d399;
}

.label-counsellor {
    background: #1e1637;
    color: #a78bfa;
}

.section-text {
    font-size: 1rem;
    line-height: 1.75;
    color: #cbd5e1;
    font-weight: 300;
}

.badge-high {
    background: #052e16;
    color: #4ade80;
    border: 1px solid #166534;
    padding: 0.5rem 1.2rem;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 500;
    display: inline-block;
    margin-bottom: 1.5rem;
}

.badge-mid {
    background: #1c1a09;
    color: #facc15;
    border: 1px solid #713f12;
    padding: 0.5rem 1.2rem;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 500;
    display: inline-block;
    margin-bottom: 1.5rem;
}

.badge-low {
    background: #1a1f2e;
    color: #94a3b8;
    border: 1px solid #334155;
    padding: 0.5rem 1.2rem;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 500;
    display: inline-block;
    margin-bottom: 1.5rem;
}

.variant-found {
    background: #0d2137;
    border: 1px solid #1e4976;
    border-radius: 10px;
    padding: 0.8rem 1.2rem;
    color: #38bdf8;
    font-size: 0.9rem;
    margin-bottom: 1rem;
}

.divider {
    border: none;
    border-top: 1px solid #1e2d45;
    margin: 2rem 0;
}

.footer-text {
    color: #4b5563;
    font-size: 0.78rem;
    text-align: center;
    margin-top: 2rem;
}

/* Input styling */
.stTextInput > div > div > input {
    background-color: #111827 !important;
    border: 1px solid #1e2d45 !important;
    border-radius: 10px !important;
    color: #e8eaf0 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 1rem !important;
    padding: 0.75rem 1rem !important;
}

.stTextInput > div > div > input:focus {
    border-color: #38bdf8 !important;
    box-shadow: 0 0 0 2px rgba(56,189,248,0.15) !important;
}

/* Button styling */
.stButton > button {
    background: linear-gradient(135deg, #0ea5e9, #6366f1) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.65rem 2rem !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.02em !important;
    transition: opacity 0.2s !important;
    width: 100% !important;
}

.stButton > button:hover {
    opacity: 0.88 !important;
}

/* Selectbox */
.stSelectbox > div > div {
    background-color: #111827 !important;
    border: 1px solid #1e2d45 !important;
    border-radius: 10px !important;
    color: #e8eaf0 !important;
}

/* Hide streamlit default elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ── Keys ───────────────────────────────────────────────────
ANTHROPIC_KEY = st.secrets["ANTHROPIC_KEY"]
OMIM_KEY = st.secrets["OMIM_KEY"]

# ── Functions ──────────────────────────────────────────────
def is_disease_name(text):
    return not any(c in text for c in ["c.", "p.", "rs", "del", "dup", "ins", ">"])

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
        max_tokens=1000,
        messages=[{"role":"user","content":f"""You are a genetics expert. Write three plain-English explanations.

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

Write exactly three sections:

PATIENT EXPLANATION:
(2-3 sentences. No jargon. What this means for their health.)

GP EXPLANATION:
(3-4 sentences. Clinical context. Inheritance and recommended action.)

GENETIC COUNSELLOR EXPLANATION:
(4-5 sentences. Technical detail. Classification, evidence, family implications.)

End every section with: Note: This is not medical advice."""}]
    )
    return msg.content[0].text

# ── Hero ───────────────────────────────────────────────────
st.markdown('<p class="hero-title">🧬 Variant Explainer</p>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Paste a genetic variant or disease name.<br>Get plain-English explanations for patients, GPs, and genetic counsellors.</p>', unsafe_allow_html=True)

# ── Input ──────────────────────────────────────────────────
common_variants = {
    "Select a common disease...": "",
    "Breast/Ovarian Cancer (BRCA1)": "BRCA1 c.5266dupC",
    "Cystic Fibrosis (CFTR)": "CFTR c.1521_1523delCTT",
    "Huntington's Disease": "HTT c.54GCA",
    "Hereditary Breast Cancer (BRCA2)": "BRCA2 c.5946delT",
    "Lynch Syndrome": "MLH1 c.1852_1853delAAinsGC",
    "Sickle Cell Anaemia": "HBB c.20A>T",
    "Marfan Syndrome": "FBN1 c.1453C>T",
}
selected = st.selectbox("Quick select a condition:", list(common_variants.keys()))
default_variant = common_variants[selected]
variant_input = st.text_input(
    "Or type any variant or disease name:",
    value=default_variant,
    placeholder="e.g. BRCA1 c.5266dupC or 'cystic fibrosis'"
)

st.button_clicked = st.button("🔍 Explain this variant")

if st.button_clicked:
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
                st.markdown(f'<div class="variant-found">🔎 Most common variant identified: <strong>{variant_input}</strong></div>', unsafe_allow_html=True)

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

        # Badge
        rs = clinvar["review_status"].lower()
        sig = clinvar["clinical_significance"].lower()
        if "expert panel" in rs or "practice guideline" in rs:
            badge_class = "badge-high"
            badge_text = "🟢 High confidence — reviewed by expert panel"
        elif "pathogenic" in sig:
            badge_class = "badge-mid"
            badge_text = "🟡 Moderate confidence — pathogenic, limited review"
        else:
            badge_class = "badge-low"
            badge_text = "⚪ Low confidence — limited evidence"

        st.markdown(f'<div class="{badge_class}">{badge_text}</div>', unsafe_allow_html=True)

        # Raw data
        with st.expander("📊 View raw clinical data"):
            st.json({"ClinVar": clinvar, "OMIM": omim})

        st.markdown('<hr class="divider">', unsafe_allow_html=True)

        # Parse and display sections
        sections = explanation.strip().split("\n\n")
        labels = {
            "PATIENT": ("label-patient", "👤 For the Patient"),
            "GP": ("label-gp", "🩺 For the GP"),
            "GENETIC COUNSELLOR": ("label-counsellor", "🔬 For the Genetic Counsellor"),
        }

        for section in sections:
            if not section.strip():
                continue
            matched_label = None
            matched_class = None
            for key, (css_class, display) in labels.items():
                if key in section.upper():
                    matched_label = display
                    matched_class = css_class
                    break
            text = section.strip()
            for key in labels:
                text = text.replace(f"{key} EXPLANATION:", "").replace(f"{key}:", "").strip()
            if matched_label:
                st.markdown(f"""
                <div class="section-card">
                    <span class="section-label {matched_class}">{matched_label}</span>
                    <p class="section-text">{text}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                if text:
                    st.markdown(f'<p class="section-text">{text}</p>', unsafe_allow_html=True)

        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        st.markdown('<p class="footer-text">Data from ClinVar (NCBI) & OMIM · For educational purposes only · Always consult a healthcare professional</p>', unsafe_allow_html=True)
