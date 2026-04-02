import streamlit as st
import pdfplumber
import re
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="IA na Gestão de Processos",
    page_icon="🤖",
    layout="wide"
)

# --- ESTILO CSS AVANÇADO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
    
    .stApp { background-color: #f4f7f6; }
    
    /* Card de Metodologia */
    .concept-card {
        background: linear-gradient(135deg, #004a99 0%, #002d5f 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    
    .quote-section {
        border-left: 4px solid #ff914d;
        padding-left: 15px;
        font-style: italic;
        color: #e0e0e0;
        margin: 15px 0;
    }

    /* Estilo para créditos */
    .footer-credits {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        text-align: center;
        margin-top: 2rem;
    }

    .status-badge {
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        background-color: #28a745;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE APOIO ---
def converter_para_minutos(hora_str):
    if not hora_str: return 0
    match = re.search(r"(\d{1,2}:\d{2})", str(hora_str))
    if match:
        h, m = map(int, match.group(1).split(':'))
        return h * 60 + m
    return 0

def processar_auditoria(pdf_file):
    relatorio_final = {}
    regex_data = re.compile(r"^(\d{2}/\d{2}/\d{2})")
    with pdfplumber.open(pdf_file) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if not texto: continue
            linhas = texto.split('\n')
            motorista_atual = "Desconhecido"
            for linha in linhas:
                if "Funcionário:" in linha:
                    motorista_atual = linha.split("Funcionário:")[1].split("Admissão:")[0].strip()
                    if motorista_atual not in relatorio_final: relatorio_final[motorista_atual] = []
                    continue
                if "TT HS" in linha: continue
                partes = linha.split()
                if not partes or not regex_data.match(partes[0]): continue
                data_dia = partes[0]
                erros = []
                if "Trabalho" in linha:
                    horarios = re.findall(r"\d{2}:\d{2}", linha)
                    # Regra de Lançamento (Dia 03/03 Bruno)
                    if len(horarios) < 3:
                        erros.append(f"⚠️ {data_dia} - FALTA DE LANÇAMENTO (Início/Fim)")
                    # Regra Interstício
                    if "Interj" in linha:
                        for p in partes:
                            if ":" in p:
                                min_p = converter_para_minutos(p)
                                if 0 < min_p < 660 and p != "08:00" and p != (horarios[0] if horarios else ""):
                                    if partes.index(p) > 6: 
                                        erros.append(f"⏱️ {data_dia} - INTERSTÍCIO REDUZIDO ({p})")
                if erros:
                    relatorio_final[motorista_atual].extend(list(set(erros)))
    return relatorio_final

# --- INTERFACE ---

# Coluna de Cabeçalho (Logo + Créditos do Professor)
header_col1, header_col2 = st.columns([1, 1])
with header_col1:
    st.image("https://portalinstitucional-assets.azureedge.net/strapi/assets/Logo_Anhanguera_Horizontal_170x60px_1_d985ea5183.svg", width=220)
with header_col2:
    st.markdown("""<div style='text-align: right; padding-top: 20px;'>
                <p style='margin-bottom: 0; color: #004a99; font-weight: bold;'>Desenvolvimento e Análise</p>
                <p style='font-size: 1.2em; color: #333;'>Prof. Cleidson Daniel</p>
                </div>""", unsafe_allow_html=True)

# Card de Conceito IA
st.markdown("""
    <div class="concept-card">
        <h1 style='margin-top:0;'>IA na Administração & Gestão de Processos</h1>
        <p>Workshop: Laboratório prático focado na <b>convergência entre Inteligência Artificial e gestão estratégica</b>. 
        O objetivo é identificar gargalos operacionais reais e desenhar soluções automatizadas que elevem a produtividade acadêmica e corporativa.</p>
        <div class="quote-section">
            "Pensar de forma inteligente não é apenas automatizar tarefas, mas redesenhar processos para que a tecnologia potencialize o capital humano, eliminando erros e acelerando a tomada de decisão."
        </div>
    </div>
    """, unsafe_allow_html=True)

# Grid Lateral para Informações da Aluna e Status
col_main, col_side = st.columns([2, 1])

with col_side:
    st.markdown(f"""
        <div style="background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #e0e0e0;">
            <h4 style='color: #004a99; margin-top:0;'>💡 Proposta Selecionada</h4>
            <p style='font-size: 0.9em;'><b>Aluna:</b> RAYNARAH MALAQUIAS SOARES<br>
            <b>ID:</b> <code>#IA-17750026</code><br>
            <b>Setor:</b> Recursos Humanos (RH)</p>
            <hr>
            <p style='font-size: 0.8em; color: #666;'><b>Monitoramento de Processos:</b><br>
            - Validação de Interstício (11h)<br>
            - Verificação de Batidas Reais<br>
            - Auditoria de Jornada Diária</p>
            <span class="status-badge">Sinalização: Ativa ✅</span>
        </div>
        """, unsafe_allow_html=True)

with col_main:
    st.subheader("📁 Auditoria de Documentos")
    uploaded_file = st.file_uploader("Upload do Espelho de Ponto (PDF)", type="pdf", label_visibility="collapsed")
    
    if uploaded_file:
        with st.status("IA Analisando Processos...", expanded=False) as status:
            resultado = processar_auditoria(uploaded_file)
            status.update(label="Análise de Conformidade Finalizada!", state="complete")
        
        if resultado:
            st.markdown("### 🚩 Inconsistências Identificadas")
            txt_output = "RELATÓRIO DE AUDITORIA ESTRATÉGICA - IA\n" + "="*50 + "\n"
            
            for motorista, erros in resultado.items():
                if erros:
                    with st.expander(f"👤 {motorista}"):
                        for erro in sorted(erros):
                            st.error(erro)
                            txt_output += f"{motorista} | {erro}\n"
            
            st.download_button("💾 Exportar Relatório para Gestão (.txt)", txt_output, "auditoria_ia.txt")
        else:
            st.balloons()
            st.success("✅ Nenhuma inconsistência detectada nos processos auditados.")

# Footer Final
st.markdown("""
    <div class="footer-credits">
        <p style='margin-bottom:0; font-size: 0.8em; color: #999;'>
            Workshop de IA Aplicada | Versão IA-Processos 1.0 | Status: Sistema Operacional Online
        </p>
    </div>
    """, unsafe_allow_html=True)