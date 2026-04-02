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

# --- ESTILO CSS PARA LAYOUT PROFISSIONAL ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #004a99; color: white; }
    .report-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .aluna-box {
        background-color: #e3f2fd;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #007bff;
        font-family: 'sans-serif';
    }
    .prof-credito {
        font-size: 0.9em;
        color: #555;
        font-style: italic;
        text-align: right;
    }
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
    regex_data = re.compile(r"(\d{2}/\d{2}/\d{2})")
    
    with pdfplumber.open(pdf_file) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if not texto: continue
            
            linhas = texto.split('\n')
            motorista_atual = "Desconhecido"
            
            for linha in linhas:
                if "Funcionário:" in linha:
                    motorista_atual = linha.split("Funcionário:")[1].split("Admissão:")[0].strip()
                    if motorista_atual not in relatorio_final:
                        relatorio_final[motorista_atual] = []
                    continue
                
                if "TT HS" in linha: continue
                
                match_data = regex_data.match(linha)
                if match_data:
                    data_dia = match_data.group(1)
                    erros = []
                    
                    # Extração de Horários da Linha
                    horarios = re.findall(r"\d{2}:\d{2}", linha)
                    
                    # 1. Regra de Lançamento (Dia de Trabalho sem batidas)
                    if "Trabalho" in linha and len(horarios) < 3:
                        erros.append(f"{data_dia} - FALTA DE LANÇAMENTO (Início/Fim não registrados)")
                    
                    # 2. Regra de Interstício < 11h
                    # Analisamos se algum valor na linha (que não seja jornada padrão) é < 11:00
                    # Na V10, focamos no campo que o PDF já calculou como irregular
                    for h in horarios:
                        minutos = converter_para_minutos(h)
                        if 0 < minutos < 660 and h != "08:00":
                            # Verifica se o PDF marcou como Interj na linha
                            if "Interj" in linha or len(horarios) > 5:
                                # Pegamos o último valor de tempo da linha para o interstício
                                if h == horarios[-1]:
                                    erros.append(f"{data_dia} - INTERSTÍCIO MENOR QUE 11H ({h})")
                    
                    # 3. Regra de Refeição (Jornada > 6h)
                    # Se houver um valor de jornada diária > 06:00 e o campo refeição for 00:00
                    if len(horarios) >= 5:
                        j_diaria = horarios[3] if len(horarios) > 3 else "00:00"
                        refeicao = horarios[4] if len(horarios) > 4 else "00:00"
                        if converter_para_minutos(j_diaria) > 360 and converter_para_minutos(refeicao) == 0:
                             erros.append(f"{data_dia} - FALTA LANÇAMENTO REFEIÇÃO")

                    if erros:
                        relatorio_final[motorista_atual].extend(list(set(erros)))
    return relatorio_final

# --- INTERFACE ---

# Topo: Logo e Título
col1, col2 = st.columns([1, 4])
with col1:
    st.image("https://portalinstitucional-assets.azureedge.net/strapi/assets/Logo_Anhanguera_Horizontal_170x60px_1_d985ea5183.svg", width=180)
with col2:
    st.title("Workshop: IA na Administração & Gestão de Processos")
    st.markdown('<p class="prof-credito">Desenvolvimento e Análise: Professor Cleidson Daniel</p>', unsafe_allow_html=True)

st.divider()

# Bloco Acadêmico
st.markdown(f"""
    <div class="aluna-box">
        <strong>💡 Proposta de Automação Estratégica</strong><br>
        Sugestão da aluna: <b>RAYNARAH MALAQUIAS SOARES</b> | ID: <code>#IA-17750026</code> | Setor de Aplicação Recursos Humanos (RH)<br>
        <i>"Pensar de forma inteligente não é apenas automatizar tarefas, mas redesenhar processos para que a tecnologia potencialize o capital humano."</i>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# Área de Upload
with st.container():
    st.markdown('<div class="report-card">', unsafe_allow_html=True)
    st.subheader("📁 Upload para Auditoria")
    uploaded_file = st.file_uploader("Selecione o Espelho de Ponto (PDF)", type="pdf")
    st.markdown('</div>', unsafe_allow_html=True)

if uploaded_file:
    with st.spinner("IA processando dados e validando conformidade..."):
        resultado = processar_auditoria(uploaded_file)
    
    if resultado:
        st.subheader("🚩 Inconsistências Detectadas")
        
        # Gerar TXT para exibição e download
        txt_content = "RELATÓRIO DE AUDITORIA - GESTÃO DE PROCESSOS IA\n" + "="*50 + "\n"
        for motorista, erros in resultado.items():
            if erros:
                with st.expander(f"👤 Motorista: {motorista}"):
                    for erro in sorted(erros):
                        st.error(erro)
                        txt_content += f"{motorista} | {erro}\n"
        
        st.divider()
        st.download_button(
            label="📄 Baixar Relatório Completo (.txt)",
            data=txt_content,
            file_name="auditoria_anhanguera_ia.txt",
            mime="text/plain"
        )
    else:
        st.balloons()
        st.success("✅ Auditoria Concluída: Nenhuma irregularidade encontrada nos padrões selecionados.")

# Rodapé de Sinalização
st.divider()
c1, c2, c3 = st.columns(3)
with c1: st.caption("Status: Sistema Operacional")
with c2: st.caption("Sinalização: Ativa ✅")
with c3: st.caption("Versão: IA-Processos 1.0")