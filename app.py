import re
import base64
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

HERO_IMAGE = "joy.png"
RESULT_LOOP_VIDEO = "joy_loading.mp4"  # ou "joy_success.mp4"

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
# CSS (premium)
# =========================
st.markdown(
    """
<style>
.block-container{
  max-width: 980px;
  padding-top: 1.2rem;
  padding-bottom: 2.2rem;
}

/* HERO */
.joy-hero{
  border: 1px solid rgba(0,0,0,.08);
  border-radius: 22px;
  padding: 18px 18px;
  background: rgba(255,255,255,.92);
  box-shadow: 0 16px 36px rgba(0,0,0,.06);
}

.joy-title{
  font-size: 28px;
  font-weight: 900;
  margin: 0;
  line-height: 1.12;
}

.joy-slogan{
  margin-top: 6px;
  font-size: 13.5px;
  color: rgba(0,0,0,.58);
}

.joy-desc{
  margin-top: 10px;
  font-size: 14px;
  color: rgba(0,0,0,.88);
  line-height: 1.55;
}

/* SEARCH */
.joy-search-row{ margin-top: 12px; }

div[data-testid="stTextInput"] input{
  border-radius: 16px !important;
  border: 1px solid rgba(0,0,0,.12) !important;
  padding: 12px 12px !important;
  font-size: 14px !important;
}
div[data-testid="stTextInput"] input:focus{
  border: 1px solid rgba(0,0,0,.22) !important;
  box-shadow: 0 0 0 5px rgba(0,0,0,.05) !important;
}

.joy-primary button{
  border-radius: 16px !important;
  padding: 11px 12px !important;
  border: 1px solid rgba(0,0,0,.12) !important;
  font-weight: 850 !important;
}

/* REFINE */
.joy-refine{
  border: 1px solid rgba(0,0,0,.08);
  border-radius: 20px;
  padding: 14px 14px;
  background: rgba(255,255,255,.92);
  box-shadow: 0 14px 30px rgba(0,0,0,.05);
  margin-top: 14px;
}
.joy-ref-title{
  font-weight: 900;
  font-size: 14px;
  margin: 0;
}
.joy-ref-sub{
  margin-top: 4px;
  font-size: 12.5px;
  color: rgba(0,0,0,.58);
}

div[role="radiogroup"]{
  gap: 10px !important;
}
div[role="radiogroup"] label{
  border: 1px solid rgba(0,0,0,.12);
  border-radius: 999px;
  padding: 7px 11px;
  background: rgba(255,255,255,.95);
}
div[role="radiogroup"] label:has(input:checked){
  background: rgba(0,0,0,.06);
  border: 1px solid rgba(0,0,0,.18);
  font-weight: 850;
}

.joy-pillline{
  margin-top: 10px;
  font-size: 13px;
  color: rgba(0,0,0,.75);
}

/* RESULT CARD */
.joy-result{
  border: 1px solid rgba(0,0,0,.08);
  border-radius: 22px;
  padding: 16px 16px;
  background: rgba(255,255,255,.94);
  box-shadow: 0 16px 34px rgba(0,0,0,.05);
  margin-top: 14px;
}
.joy-hr{ margin: 12px 0; border-bottom: 1px solid rgba(0,0,0,.08); }

/* LOOP VIDEO (sem controles) */
.joy-video-box{
  border-radius: 18px;
  overflow: hidden;
  border: 1px solid rgba(0,0,0,.10);
  box-shadow: 0 14px 28px rgba(0,0,0,.06);
}

/* Tabela */
[data-testid="stDataFrame"]{
  border-radius: 16px;
  overflow:hidden;
  border: 1px solid rgba(0,0,0,.08);
}
</style>
""",
    unsafe_allow_html=True,
)


# =========================
# HELPERS
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


@st.cache_data(show_spinner=False)
def video_to_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def render_loop_video(path: str, height_px: int = 260):
    """
    Vídeo loop REAL (autoplay, loop, muted, playsinline) sem controles.
    """
    try:
        b64 = video_to_base64(path)
        html = f"""
        <div class="joy-video-box">
          <video autoplay loop muted playsinline style="width:100%; height:{height_px}px; object-fit:cover; display:block;">
            <source src="data:video/mp4;base64,{b64}" type="video/mp4">
          </video>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)
    except Exception:
        # fallback silencioso
        st.write("")


# =========================
# UI - HERO
# =========================
df = load_data(SHEETS_CSV_URL)

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

    # search box + button
    st.markdown("<div class='joy-search-row'></div>", unsafe_allow_html=True)
    c_in, c_btn = st.columns([4.2, 1.3])
    with c_in:
        st.session_state.query = st.text_input(
            "🔎 Pesquisa",
            value=st.session_state.query,
            label_visibility="collapsed",
            placeholder="Ex.: 6163 | Leadec | 6163 histórico | Leadec saúde | desde 10/01/2026",
        )
    with c_btn:
        st.markdown("<div class='joy-primary'>", unsafe_allow_html=True)
        do_search = st.button("Buscar", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ✅ REMOVIDO: exemplos/chips (você riscou — agora não existe mais)


# =========================
# UI - REFINE (premium)
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
    f"<div class='joy-pillline'>Produto: <b>{st.session_state.produto_seg}</b> &nbsp;•&nbsp; "
    f"Modo: <b>{st.session_state.modo_seg}</b></div>",
    unsafe_allow_html=True,
)

st.markdown("</div>", unsafe_allow_html=True)


# =========================
# RESULT
# =========================
if do_search and st.session_state.query.strip():
    q = st.session_state.query.strip()

    demanda_id, empresa_term, produto_text, historico_text, date_since = parse_user_message(q)

    # refine caso texto não tenha
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
        left, right = st.columns([4.8, 1.2], vertical_alignment="top")

        with left:
            if historico_final:
                st.markdown("### 🗂️ Histórico")
                st.caption("Mais recente primeiro")
            else:
                st.markdown("### 📌 Última atualização")

            st.caption(f"Consulta: {q}")

        with right:
            # ✅ VÍDEO LOOP REAL — SEM CONTROLES — SÓ NO RESULTADO
            render_loop_video(RESULT_LOOP_VIDEO, height_px=240)

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
