import streamlit as st
import pdfplumber
import re

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="IA na Gestão de Processos", page_icon="🤖", layout="wide")

# --- CSS ORIGINAL ---
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
.stApp { background-color: #f4f7f6; }
.concept-card { background: linear-gradient(135deg, #004a99 0%, #002d5f 100%); color: white; padding: 2rem; border-radius: 15px; margin-bottom: 2rem; }
.side-info-card { background-color: white; padding: 30px; border-radius: 15px; }
.status-badge { padding: 6px 12px; border-radius: 20px; background-color: #28a745; color: white; }
</style>""", unsafe_allow_html=True)

# --- AUX ---
def conv_min(h):
    try:
        h, m = h.split(":")
        return int(h)*60 + int(m)
    except:
        return 0

# 🔥 EXTRAÇÃO REAL BASEADA NA LINHA
def extrair_linha_texto(linha):

    horarios = re.findall(r"\d{2}:\d{2}", linha)

    inicio = horarios[0] if len(horarios) > 0 else ""
    fim = horarios[1] if len(horarios) > 1 else ""

    refeicao = ""
    interj = ""

    if "08:00" in horarios:
        idx = horarios.index("08:00")

        # após jornada normal
        candidatos = horarios[idx+2:]

        for h in candidatos:
            m = conv_min(h)

            # refeição
            if 30 <= m <= 150 and not refeicao:
                refeicao = h
                continue

            # interj (>= 11h)
            if m >= 660:
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

                    # 🚨 FALTA
                    if not inicio or not fim:
                        relatorio[nome].append(f"⚠️ {data} - FALTA DE LANÇAMENTO")
                        continue

                    # 🍱 REFEIÇÃO
                    if not refeicao:
                        relatorio[nome].append(f"🍱 {data} - FALTA INTERVALO REFEIÇÃO")
                    elif conv_min(refeicao) > 120:
                        relatorio[nome].append(f"🍱 {data} - REFEIÇÃO EXCEDEU 2H ({refeicao})")

                    # ⏱️ INTERJ
                    if interj:
                        if conv_min(interj) < 660:
                            relatorio[nome].append(f"⏱️ {data} - INTERSTÍCIO REDUZIDO ({interj})")

    return relatorio

# --- LAYOUT ORIGINAL ---
col_logo, col_adm = st.columns([1,1])

with col_logo:
    st.image("https://portalinstitucional-assets.azureedge.net/strapi/assets/Logo_Anhanguera_Horizontal_170x60px_1_d985ea5183.svg", width=220)

with col_adm:
    st.markdown("<div style='text-align:right'><b>Prof. Cleidson Daniel</b></div>", unsafe_allow_html=True)

st.markdown('<div class="concept-card"><h1>IA na Administração</h1></div>', unsafe_allow_html=True)

col1, col2 = st.columns([2,1])

with col2:
    st.markdown('<div class="side-info-card">Monitoramento Ativo</div>', unsafe_allow_html=True)

with col1:
    st.subheader("📁 Auditoria de Documentos")
    up = st.file_uploader("Upload PDF", type="pdf")

    if up:
        res = auditoria(up)

        st.markdown("### 🚩 Inconsistências Identificadas")

        for mot, erros in res.items():
            with st.expander(f"👤 {mot}"):
                for e in erros:
                    st.error(e)