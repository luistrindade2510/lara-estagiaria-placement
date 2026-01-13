import re
import pandas as pd
import streamlit as st
import time

# =========================
# CONFIGURAÇÃO DA PÁGINA
# =========================
st.set_page_config(
    page_title="JOY – Assistente Placement Jr",
    page_icon="💬",
    layout="centered",
)

# =========================
# CSS (VISUAL PREMIUM)
# =========================
st.markdown("""
<style>
.block-container { max-width: 1100px; padding-top: 2.5rem; }

.joy-hero {
  display: flex;
  gap: 32px;
  align-items: center;
  margin-bottom: 32px;
}

.joy-text h1 {
  font-size: 34px;
  margin-bottom: 8px;
}

.joy-slogan {
  color: rgba(0,0,0,.65);
  font-size: 16px;
  margin-bottom: 18px;
}

.joy-instruction {
  font-size: 17px;
  margin-bottom: 6px;
}

.joy-muted {
  color: rgba(0,0,0,.55);
  font-size: 14px;
}

.joy-section-title {
  font-weight: 600;
  margin-top: 28px;
  margin-bottom: 10px;
}

.joy-chip {
  display:inline-block;
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid rgba(0,0,0,.12);
  font-size: 13px;
  margin-right: 6px;
}

.joy-divider {
  margin: 30px 0;
  border-bottom: 1px solid rgba(0,0,0,.08);
}
</style>
""", unsafe_allow_html=True)

# =========================
# ESTADO DO APP
# =========================
if "state" not in st.session_state:
    st.session_state.state = "idle"  # idle | loading | success

# =========================
# HERO (VÍDEO + TEXTO)
# =========================
st.markdown('<div class="joy-hero">', unsafe_allow_html=True)

# Vídeo da JOY conforme estado
if st.session_state.state == "idle":
    st.video("joy_idle.mp4", loop=True)
elif st.session_state.state == "loading":
    st.video("joy_loading.mp4", loop=True)
elif st.session_state.state == "success":
    st.video("joy_success.mp4", loop=True)

st.markdown("""
<div class="joy-text">
  <h1>💬 JOY – Assistente Placement Jr</h1>
  <div class="joy-slogan">
    Status, histórico e andamento dos estudos — sem depender de mensagens no Teams.
  </div>
  <div class="joy-instruction">
    Consulte estudos de Placement com clareza e rapidez.
  </div>
  <div class="joy-muted">
    Informe o código da demanda ou o nome da empresa para começar.
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# =========================
# DADOS
# =========================
SHEETS_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT7eJXK_IARZPmt6GdsQLDPX4sSI-aCWZK286Y4DtwhVXr3NOH22eTIPwkFSbF14rfdYReQndgU51st/pub?gid=0&single=true&output=csv"

COL_ID = "COD_ACRISURE"
COL_DATE = "DATA_ATUALIZACAO"
COL_EMPRESA = "EMPRESA"
COL_DEMANDA = "DEMANDA"
COL_PRODUTO = "PRODUTO"
COL_AUTOR = "AUTOR"
COL_STATUS = "STATUS"
COL_TEXTO = "TEXTO"

@st.cache_data(ttl=60)
def load_data(url):
    df = pd.read_csv(url)
    df[COL_DATE] = pd.to_datetime(df[COL_DATE], errors="coerce", dayfirst=True)
    df[COL_ID] = df[COL_ID].astype(str)
    return df

df = load_data(SHEETS_CSV_URL)

# =========================
# BUSCA
# =========================
user_msg = st.chat_input(
    "Digite o código da demanda ou o nome da empresa  •  Ex.: 6163 | Leadec | desde 10/01/2026"
)

if user_msg:
    st.session_state.state = "loading"
    time.sleep(1.2)

    term = user_msg.lower()
    result = df[
        df[COL_ID].str.contains(term, na=False) |
        df[COL_EMPRESA].str.lower().str.contains(term, na=False)
    ].sort_values(by=COL_DATE, ascending=False)

    if result.empty:
        st.session_state.state = "idle"
        st.chat_message("assistant").markdown(
            "Não encontrei estudos com esses critérios. "
            "Tente ajustar o código ou o nome da empresa."
        )
    else:
        st.session_state.state = "success"
        r = result.iloc[0]
        d = r[COL_DATE].strftime("%d/%m/%Y") if pd.notna(r[COL_DATE]) else "—"

        st.chat_message("assistant").markdown(
            f"""
**Última atualização**

- **Empresa:** {r[COL_EMPRESA]}
- **Demanda:** {r[COL_DEMANDA]}
- **Produto:** {r[COL_PRODUTO]}
- **Status:** {r[COL_STATUS]}
- **Data:** {d}

**Resumo:** {r[COL_TEXTO]}
"""
        )
