import streamlit as st
import pdfplumber
import re
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="IA na Gestão de Processos - Auditoria",
    page_icon="⚖️",
    layout="wide"
)

# --- ESTILO CSS ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #004a99; color: white; }
    .report-card { background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .aluna-box { background-color: #e3f2fd; padding: 15px; border-radius: 8px; border-left: 5px solid #007bff; font-family: 'sans-serif'; }
    .prof-credito { font-size: 0.9em; color: #555; font-style: italic; text-align: right; }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE AUDITORIA ---
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
                # 1. Identifica Motorista
                if "Funcionário:" in linha:
                    motorista_atual = linha.split("Funcionário:")[1].split("Admissão:")[0].strip()
                    if motorista_atual not in relatorio_final:
                        relatorio_final[motorista_atual] = []
                    continue
                
                # 2. Ignora linhas de resumo
                if "TT HS" in linha or "Resumo" in linha:
                    continue
                
                # 3. Processa linha de data
                partes = linha.split()
                if not partes or not regex_data.match(partes[0]):
                    continue

                data_dia = partes[0]
                erros = []
                
                # Regra: Dia de Trabalho
                if "Trabalho" in linha:
                    # Buscamos horários no formato HH:MM
                    horarios = re.findall(r"\d{2}:\d{2}", linha)
                    
                    # CORREÇÃO DEFINITIVA: Falta de lançamento (Dia 03/03)
                    # No dia 03/03 do Bruno, a linha tem apenas o 08:00 de faltas.
                    # Dias normais de trabalho têm Início, Fim e Jornada (pelo menos 3 horários)
                    if len(horarios) < 3:
                        erros.append(f"{data_dia} - FALTA DE LANÇAMENTO (Início/Fim não registrados)")
                    
                    # CORREÇÃO INTERSTÍCIO: 
                    # O interstício no seu PDF é o valor que fica na 9ª coluna (após faltas)
                    # Ao dar split(), ele costuma ser um dos últimos itens se houver irregularidade.
                    if "Interj" in linha:
                        # Pegamos o valor específico de interstício. 
                        # No PDF da Transpedrosa, quando há erro, o valor aparece isolado.
                        for p in partes:
                            if ":" in p:
                                min_p = converter_para_minutos(p)
                                # Somente alerta se o valor for especificamente de interstício (<11h) 
                                # e não for o 08:00 padrão da jornada.
                                if 0 < min_p < 660 and p != "08:00" and p != horarios[0]:
                                    # Verificação extra para não pegar a refeição (que costuma ser a 6ª parte)
                                    if partes.index(p) > 6: 
                                        erros.append(f"{data_dia} - INTERSTÍCIO MENOR QUE 11H ({p})")

                if erros:
                    relatorio_final[motorista_atual].extend(list(set(erros)))
    return relatorio_final

# --- INTERFACE ---

# Cabeçalho
col1, col2 = st.columns([1, 4])
with col1:
    st.image("https://portalinstitucional-assets.azureedge.net/strapi/assets/Logo_Anhanguera_Horizontal_170x60px_1_d985ea5183.svg", width=180)
with col2:
    st.title("Workshop: IA na Administração & Gestão de Processos")
    st.markdown('<p class="prof-credito">Desenvolvimento e Análise: Professor Cleidson Daniel</p>', unsafe_allow_html=True)

st.divider()

# Informações do Projeto (Conforme solicitado)
st.markdown(f"""
    <div class="aluna-box">
        <strong>📌 Laboratório Prático: Convergência entre IA e Gestão Estratégica</strong><br>
        Sugestão da aluna: <b>RAYNARAH MALAQUIAS SOARES</b> | ID: <code>#IA-17750026</code> | Setor: RH<br><br>
        <i>"Pensar de forma inteligente não é apenas automatizar tarefas, mas redesenhar processos para que a tecnologia potencialize o capital humano, eliminando erros e acelerando a tomada de decisão."</i>
    </div>
    <br>
    <p>Este workshop foca na identificação de gargalos operacionais e no desenho de soluções automatizadas para elevar a produtividade acadêmica e corporativa.</p>
    """, unsafe_allow_html=True)

# Upload
with st.container():
    st.markdown('<div class="report-card">', unsafe_allow_html=True)
    st.subheader("📁 Análise de Espelho de Ponto")
    uploaded_file = st.file_uploader("Arraste o PDF para validar conformidade", type="pdf")
    st.markdown('</div>', unsafe_allow_html=True)

if uploaded_file:
    with st.spinner("IA processando dados..."):
        resultado = processar_auditoria(uploaded_file)
    
    if resultado:
        st.subheader("🚩 Relatório de Irregularidades")
        txt_out = "AUDITORIA DE PROCESSOS IA - RETORNO\n" + "="*50 + "\n"
        
        for motorista, erros in resultado.items():
            if erros:
                with st.expander(f"👤 Motorista: {motorista}"):
                    for erro in sorted(erros):
                        st.error(erro)
                        txt_out += f"{motorista} | {erro}\n"
        
        st.download_button("📄 Baixar Relatório Completo (.txt)", txt_out, "auditoria.txt")
    else:
        st.balloons()
        st.success("✅ Nenhuma irregularidade encontrada nos critérios de Interstício e Lançamento.")

# Rodapé
st.divider()
c1, c2, c3 = st.columns(3)
with c1: st.caption("Status: Sistema Operacional")
with c2: st.caption("Sinalização: Ativa ✅")
with c3: st.caption("Versão: IA-Processos 1.0")