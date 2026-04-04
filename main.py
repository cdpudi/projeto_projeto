import streamlit as st
import pdfplumber
import re

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="IA na Gestão de Processos", page_icon="🤖", layout="wide")

# --- CSS ORIGINAL (NÃO ALTERADO) ---
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

# --- AUXILIAR ---
def conv_min(h):
    try:
        h, m = h.split(":")
        return int(h) * 60 + int(m)
    except:
        return 0


# 🔥 EXTRAÇÃO FINAL CORRIGIDA (INTERJ DEFINITIVO)
def extrair_linha_texto(linha):

    horarios = re.findall(r"\d{2}:\d{2}", linha)

    inicio = horarios[0] if len(horarios) > 0 else ""
    fim = horarios[1] if len(horarios) > 1 else ""

    refeicao = ""
    interj = ""

    if "08:00" in horarios:
        idx = horarios.index("08:00")

        pos = idx + 2

        while pos < len(horarios):
            h = horarios[pos]
            m = conv_min(h)

            # 🍱 refeição
            if not refeicao and 30 <= m <= 150:
                refeicao = h
                pos += 1
                continue

            # ⛔ ignorar repouso
            if m <= 120:
                pos += 1
                continue

            # 🎯 INTERJ REAL
            interj = h
            break

    return inicio, fim, refeicao, interj


def auditoria(pdf_file):
    relatorio = {}

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:

            texto = page.extract_text()

            nome_match = re.search(r"Funcionário:\s*(.*?)(?=Admissão|CPF|$)", texto)
            nome = nome_match.group(1).strip() if nome_match else "Desconhecido"

            if nome not in relatorio:
                relatorio[nome] = []

            linhas = texto.split("\n")

            for linha in linhas:

                if re.match(r"\d{2}/\d{2}/\d{2}", linha) and "Trabalho" in linha:

                    data = linha.split()[0]

                    inicio, fim, refeicao, interj = extrair_linha_texto(linha)

                    # 🚨 FALTA DE LANÇAMENTO
                    if not inicio or not fim:
                        relatorio[nome].append(f"⚠️ {data} - FALTA DE LANÇAMENTO")
                        continue

                    # 🍱 REFEIÇÃO
                    if not refeicao:
                        relatorio[nome].append(f"🍱 {data} - FALTA INTERVALO REFEIÇÃO")
                    elif conv_min(refeicao) > 120:
                        relatorio[nome].append(f"🍱 {data} - REFEIÇÃO EXCEDEU 2H ({refeicao})")

                    # ⏱️ INTERSTÍCIO
                    if interj:
                        if conv_min(interj) < 660:
                            relatorio[nome].append(f"⏱️ {data} - INTERSTÍCIO REDUZIDO ({interj})")

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
        <div class="quote-section">"Pensar de forma inteligente não é apenas automatizar tarefas, mas redesenhar processos..."</div>
    </div>
""", unsafe_allow_html=True)

c_main, c_side = st.columns([2, 1.2])

with c_side:
    st.markdown(f"""
        <div class="side-info-card">
            <h3 style='color: #004a99;'>Proposta Selecionada</h3>
            <p><b>Aluna:</b> RAYNARAH MALAQUIAS SOARES</p>
            <h5>📡 Monitoramento:</h5>
            <div class="monitoring-item">✅ Interstício</div>
            <div class="monitoring-item">✅ Refeição</div>
            <div class="monitoring-item">✅ Lançamentos</div>
            <div style="text-align: center; margin-top: 20px;"><span class="status-badge">Ativo</span></div>
        </div>
    """, unsafe_allow_html=True)

with c_main:
    st.subheader("📁 Auditoria de Documentos")
    up = st.file_uploader("Upload PDF", type="pdf", label_visibility="collapsed")

    if up:
        with st.status("Processando Auditoria...", expanded=False):
            res = auditoria(up)

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