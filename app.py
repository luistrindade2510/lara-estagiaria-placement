import re
import pandas as pd
import streamlit as st

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="JOY – Assistente Placement Jr",
    page_icon="💬",
    layout="centered",
)

# Arquivos no repo
HERO_IMAGE = "joy.png"            # imagem do topo (pode trocar por png)
RESULT_VIDEO = "joy_loading.mp4"  # vídeo pequeno APENAS no resultado (você pediu esse)

SHEETS_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT7eJXK_IARZPmt6GdsQLDPX4sSI-aCWZK286Y4DtwhVXr3NOH22eTIPwkFSbF14rfdYReQndgU51st/pub?gid=0&single=true&output=csv"

COL_ID = "COD_ACRISURE"
COL_DATE = "DATA_ATUALIZACAO"
COL_EMPRESA = "EMPRESA"
COL_DEMANDA = "DEMANDA"
COL_PRODUTO = "PRODUTO"
COL_AUTOR = "AUTOR"
COL_STATUS = "STATUS"
COL_TEXTO = "TEXTO"

# =========================
# STATE
# =========================
if "query" not in st.session_state:
    st.session_state.query = ""

if "produto_seg" not in st.session_state:
    st.session_state.produto_seg = "Todos"  # Todos | Saúde | Odonto | Ambos

if "modo_seg" not in st.session_state:
    st.session_state.modo_seg = "Última atualização"  # Última atualização | Histórico

# =========================
# CSS (corrige chips quebrando + refine premium)
# =========================
st.markdown(
    """
<style>
.block-container{
  max-width: 980px;
  padding-top: 1.2rem;
  padding-bottom: 2rem;
}

/* Card topo */
.joy-hero{
  border: 1px solid rgba(0,0,0,.08);
  border-radius: 20px;
  padding: 16px 16px;
  background: rgba(255,255,255,.92);
  box-shadow: 0 12px 30px rgba(0,0,0,.05);
}

/* Título / slogan */
.joy-title{
  font-size: 26px;
  font-weight: 850;
  line-height: 1.15;
  margin: 0;
}
.joy-slogan{
  margin-top: 6px;
  font-size: 13px;
  color: rgba(0,0,0,.58);
}
.joy-desc{
  margin-top: 10px;
  font-size: 14px;
  color: rgba(0,0,0,.85);
  line-height: 1.5;
}

/* Chips (PRINT 3 fix: não quebrar texto e não criar linha feia) */
.joy-chip-row{
  display:flex;
  flex-wrap:wrap;
  gap: 8px;
  margin-top: 10px;
}

div[data-testid="stButton"] > button{
  white-space: nowrap !important;   /* <<< impede quebrar linha */
}

.joy-chip button{
  border-radius: 999px !important;
  padding: 6px 10px !important;
  border: 1px solid rgba(0,0,0,.12) !important;
  background: rgba(255,255,255,.95) !important;
  font-size: 12px !important;       /* <<< menor pra caber */
}

/* Input e botão Buscar */
div[data-testid="stTextInput"] input{
  border-radius: 14px !important;
  border: 1px solid rgba(0,0,0,.12) !important;
  padding: 11px 12px !important;
}
div[data-testid="stTextInput"] input:focus{
  border: 1px solid rgba(0,0,0,.20) !important;
  box-shadow: 0 0 0 4px rgba(0,0,0,.05) !important;
}
.joy-primary button{
  border-radius: 14px !important;
  padding: 10px 12px !important;
  border: 1px solid rgba(0,0,0,.12) !important;
  font-weight: 750 !important;
}

/* Refine premium */
.joy-refine{
  border: 1px solid rgba(0,0,0,.08);
  border-radius: 18px;
  padding: 14px 14px;
  background: rgba(255,255,255,.92);
  box-shadow: 0 12px 26px rgba(0,0,0,.04);
  margin-top: 14px;
}
.joy-ref-title{
  font-weight: 850;
  font-size: 14px;
  margin: 0;
}
.joy-ref-sub{
  margin-top: 4px;
  font-size: 12.5px;
  color: rgba(0,0,0,.58);
}

/* Radios horizontais (segmentado) */
div[role="radiogroup"]{
  gap: 10px !important;
}
div[role="radiogroup"] label{
  border: 1px solid rgba(0,0,0,.12);
  border-radius: 999px;
  padding: 6px 10px;
  background: rgba(255,255,255,.95);
}
div[role="radiogroup"] label:has(input:checked){
  background: rgba(0,0,0,.06);
  border: 1px solid rgba(0,0,0,.18);
  font-weight: 750;
}

/* Card de resultado */
.joy-result{
  border: 1px solid rgba(0,0,0,.08);
  border-radius: 18px;
  padding: 14px 14px;
  background: rgba(255,255,255,.94);
  box-shadow: 0 12px 26px rgba(0,0,0,.04);
  margin-top: 14px;
}
.joy-hr{
  margin: 12px 0;
  border-bottom: 1px solid rgba(0,0,0,.08);
}

/* Avatar vídeo pequeno no resultado (PRINT 2 vibe) */
.joy-mini-video{
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid rgba(0,0,0,.10);
  box-shadow: 0 10px 20px rgba(0,0,0,.06);
}

/* Tabela */
[data-testid="stDataFrame"]{
  border-radius: 14px;
  overflow:hidden;
  border: 1px solid rgba(0,0,0,.08);
}
</style>
""",
    unsafe_allow_html=True,
)

# =========================
# DATA
# =========================
@st.cache_data(ttl=60, show_spinner=False)
def load_data(url: str) -> pd.DataFrame:
    df = pd.read_csv(url)
    df.columns = [c.strip() for c in df.columns]
    df[COL_DATE] = pd.to_datetime(df[COL_DATE], errors="coerce", dayfirst=True)
    df[COL_ID] = df[COL_ID].astype(str).str.strip()

    for c in [COL_EMPRESA, COL_DEMANDA, COL_PRODUTO, COL_AUTOR, COL_STATUS, COL_TEXTO]:
        if c in df.columns:
            df[c] = df[c].astype(str).fillna("").str.strip()
    return df

df = load_data(SHEETS_CSV_URL)

# =========================
# HELPERS
# =========================
def parse_user_message(msg: str):
    m = msg.strip()

    historico = bool(re.search(r"\bhist(ó|o)rico\b|\bhist\b", m, flags=re.I))

    produto = None
    if re.search(r"\bambos\b|\bodonto\+sa(ú|u)de\b", m, flags=re.I):
        produto = "AMBOS"
    elif re.search(r"\bodonto\b", m, flags=re.I):
        produto = "ODONTO"
    elif re.search(r"\bsa(ú|u)de\b", m, flags=re.I):
        produto = "SAÚDE"

    date_since = None
    msince = re.search(r"desde\s+(\d{1,2}/\d{1,2}/\d{4})", m, flags=re.I)
    if msince:
        try:
            date_since = pd.to_datetime(msince.group(1), dayfirst=True)
        except Exception:
            date_since = None

    mid = re.search(r"\b(\d{3,})\b", m)
    demanda_id = mid.group(1) if mid else None

    cleaned = re.sub(r"\bhist(ó|o)rico\b|\bhist\b", "", m, flags=re.I)
    cleaned = re.sub(r"\bsa(ú|u)de\b|\bodonto\b|\bambos\b|\bodonto\+sa(ú|u)de\b", "", cleaned, flags=re.I)
    cleaned = re.sub(r"desde\s+\d{1,2}/\d{1,2}/\d{4}", "", cleaned, flags=re.I)
    cleaned = cleaned.strip(" -|,;")

    empresa_term = None if demanda_id else cleaned.strip()
    if empresa_term == "":
        empresa_term = None

    return demanda_id, empresa_term, produto, historico, date_since

def filter_df(df: pd.DataFrame, demanda_id=None, empresa_term=None, produto=None, date_since=None):
    out = df.copy()

    if demanda_id:
        out = out[out[COL_ID] == str(demanda_id)]

    if empresa_term:
        term = empresa_term.lower()
        out = out[out[COL_EMPRESA].str.lower().str.contains(term, na=False)]

    # produto
    if produto and produto != "AMBOS":
        out = out[out[COL_PRODUTO].str.lower().str.contains(produto.lower(), na=False)]

    if date_since is not None:
        out = out[out[COL_DATE] >= date_since]

    return out.sort_values(by=COL_DATE, ascending=False)

def produto_from_segment(seg: str):
    if seg == "Saúde":
        return "SAÚDE"
    if seg == "Odonto":
        return "ODONTO"
    if seg == "Ambos":
        return "AMBOS"
    return None

def is_hist_from_segment(seg: str):
    return seg == "Histórico"

# =========================
# HERO (volta pro estilo do print 1)
# =========================
st.markdown("<div class='joy-hero'>", unsafe_allow_html=True)
c_img, c_txt = st.columns([1, 3], vertical_alignment="center")

with c_img:
    try:
        st.image(HERO_IMAGE, use_container_width=True)
    except Exception:
        st.write("")

with c_txt:
    st.markdown("<p class='joy-title'>J.O.Y – Assistente Placement Jr</p>", unsafe_allow_html=True)
    st.markdown(
        "<div class='joy-slogan'>Status, histórico e andamento — sem depender de mensagens no Teams.</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='joy-desc'><b>Como pesquisar:</b> digite <b>ID</b> ou <b>empresa</b>. "
        "Para refinar: <b>saúde/odonto</b>, <b>histórico</b>, <b>desde dd/mm/aaaa</b>.</div>",
        unsafe_allow_html=True,
    )

    # Busca
    st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)
    c_in, c_btn = st.columns([4.4, 1.2])
    with c_in:
        st.session_state.query = st.text_input(
            "🔎 O que vamos consultar agora?",
            value=st.session_state.query,
            label_visibility="collapsed",
            placeholder="Ex.: 6163 | Leadec | 6163 histórico | Leadec saúde | desde 10/01/2026",
        )
    with c_btn:
        st.markdown("<div class='joy-primary'>", unsafe_allow_html=True)
        do_search = st.button("Buscar", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Chips (corrigidos - sem linha/quebra)
    st.markdown("<div class='joy-chip-row'>", unsafe_allow_html=True)
    chips = ["6163", "6163 histórico", "Leadec", "Leadec saúde", "Leadec odonto", "desde 10/01/2026"]
    chip_cols = st.columns(6)
    for i, ch in enumerate(chips):
        with chip_cols[i]:
            st.markdown("<div class='joy-chip'>", unsafe_allow_html=True)
            if st.button(ch):
                st.session_state.query = ch
                do_search = True
            st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)  # fecha hero

# =========================
# REFINE (profissional)
# =========================
st.markdown("<div class='joy-refine'>", unsafe_allow_html=True)
st.markdown("<div class='joy-ref-title'>🎛️ Refine</div>", unsafe_allow_html=True)
st.markdown("<div class='joy-ref-sub'>Escolha o produto e o modo. Depois clique em <b>Buscar</b>.</div>", unsafe_allow_html=True)

rf1, rf2, rf3 = st.columns([2.2, 2.2, 1.1], vertical_alignment="center")

with rf1:
    st.session_state.produto_seg = st.radio(
        "Produto",
        ["Todos", "Saúde", "Odonto", "Ambos"],
        horizontal=True,
        label_visibility="collapsed",
        index=["Todos", "Saúde", "Odonto", "Ambos"].index(st.session_state.produto_seg),
    )

with rf2:
    st.session_state.modo_seg = st.radio(
        "Modo",
        ["Última atualização", "Histórico"],
        horizontal=True,
        label_visibility="collapsed",
        index=["Última atualização", "Histórico"].index(st.session_state.modo_seg),
    )

with rf3:
    if st.button("🧽 Limpar", use_container_width=True):
        st.session_state.produto_seg = "Todos"
        st.session_state.modo_seg = "Última atualização"
        st.session_state.query = ""

st.markdown(
    f"""
<span class="joy-pilltag">Produto: {st.session_state.produto_seg}</span>
<span class="joy-pilltag">Modo: {st.session_state.modo_seg}</span>
""",
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)

# =========================
# RESULTADO
# =========================
if do_search and st.session_state.query.strip():
    q = st.session_state.query.strip()

    demanda_id, empresa_term, produto_text, historico_text, date_since = parse_user_message(q)

    # aplica refine caso não veio no texto
    seg_prod = produto_from_segment(st.session_state.produto_seg)
    seg_hist = is_hist_from_segment(st.session_state.modo_seg)

    produto_final = produto_text or seg_prod
    historico_final = historico_text or seg_hist

    result = filter_df(df, demanda_id, empresa_term, produto_final, date_since)

    st.markdown("<div class='joy-result'>", unsafe_allow_html=True)

    if result.empty:
        st.markdown("### 😅 Não encontrei nada")
        st.markdown("Tenta só **6163** ou só **Leadec** (sem mais nada) e depois refina.")
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        # Header do card + vídeo pequeno (estilo print 2)
        left, right = st.columns([4.6, 1.2], vertical_alignment="top")

        with left:
            if historico_final:
                st.markdown("### 🗂️ Histórico")
                st.markdown("<div style='color:rgba(0,0,0,.58);font-size:12.8px'>Mais recente primeiro</div>", unsafe_allow_html=True)
            else:
                st.markdown("### 📌 Última atualização")

            st.markdown(f"<div style='color:rgba(0,0,0,.58);font-size:12.8px'>Consulta: <b>{q}</b></div>", unsafe_allow_html=True)

        with right:
            # VÍDEO PEQUENO — só aqui (nada de loading)
            try:
                st.markdown("<div class='joy-mini-video'>", unsafe_allow_html=True)
                st.video(RESULT_VIDEO)  # fica pequeno pq a coluna é pequena
                st.markdown("</div>", unsafe_allow_html=True)
            except Exception:
                pass

        st.markdown("<div class='joy-hr'></div>", unsafe_allow_html=True)

        if historico_final:
            view = result[[COL_DATE, COL_STATUS, COL_PRODUTO, COL_AUTOR, COL_TEXTO]].copy()
            view[COL_DATE] = view[COL_DATE].dt.strftime("%d/%m/%Y")
            view = view.rename(columns={
                COL_DATE: "Data",
                COL_STATUS: "Status",
                COL_PRODUTO: "Produto",
                COL_AUTOR: "Autor",
                COL_TEXTO: "Atualização",
            })
            st.dataframe(view, use_container_width=True, hide_index=True)

        else:
            r = result.iloc[0]
            d = r[COL_DATE].strftime("%d/%m/%Y") if pd.notna(r[COL_DATE]) else "—"
            st.markdown(
                f"""
- **ID:** {r[COL_ID]}
- **Empresa:** {r[COL_EMPRESA]}
- **Demanda:** {r[COL_DEMANDA]}
- **Produto:** {r[COL_PRODUTO]}
- **Status:** {r[COL_STATUS]}
- **Data:** {d}
- **Autor:** {r[COL_AUTOR]}

**Resumo:** {r[COL_TEXTO]}
"""
            )

        st.markdown("</div>", unsafe_allow_html=True)
