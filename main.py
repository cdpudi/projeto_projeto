import streamlit as st
import pdfplumber
import re

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="IA na Gestão de Processos", page_icon="🤖", layout="wide")

# --- ESTILO CSS ORIGINAL ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
    .stApp { background-color: #f4f7f6; }
    .concept-card { background: linear-gradient(135deg, #004a99 0%, #002d5f 100%); color: white; padding: 2rem; border-radius: 15px; margin-bottom: 2rem; box-shadow: 0 10px 20px rgba(0,0,0,0.1); }
    .quote-section { border-left: 4px solid #ff914d; padding-left: 15px; font-style: italic; color: #e0e0e0; margin: 15px 0; }
    .side-info-card { background-color: white; padding: 30px; border-radius: 15px; border: 1px solid #e0e0e0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 1.5rem; }
    .monitoring-item { font-size: 0.85em; color: #444; margin: 8px 0; }
    .status-badge { padding: 6px 12px; border-radius: 20px; font-size: 13px; background-color: #28a745; color: white; font-weight: bold; }
    .footer-credits { background-color: #ffffff; padding: 1rem; border-radius: 10px; border: 1px solid #e0e0e0; text-align: center; margin-top: 2rem; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÃO AUXILIAR ---
def conv_min(h):
    try:
        h, m = str(h).split(":")
        return int(h) * 60 + int(m)
    except:
        return 0


def auditoria_final(pdf_file):
    relatorio = {}

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            texto = page.extract_text()

            func_match = re.search(r"Funcionário:\s*(.*?)(?=Admissão|CPF|$)", texto)
            nome = func_match.group(1).strip() if func_match else "Desconhecido"

            if nome not in relatorio:
                relatorio[nome] = []

            table = page.extract_table()
            if not table:
                continue

            for row in table:
                if not row or not row[0]:
                    continue

                if re.match(r"^\d{2}/\d{2}/\d{2}", str(row[0])):

                    data_dia = row[0].split()[0]
                    tipo = str(row[1]).strip()

                    if "Trabalho" not in tipo:
                        continue

                    # 🔥 CAMPOS DIRETOS (SEM ADIVINHAÇÃO)
                    inicio = str(row[2]).strip() if len(row) > 2 else ""
                    fim = str(row[3]).strip() if len(row) > 3 else ""
                    refeicao = str(row[6]).strip() if len(row) > 6 else ""
                    interj = str(row[9]).strip() if len(row) > 9 else ""

                    # 🚨 FALTA DE LANÇAMENTO
                    if not inicio or not fim:
                        relatorio[nome].append(f"⚠️ {data_dia} - FALTA DE LANÇAMENTO")
                        continue

                    # 🍱 REFEIÇÃO
                    if not refeicao or refeicao == "00:00":
                        relatorio[nome].append(f"🍱 {data_dia} - FALTA INTERVALO REFEIÇÃO")
                    elif conv_min(refeicao) > 120:
                        relatorio[nome].append(f"🍱 {data_dia} - REFEIÇÃO EXCEDEU 2H ({refeicao})")

                    # ⏱️ INTERSTÍCIO (AGORA 100% CORRETO)
                    if interj:
                        m_int = conv_min(interj)

                        if 0 < m_int < 660:
                            relatorio[nome].append(f"⏱️ {data_dia} - INTERSTÍCIO REDUZIDO ({interj})")

    return relatorio


# --- LAYOUT ORIGINAL (INALTERADO) ---
col_logo, col_adm = st.columns([1, 1])

with col_logo:
    st.image("https://portalinstitucional-assets.azureedge.net/strapi/assets/Logo_Anhanguera_Horizontal_170x60px_1_d985ea5183.svg", width=220)

with col_adm:
    st.markdown("<div style='text-align: right; padding-top: 20px;'><p style='color: #004a99; font-weight: bold; margin-bottom: 0;'>Desenvolvimento e Análise</p><p style='font-size: 1.2em; color: #333;'>Prof. Cleidson Daniel</p></div>", unsafe_allow_html=True)

st.markdown("""
    <div class="concept-card">
        <h1>IA na Administração & Gestão de Processos</h1>
        <p>Workshop: Laboratório prático focado na <b>convergência entre Inteligência Artificial e gestão estratégica</b>.</p>
        <div class="quote-section">"Pensar de forma inteligente não é apenas automatizar tarefas, mas redesenhar processos para que a tecnologia potencialize o capital humano..."</div>
    </div>
""", unsafe_allow_html=True)

c_main, c_side = st.columns([2, 1.2])

with c_main:
    st.subheader("📁 Auditoria de Documentos")
    up = st.file_uploader("Upload PDF", type="pdf", label_visibility="collapsed")

    if up:
        with st.status("Processando Auditoria...", expanded=False):
            res = auditoria_final(up)

        if res:
            st.markdown("### 🚩 Inconsistências Identificadas")
            for mot, errs in res.items():
                if errs:
                    with st.expander(f"👤 {mot}"):
                        for e in sorted(set(errs)):
                            st.error(e)
                else:
                    st.success(f"👤 {mot} - Em conformidade")

st.markdown('<div class="footer-credits">Sistema de Auditoria Inteligente</div>', unsafe_allow_html=True)