import streamlit as st
import requests
import xml.etree.ElementTree as ET
import anthropic
import time

ANTHROPIC_KEY = st.secrets["ANTHROPIC_KEY"]
OMIM_KEY = st.secrets["OMIM_KEY"]

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
    diseases, inheritance_set = [], set()
    for item in phenotype_list:
        p = item.get("phenotypeMap",{})
      d = p.get("phenotype", "")
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

def get_badge(review_status, significance):
    if "expert panel" in review_status.lower():
        return "🟢 High confidence — reviewed by expert panel"
    elif "pathogenic" in significance.lower():
        return "🟡 Moderate confidence — pathogenic but limited review"
    else:
        return "⚪ Low confidence — limited evidence"

st.set_page_config(page_title="Rare Disease Variant Explainer", page_icon="🧬")
st.title("🧬 Rare Disease Variant Explainer")
st.markdown("Type a gene variant below and get plain-English explanations for patients, GPs, and genetic counsellors.")

variant_input = st.text_input("Enter a variant (e.g. BRCA1 c.5266dupC)", placeholder="BRCA1 c.5266dupC")

if st.button("🔍 Explain this variant"):
    if not variant_input.strip():
        st.warning("Please enter a variant first.")
    else:
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
        st.success("Done!")
        badge = get_badge(clinvar["review_status"], clinvar["clinical_significance"])
        st.markdown(f"### {badge}")
        with st.expander("📊 Raw clinical data"):
            st.write("**ClinVar:**", clinvar)
            st.write("**OMIM:**", omim)
        st.markdown("---")
        for section in explanation.split("\n\n"):
            if section.strip():
                st.markdown(section)
        st.markdown("---")
        st.caption("Data sources: ClinVar (NCBI), OMIM. This tool is for educational purposes only.")
