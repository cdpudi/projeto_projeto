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

# --- FUNÇÕES AUXILIARES ---
def conv_min(h):
    if not h or h == "" or h == "00:00":
        return 0
    try:
        h, m = h.split(":")
        return int(h) * 60 + int(m)
    except:
        return 0


# 🔥 EXTRAÇÃO FINAL (COM INTERJ PRIORITÁRIO DA COLUNA)
def extrair_dados_linha(row):
    linha = " ".join([str(c) for c in row if c])
    horarios = re.findall(r"\d{2}:\d{2}", linha)

    inicio, fim = "", ""
    diaria, refeicao, interj = "", "", ""

    # ✔ Início/Fim robusto
    if len(horarios) >= 2:
        inicio, fim = horarios[0], horarios[1]

    # 🔥 1. INTERJ DIRETO DA COLUNA (PRIORIDADE)
    for val in row:
        if val and re.match(r"\d{2}:\d{2}", str(val)):
            m = conv_min(val)
            # Interj real sempre >= 6h e <= 24h (evita pegar refeição/repouso)
            if 360 <= m <= 1440:
                interj = val

    # 🔥 2. EXTRAÇÃO INTELIGENTE RESTANTE (fallback + refeição)
    if "08:00" in horarios:
        idx = horarios.index("08:00")

        if len(horarios) > idx + 1:
            diaria = horarios[idx + 1]

        encontrou_refeicao = False

        for h in horarios[idx + 2:]:
            m = conv_min(h)

            # 🍱 Refeição
            if 30 <= m <= 150 and not encontrou_refeicao:
                refeicao = h
                encontrou_refeicao = True
                continue

            # Ignora repouso
            if encontrou_refeicao and m < 60:
                continue

            # Interj fallback (caso não venha na coluna)
            if not interj and m >= 660:
                interj = h
                break

    return inicio, fim, diaria, refeicao, interj


def auditoria_final_v10(pdf_file):
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
                if row[0] and re.match(r"^\d{2}/\d{2}/\d{2}", row[0]):

                    data_dia = row[0].split()[0]
                    tipo = str(row[1]).strip()

                    if "Trabalho" not in tipo:
                        continue

                    inicio, fim, diaria, refeicao, interj = extrair_dados_linha(row)
                    inicio_fim_valido = bool(inicio and fim)

                    # 🚨 FALTA DE LANÇAMENTO
                    if not inicio_fim_valido:
                        relatorio[nome].append(f"⚠️ {data_dia} - FALTA DE LANÇAMENTO")
                        continue

                    # 🍱 REFEIÇÃO
                    if not refeicao:
                        relatorio[nome].append(f"🍱 {data_dia} - FALTA INTERVALO REFEIÇÃO")
                    elif conv_min(refeicao) > 120:
                        relatorio[nome].append(f"🍱 {data_dia} - REFEIÇÃO EXCEDEU 2H ({refeicao})")

                    # ⏱️ INTERSTÍCIO (AGORA CORRETO)
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

with c_side:
    st.markdown(f"""
        <div class="side-info-card">
            <h3 style='color: #004a99; margin-top:0; border-bottom: 2px solid #004a99; padding-bottom: 10px;'>Proposta Selecionada</h3>
            <p style='font-size: 0.95em;'><b>Aluna:</b> RAYNARAH MALAQUIAS SOARES<br><b>ID:</b> <code>#IA-17750026</code></p>
            <h5 style='color: #004a99;'>📡 Monitoramento:</h5>
            <div class="monitoring-item">✅ Validação de Interstício (Mín. 11h)</div>
            <div class="monitoring-item">✅ Verificação de Intervalo Alimentação (Máx. 2h)</div>
            <div class="monitoring-item">✅ Auditoria de Lançamentos Inexistentes</div>
            <div style="text-align: center; margin-top: 20px;"><span class="status-badge">Sinalização: Ativa ✅</span></div>
        </div>
        """, unsafe_allow_html=True)

with c_main:
    st.subheader("📁 Auditoria de Documentos")
    up = st.file_uploader("Upload PDF", type="pdf", label_visibility="collapsed")

    if up:
        with st.status("Processando Auditoria...", expanded=False):
            res = auditoria_final_v10(up)

        if res:
            st.markdown("### 🚩 Inconsistências Identificadas")
            for mot, errs in res.items():
                if errs:
                    with st.expander(f"👤 {mot}"):
                        for e in sorted(list(set(errs))):
                            st.error(e)
                else:
                    st.success(f"👤 {mot} - Em conformidade")
        else:
            st.success("✅ Nenhuma inconsistência detectada nos dias com jornada.")

st.markdown('<div class="footer-credits"><p style="font-size: 0.8em; color: #999;">Workshop IA Aplicada | Versão Final | Status: Online</p></div>', unsafe_allow_html=True)