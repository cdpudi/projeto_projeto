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

# --- ESTILO CSS AVANÇADO (MANTIDO) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
    .stApp { background-color: #f4f7f6; }
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
    .side-info-card {
        background-color: white;
        padding: 30px;
        border-radius: 15px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 1.5rem;
    }
    .monitoring-item { font-size: 0.85em; color: #444; margin: 8px 0; }
    .footer-credits {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        text-align: center;
        margin-top: 2rem;
    }
    .status-badge {
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 13px;
        background-color: #28a745;
        color: white;
        font-weight: bold;
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
                    
                    # 1. Regra de Lançamento Início/Fim
                    if len(horarios) < 3:
                        erros.append(f"⚠️ {data_dia} - FALTA DE LANÇAMENTO (Início/Fim)")
                    
                    # 2. Regra de Intervalo de Alimentação (Refeição)
                    # No PDF Transpedrosa: Início(2), Fim(3), J.Normal(4), J.Diária(5), Refeição(6)
                    # Nota: O regex extrai todos os HH:MM. Precisamos validar a posição.
                    if len(horarios) >= 5:
                        # Pegamos o valor da Jornada Normal (geralmente 08:00)
                        minutos_normal = converter_para_minutos(horarios[2]) if len(horarios) > 2 else 0
                        
                        # Localizamos o valor da Refeição (Coluna 6 no layout original)
                        # Como o PDF extrai texto corrido, buscamos o valor após a jornada diária
                        # Para o Marcelo Wender (01/04), a refeição está vazia
                        refeicao_str = ""
                        # Se a linha tem 'Trabalho' mas não tem o horário de refeição preenchido
                        # ou se o valor extraído na posição de refeição for 00:00
                        if minutos_normal > 360: # Maior que 6 horas
                             # Verificamos se há valor de refeição na linha
                             # No texto extraído, se não houver refeição, o número de horários diminui
                             if len(horarios) < 6:
                                 erros.append(f"🍱 {data_dia} - FALTA INTERVALO REFEIÇÃO (Jornada > 6h)")
                             else:
                                 # Se existe o horário, validamos se é > 2h
                                 # A refeição costuma ser o 5º ou 6º horário encontrado
                                 min_ref = converter_para_minutos(horarios[4]) 
                                 if min_ref > 120:
                                     erros.append(f"🍱 {data_dia} - INTERVALO REFEIÇÃO EXCEDEU 2H ({horarios[4]})")

                    # 3. Regra Interstício
                    if "Interj" in linha:
                        for p in partes:
                            if ":" in p:
                                min_p = converter_para_minutos(p)
                                if 0 < min_p < 660 and p != "08:00" and p not in horarios[:3]:
                                    if partes.index(p) > 6: 
                                        erros.append(f"⏱️ {data_dia} - INTERSTÍCIO REDUZIDO ({p})")
                
                if erros:
                    relatorio_final[motorista_atual].extend(list(set(erros)))
    return relatorio_final

# --- INTERFACE (LAYOUT MANTIDO) ---

header_col1, header_col2 = st.columns([1, 1])
with header_col1:
    st.image("https://portalinstitucional-assets.azureedge.net/strapi/assets/Logo_Anhanguera_Horizontal_170x60px_1_d985ea5183.svg", width=220)
with header_col2:
    st.markdown("""<div style='text-align: right; padding-top: 20px;'>
                <p style='margin-bottom: 0; color: #004a99; font-weight: bold;'>Desenvolvimento e Análise</p>
                <p style='font-size: 1.2em; color: #333;'>Prof. Cleidson Daniel</p>
                </div>""", unsafe_allow_html=True)

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

col_main, col_side = st.columns([2, 1.2])

with col_side:
    st.markdown(f"""
        <div class="side-info-card">
            <h3 style='color: #004a99; margin-top:0; border-bottom: 2px solid #004a99; padding-bottom: 10px;'>
                Proposta Selecionada
            </h3>
            <p style='font-size: 0.95em; color: #333; margin-top: 20px;'>
                <b>Aluna:</b> RAYNARAH MALAQUIAS SOARES<br>
                <b>ID:</b> <code>#IA-17750026</code><br>
                <b>Setor:</b> Recursos Humanos (RH)
            </p>
            <br>
            <h5 style='color: #004a99; margin-bottom: 15px;'>📡 Monitoramento de Processos:</h5>
            <div class="monitoring-item">✅ Validação de Interstício (11h)</div>
            <div class="monitoring-item">✅ Verificação de Intervalo Alimentação</div>
            <div class="monitoring-item">✅ Auditoria de Jornada Diária</div>
            <br>
            <div style="text-align: center; margin-top: 15px;">
                <span class="status-badge">Sistema: ONLINE ✅</span>
            </div>
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

st.markdown("""
    <div class="footer-credits">
        <p style='margin-bottom:0; font-size: 0.8em; color: #999;'>
            Workshop de IA Aplicada | Versão IA-Processos 1.0 | Status: Sistema Operacional Online
        </p>
    </div>
    """, unsafe_allow_html=True)