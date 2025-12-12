# app.py
import streamlit as st
import pdfplumber
import re, io
import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import nltk

# ensure NLTK data is present (first run may take a sec)
nltk.download('punkt')
nltk.download('stopwords')

st.set_page_config(page_title="PDF Keyword Paragraphs + WordCloud", layout="wide")
st.title("PDF → Paragraph Extractor + WordCloud")

# Optional: set a default PDF path to auto-load for local testing
DEFAULT_PDF_PATH = None  # change to "/mnt/data/Annual-Report-2024-25.pdf" to auto-load locally

uploaded_file = st.file_uploader("Upload PDF (or use default path)", type=["pdf"])
use_default = False
if DEFAULT_PDF_PATH and uploaded_file is None:
    try:
        with open(DEFAULT_PDF_PATH, "rb") as f:
            pdf_bytes = f.read()
        use_default = True
        st.sidebar.success(f"Loaded default file: {DEFAULT_PDF_PATH}")
    except Exception as e:
        pdf_bytes = None
        st.sidebar.warning(f"Unable to load default file: {e}")
else:
    pdf_bytes = uploaded_file.read() if uploaded_file else None

keywords_input = st.sidebar.text_input("Enter keywords (comma-separated)", value="semiconductor, aerospace, xEV, orderbook")
min_len = st.sidebar.number_input("Minimum paragraph length (chars)", min_value=20, max_value=2000, value=50)
show_pars = st.sidebar.checkbox("Display matched paragraphs", value=True)

def extract_paragraphs_from_bytes(pdf_bytes):
    paragraphs = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            txt = page.extract_text() or ""
            raw_pars = re.split(r'\n{2,}', txt)
            for p in raw_pars:
                p = p.strip()
                if p:
                    paragraphs.append(p)
    return paragraphs

if not pdf_bytes:
    st.warning("Upload a PDF (or set DEFAULT_PDF_PATH in app.py for local testing).")
    st.stop()

with st.spinner("Extracting paragraphs..."):
    paragraphs = extract_paragraphs_from_bytes(pdf_bytes)
st.success(f"Extracted {len(paragraphs)} paragraphs")

keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
if not keywords:
    st.sidebar.error("Enter at least one keyword.")
    st.stop()

matched = [p for p in paragraphs if len(p) >= min_len and any(k.lower() in p.lower() for k in keywords)]
st.write(f"Paragraphs matching keywords ({len(keywords)}): {len(matched)}")

if show_pars:
    for i,p in enumerate(matched[:200],1):
        st.markdown(f"**Paragraph {i}:** {p}")

if matched:
    combined = " ".join(matched).lower()
    combined = re.sub(r'[^a-z0-9\s]', ' ', combined)
    combined = re.sub(r'\s+', ' ', combined)

    stop_words = set(stopwords.words('english'))
    custom_stop = {'company','annual','report','page','sansera','engineering','limited','note','notes','figure','table','financial'}
    stop_words |= custom_stop

    tokens = [w for w in word_tokenize(combined) if w.isalnum() and len(w)>2 and w not in stop_words]
    freqs = pd.Series(tokens).value_counts().head(50)
    st.subheader("Top tokens")
    st.dataframe(freqs.reset_index().rename(columns={'index':'token',0:'count'}))

    wc = WordCloud(width=1200, height=600, background_color='white', collocations=False).generate(" ".join(tokens))
    fig, ax = plt.subplots(figsize=(12,6))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')
    st.pyplot(fig)

    df_out = pd.DataFrame({'paragraph': matched})
    st.download_button("Download matched paragraphs CSV", df_out.to_csv(index=False).encode('utf-8'),
                       file_name="matched_paragraphs.csv", mime="text/csv")
else:
    st.info("No paragraphs matched the given keywords. Try broader keywords or reduce min length.")
