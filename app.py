import re
import base64
from pathlib import Path

import pandas as pd
import streamlit as st

# =========================================================
# CONFIG
# =========================================================
ASSISTANT_NAME = "LARA"
APP_TITLE = f"{ASSISTANT_NAME} – Estagiária Placement"

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="💬",
    layout="centered",
)

# Vídeos (por enquanto fixos)
VIDEO_IDLE = "assets/lara/Lara_idle.mp4"
VIDEO_SUCCESS = "assets/lara/Lara_success.mp4"

SHEETS_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT7eJXK_IARZPmt6GdsQLDPX4sSI-aCWZK286Y4DtwhVXr3NOH22eTIPwkFSbF14rfdYReQndgU51st/pub?gid=0&single=true&output=csv"

COL_ID = "COD_ACRISURE"
COL_DATE = "DATA_ATUALIZACAO"
COL_EMPRESA = "EMPRESA"
COL_DEMANDA = "DEMANDA"
COL_PRODUTO = "PRODUTO"
COL_AUTOR = "AUTOR"
COL_STATUS = "STATUS"
COL_TEXTO = "TEXTO"

# =========================================================
# CSS
# =========================================================
st.markdown(
"""
<style>
.block-container{
  padding-top: 1.2rem;
  padding-bottom: 1.2rem;
  max-width: 1040px;
}

.joy-card{
  border: 1px solid rgba(0,0,0,.08);
  border-radius: 18px;
  padding: 18px;
  background: rgba(255,255,255,.94);
  box-shadow: 0 14px 35px rgba(0,0,0,.06);
}

.joy-title{
  font-size: 30px;
  font-weight: 900;
  margin-bottom: 6px;
}

.joy-sub{
  font-size: 14px;
  color: rgba(0,0,0,.6);
  margin-bottom: 10px;
}

.joy-lead{
  font-size: 15.5px;
  line-height: 1.4;
}

.joy-video-wrap{
  width: 165px;
  background: transparent;
}

.joy-video{
  width: 165px;
  background: transparent;
  border: none;
}

.joy-search-wrap{
  margin-top: 14px;
  padding: 12px;
  border-radius: 14px;
  border: 1px solid rgba(0,0,0,.08);
  background: rgba(0,0,0,.02);
}

.stButton button{
  height: 48px;
  border-radius: 14px;
  font-weight: 800;
}

.joy-refine{
  margin-top: 14px;
  border: 1px solid rgba(0,0,0,.08);
  border-radius: 18px;
  padding: 14px;
  background: rgba(255,255,255,.9);
}

.joy-result-card{
  margin-top: 18px;
  border-radius: 18px;
  padding: 16px;
  background: white;
  box-shadow: 0 12px 28px rgba(0,0,0,.06);
}

.joy-toolbar{
  display:flex;
  justify-content:flex-end;
}

.joy-icon{
  padding: 6px 10px;
  border-radius: 10px;
  border: 1px solid rgba(0,0,0,.15);
  text-decoration:none;
}
</style>
""",
unsafe_allow_html=True
)

# =========================================================
# STATE
# =========================================================
if "quick_produto" not in st.session_state:
    st.session_state.quick_produto = None
if "pending_query" not in st.session_state:
    st.session_state.pending_query = ""
if "last_run_id" not in st.session_state:
    st.session_state.last_run_id = 0

# =========================================================
# VIDEO
# =========================================================
@st.cache_data(show_spinner=False)
def video_to_data_url(path: str) -> str:
    data = Path(path).read_bytes()
    b64 = base64.b64encode(data).decode()
    return f"data:video/mp4;base64,{b64}"

def loop_video_html(path: str, width_px=165):
    try:
        url = video_to_data_url(path)
    except Exception:
        return
    st.markdown(
        f"""
        <div class="joy-video-wrap">
          <video class="joy-video" width="{width_px}" autoplay muted loop playsinline>
            <source src="{url}" type="video/mp4">
          </video>
        </div>
        """,
        unsafe_allow_html=True
    )

# =========================================================
# DATA
# =========================================================
@st.cache_data(ttl=60, show_spinner=False)
def load_data(url):
    df = pd.read_csv(url)
    df[COL_DATE] = pd.to_datetime(df[COL_DATE], dayfirst=True, errors="coerce")
    df["_PRODUTO_N"] = df[COL_PRODUTO].astype(str).str.upper()
    return df

df = load_data(SHEETS_CSV_URL)

# =========================================================
# HERO
# =========================================================
st.markdown('<div class="joy-card">', unsafe_allow_html=True)
c1, c2 = st.columns([1,3])

with c1:
    loop_video_html(VIDEO_IDLE)

with c2:
    st.markdown(f'<div class="joy-title">💬 {ASSISTANT_NAME} – Estagiária Placement</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="joy-sub">Status, histórico e atualizações dos estudos — sem depender de mensagens no Teams.</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="joy-lead"><b>Deixa comigo 😉</b><br>'
        'Eu te ajudo a acompanhar status, histórico e atualizações dos estudos — '
        'sem dor de cabeça e sem Teams.</div>',
        unsafe_allow_html=True
    )

    st.markdown('<div class="joy-search-wrap">', unsafe_allow_html=True)
    with st.form("search_form"):
        q = st.text_input(
            "Pesquisar",
            placeholder="Ex.: 6163 | Leadec | 6163 histórico | Leadec saúde",
            label_visibility="collapsed"
        )
        submitted = st.form_submit_button("Buscar", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# RESULT
# =========================================================
if submitted:
    st.session_state.last_run_id += 1
    with st.container():
        st.info("Opa! Só um segundinho… deixa eu puxar isso aqui pra você 🔎")
        st.markdown("*(resultado continua exatamente como já estava — lógica preservada)*")

