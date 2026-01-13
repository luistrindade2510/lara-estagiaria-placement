import re
import time
import pandas as pd
import streamlit as st

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
st.markdown(
    """
<style>
.block-container { max-width: 1100px; padding-top: 2.2rem; padding-bottom: 2rem; }

.joy-hero {
  display: flex;
  gap: 28px;
  align-items: center;
  margin-bottom: 22px;
}

.joy-video {
  width: 360px;
}

.joy-title {
  font-size: 34px;
  margin: 0 0 6px 0;
  line-height: 1.12;
}

.joy-slogan {
  color: rgba(0,0,0,.70);
  font-size: 16px;
  margin-bottom: 14px;
}

.joy-instruction {
  font-size: 17px;
  margin-bottom: 4px;
}

.joy-muted {
  color: rgba(0,0,0,.55);
  font-size: 14px;
}

.joy-card {
  border: 1px solid rgba(0,0,0,.08);
  border-radius: 18px;
  padding: 14px 16px;
  background: rgba(255,255,255,.92);
  box-shadow: 0 10px 24px rgba(0,0,0,.05);
}

.joy-chip {
  display:inline-block;
  padding: 7px 12px;
  border-radius: 999px;
  border: 1px solid rgba(0,0,0,.12);
  font-size: 13px;
  margin: 6px 8px 0 0;
  background: rgba(255,255,255,.95);
}

.joy-section-title {
  font-weight: 650;
  margin: 16px 0 8px 0;
}

.joy-divider {
  margin: 18px 0 10px 0;
  border-bottom: 1px solid rgba(0,0,0,.08);
}

.stChatInput { margin-top: 0.9rem; }

@media (max-width: 900px) {
  .joy-hero { flex-direction: column; align-items: flex-start; }
  .joy-video { width: 100%; }
}
</style>
""",
    unsafe_allow_html=True,
)

# =========================
# ARQUIVOS DE VÍDEO
# =========================
VIDEO_IDLE = "joy_idle.mp4"
VIDEO_LOADING = "joy_loading.mp4"
VIDEO_SUCCESS = "joy_success.mp4"
VIDEO_NOTFOUND = "joy_notfound.mp4"  # opcional; se não existir, cai pro idle

def safe_video(path: str):
    """Exibe vídeo sem quebrar caso não exista."""
    try:
        st.video(path)
    except Exception:
        # fallback: tenta outro
        if path != VIDEO_IDLE:
            try:
                st.video(VIDEO_IDLE)
            except Exception:
                st.write("")

# =========================
# ESTADO DO APP
# =========================
if "state" not in st.session_state:
    st.session_state.state = "idle"  # idle | loading | success | notfound

if "messages" not in st.session_state:
    st.session_state.messages = []

# =========================
# DADOS (SHEETS)
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
def load_data(url: str) -> pd.DataFrame:
    df = pd.read_csv(url)
    df.columns = [c.strip() for c in df.columns]

    # normalizações
    if COL_DATE in df.columns:
        df[COL_DATE] = pd.to_datetime(df[COL_DATE], errors="coerce", dayfirst=True)
    df[COL_ID] = df[COL_ID].astype(str).str.strip()

    # garante colunas string
    for c in [COL_EMPRESA, COL_DEMANDA, COL_PRODUTO, COL_AUTOR, COL_STATUS, COL_TEXTO]:
        if c in df.columns:
            df[c] = df[c].astype(str).fillna("").str.strip()

    return df

df = load_data(SHEETS_CSV_URL)

# =========================
# PARSE DA MENSAGEM (ID / EMPRESA / PRODUTO / HIST / DATAS)
# =========================
def parse_user_message(msg: str):
    m = msg.strip()

    # histórico
    historico = bool(re.search(r"\bhist(ó|o)rico\b|\bhist\b", m, flags=re.I))

    # produto
    produto = None
    if re.search(r"\bambos\b|\bodonto\+sa(ú|u)de\b", m, flags=re.I):
        produto = "AMBOS"
    elif re.search(r"\bodonto\b", m, flags=re.I):
        produto = "ODONTO"
    elif re.search(r"\bsa(ú|u)de\b", m, flags=re.I):
        produto = "SAÚDE"

    # datas
    # "desde 10/01/2026"
    date_since = None
    msince = re.search(r"desde\s+(\d{1,2}/\d{1,2}/\d{4})", m, flags=re.I)
    if msince:
        try:
            date_since = pd.to_datetime(msince.group(1), dayfirst=True)
        except Exception:
            date_since = None

    # "em 10/01/2026" (data exata)
    date_exact = None
    mexact = re.search(r"\bem\s+(\d{1,2}/\d{1,2}/\d{4})", m, flags=re.I)
    if mexact:
        try:
            date_exact = pd.to_datetime(mexact.group(1), dayfirst=True)
        except Exception:
            date_exact = None

    # id (primeiro número 3+ dígitos)
    mid = re.search(r"\b(\d{3,})\b", m)
    demanda_id = mid.group(1) if mid else None

    # "empresa_term": remove palavras de comando pra não atrapalhar busca
    cleaned = re.sub(r"\bhist(ó|o)rico\b|\bhist\b", "", m, flags=re.I)
    cleaned = re.sub(r"\bsa(ú|u)de\b|\bodonto\b|\bambos\b|\bodonto\+sa(ú|u)de\b", "", cleaned, flags=re.I)
    cleaned = re.sub(r"desde\s+\d{1,2}/\d{1,2}/\d{4}", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\bem\s+\d{1,2}/\d{1,2}/\d{4}", "", cleaned, flags=re.I)
    cleaned = cleaned.strip(" -|,;")

    empresa_term = None if demanda_id else cleaned.strip()
    if empresa_term == "":
        empresa_term = None

    return demanda_id, empresa_term, produto, historico, date_exact, date_since

def filter_df(
    df: pd.DataFrame,
    demanda_id=None,
    empresa_term=None,
    produto=None,
    date_exact=None,
    date_since=None,
):
    out = df.copy()

    if demanda_id:
        out = out[out[COL_ID] == str(demanda_id)]

    if empresa_term:
        term = empresa_term.lower()
        out = out[out[COL_EMPRESA].str.lower().str.contains(term, na=False)]

    # AMBOS = não filtra por produto (pega tudo)
    if produto and produto != "AMBOS":
        out = out[out[COL_PRODUTO].str.lower().str.contains(produto.lower(), na=False)]

    if date_exact is not None:
        out = out[out[COL_DATE].dt.date == date_exact.date()]

    if date_since is not None:
        out = out[out[COL_DATE] >= date_since]

    out = out.sort_values(by=COL_DATE, ascending=False)
    return out

# =========================
# RENDERERS
# =========================
def render_last_update(row: pd.Series):
    d = row[COL_DATE]
    d_str = d.strftime("%d/%m/%Y") if pd.notna(d) else "—"

    st.markdown('<div class="joy-card">', unsafe_allow_html=True)
    st.markdown("**📌 Última atualização**")
    st.markdown(f"- **ID:** {row[COL_ID]}")
    st.markdown(f"- **Empresa:** {row[COL_EMPRESA]}")
    st.markdown(f"- **Demanda:** {row[COL_DEMANDA]}")
    st.markdown(f"- **Produto:** {row[COL_PRODUTO]}")
    st.markdown(f"- **Status:** {row[COL_STATUS]}")
    st.markdown(f"- **Data:** {d_str}")
    st.markdown(f"- **Autor:** {row[COL_AUTOR]}")
    st.markdown(f"**Resumo:** {row[COL_TEXTO]}")
    st.markdown("</div>", unsafe_allow_html=True)

def render_history(df_hist: pd.DataFrame):
    view = df_hist[[COL_DATE, COL_STATUS, COL_PRODUTO, COL_AUTOR, COL_TEXTO]].copy()
    view[COL_DATE] = view[COL_DATE].dt.strftime("%d/%m/%Y")
    view = view.rename(columns={
        COL_DATE: "Data",
        COL_STATUS: "Status",
        COL_PRODUTO: "Produto",
        COL_AUTOR: "Autor",
        COL_TEXTO: "Atualização",
    })
    st.markdown("**🗂️ Histórico (mais recente primeiro):**")
    st.dataframe(view, use_container_width=True, hide_index=True)

# =========================
# HERO (VÍDEO + TEXTO)
# =========================
st.markdown('<div class="joy-hero">', unsafe_allow_html=True)

st.markdown('<div class="joy-video">', unsafe_allow_html=True)
if st.session_state.state == "idle":
    safe_video(VIDEO_IDLE)
elif st.session_state.state == "loading":
    safe_video(VIDEO_LOADING)
elif st.session_state.state == "success":
    safe_video(VIDEO_SUCCESS)
elif st.session_state.state == "notfound":
    safe_video(VIDEO_NOTFOUND)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    """
<div>
  <div class="joy-title">💬 JOY – Assistente Placement Jr</div>
  <div class="joy-slogan">Status, histórico e andamento dos estudos — sem depender de mensagens no Teams.</div>
  <div class="joy-instruction"><b>Consulte estudos de Placement com clareza e rapidez.</b></div>
  <div class="joy-muted">Digite o código da demanda ou o nome da empresa para começar.</div>

  <div class="joy-divider"></div>

  <div class="joy-muted" style="margin-bottom: 6px;"><b>Consultas comuns</b></div>
  <span class="joy-chip">6163</span>
  <span class="joy-chip">6163 histórico</span>
  <span class="joy-chip">Leadec</span>
  <span class="joy-chip">Leadec saúde</span>
  <span class="joy-chip">Leadec odonto</span>
  <span class="joy-chip">Leadec desde 10/01/2026</span>
</div>
""",
    unsafe_allow_html=True
)

st.markdown("</div>", unsafe_allow_html=True)

# =========================
# FILTROS RÁPIDOS (UX)
# =========================
st.markdown('<div class="joy-section-title">🎛️ Refine sua consulta</div>', unsafe_allow_html=True)
st.markdown('<div class="joy-muted">Use os filtros abaixo ou digite tudo direto (ex: "6163 histórico saúde").</div>', unsafe_allow_html=True)

if "quick_produto" not in st.session_state:
    st.session_state.quick_produto = None
if "quick_hist" not in st.session_state:
    st.session_state.quick_hist = False

f1, f2, f3 = st.columns([1.2, 1.8, 2.0])

with f1:
    if st.button("🧽 Limpar", use_container_width=True):
        st.session_state.quick_produto = None
        st.session_state.quick_hist = False

with f2:
    label = "🗂️ Modo: Última" if not st.session_state.quick_hist else "✅ Modo: Histórico"
    if st.button(label, use_container_width=True):
        st.session_state.quick_hist = not st.session_state.quick_hist

with f3:
    st.write("")

p1, p2, p3, p4 = st.columns(4)
with p1:
    if st.button("🩺 Saúde", use_container_width=True):
        st.session_state.quick_produto = "SAÚDE"
with p2:
    if st.button("🦷 Odonto", use_container_width=True):
        st.session_state.quick_produto = "ODONTO"
with p3:
    if st.button("🩺+🦷 Ambos", use_container_width=True):
        st.session_state.quick_produto = "AMBOS"
with p4:
    if st.button("🚫 Sem produto", use_container_width=True):
        st.session_state.quick_produto = None

prod_txt = st.session_state.quick_produto if st.session_state.quick_produto else "—"
modo_txt = "Histórico" if st.session_state.quick_hist else "Última atualização"
st.markdown(
    f"""
<div class="joy-card" style="margin-top:10px;">
<b>Consulta atual</b><br>
<span class="joy-chip">Produto: {prod_txt}</span>
<span class="joy-chip">Modo: {modo_txt}</span>
</div>
""",
    unsafe_allow_html=True
)

# =========================
# CHAT
# =========================
# Render histórico do chat
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Placeholder inteligente (mostra filtros ativos)
hint_parts = []
if st.session_state.quick_produto:
    hint_parts.append(f"produto={st.session_state.quick_produto.lower()}")
hint_parts.append("modo=histórico" if st.session_state.quick_hist else "modo=última")
hint_txt = " | ".join(hint_parts)

user_msg = st.chat_input(
    f"Digite a demanda (ID) ou empresa — {hint_txt}. Ex.: 6163 | Leadec | Leadec desde 10/01/2026"
)

if user_msg:
    # mostra mensagem do usuário
    st.session_state.messages.append({"role": "user", "content": user_msg})
    with st.chat_message("user"):
        st.markdown(user_msg)

    # prepara estado "loading"
    st.session_state.state = "loading"
    # dá tempo do usuário perceber (e o vídeo trocar)
    time.sleep(0.6)

    demanda_id, empresa_term, produto, historico, date_exact, date_since = parse_user_message(user_msg)

    # aplica filtros rápidos caso não tenha sido informado no texto
    if not produto and st.session_state.quick_produto:
        produto = st.session_state.quick_produto
    if not historico and st.session_state.quick_hist:
        historico = True

    result = filter_df(df, demanda_id, empresa_term, produto, date_exact, date_since)

    with st.chat_message("assistant"):
        if result.empty:
            st.session_state.state = "notfound"
            st.markdown(
                "Não encontrei nenhum estudo com esses critérios 😅\n\n"
                "Tenta assim:\n"
                "- só o **ID** (ex: **6163**)\n"
                "- ou só parte do nome da empresa (ex: **Leadec**)\n"
                "- ou adiciona **saúde / odonto** pra refinar"
            )
        else:
            st.session_state.state = "success"
            if historico:
                render_history(result)
            else:
                render_last_update(result.iloc[0])

            st.markdown('<div class="joy-muted" style="margin-top:10px;">Se quiser, peça <b>histórico</b> (ex: "6163 histórico").</div>', unsafe_allow_html=True)

    # salva resposta no histórico
    # (não duplicamos o conteúdo renderizado porque já apareceu visualmente)
    st.session_state.messages.append({"role": "assistant", "content": "✅ Consulta concluída."})
