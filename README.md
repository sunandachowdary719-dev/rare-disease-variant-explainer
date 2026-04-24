# rare-disease-variant-explainer
# Variant Explainer

A plain-English genetic variant explainer for patients, primary care doctors, and genetic counsellors.

## What it does

Variant Explainer takes any genetic variant (like `BRCA1 c.5266dupC`) or disease name (like "Huntington's disease") and generates three separate plain-English explanations tailored to different audiences — a patient with no medical background, a primary care physician, and a genetic counsellor. It pulls live data from ClinVar and OMIM, the same clinical databases used in genetics labs, and uses AI to translate the raw clinical data into clear, accurate language.

## Who it's for

Clinical genetics is full of jargon that patients can't understand and reports that primary care doctors weren't trained to interpret. This tool bridges that gap for any of the 7,000+ rare diseases represented in ClinVar.

## How to use it

- Go to [rare-disease-explainer.streamlit.app](https://rare-disease-explainer.streamlit.app)
- Type a genetic variant (e.g. `BRCA1 c.5266dupC`) or a disease name (e.g. `cystic fibrosis`)
- Get three plain-English explanations instantly

## Data sources

- **ClinVar** (NCBI) — clinical significance, review status, submission count
- **OMIM** — gene-disease associations, inheritance patterns
- **Claude API** (Anthropic) — plain-English translation and audience-switching

## Limitations

This tool covers variants with ClinVar records (~7,000+ rare diseases). It may not support newly discovered or ultra-rare variants not yet submitted to clinical databases. All outputs include a "not medical advice" disclaimer.

## Built with

Python · Streamlit · ClinVar API · OMIM API · Claude API (Anthropic)

## Disclaimer

This tool is for educational purposes only and does not constitute medical advice. Always consult a qualified healthcare professional or genetic counsellor before making any clinical or personal health decisions based on genetic information.
