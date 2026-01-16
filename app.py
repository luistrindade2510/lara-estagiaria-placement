/* ====== FIX: some a faixa/linha clara do bloco do video (coluna esquerda) ====== */
[data-testid="stColumn"]{
  background: transparent !important;
}

.lara-video-wrap{
  background: #ffffff !important;   /* branco puro */
  border: 0 !important;
  outline: 0 !important;
  box-shadow: none !important;
  overflow: hidden !important;
  border-radius: 0 !important;
}

/* CROP MAIS FORTE pra matar qualquer linha do MP4 */
.lara-video{
  background: #ffffff !important;
  border: 0 !important;
  outline: 0 !important;
  box-shadow: none !important;

  transform: scale(1.06) !important;   /* antes 1.03 */
  transform-origin: center center !important;
  margin: -4px !important;             /* antes -2px */
}

/* Streamlit às vezes coloca uma "linha" via hr/divs internos */
hr, .stDivider{
  display:none !important;
}
