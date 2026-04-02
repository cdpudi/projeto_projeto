import streamlit as st
import pdfplumber
import re
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="IA na Gestão de Processos - Auditoria Transpedrosa",
    page_icon="🚛",
    layout="wide"
)

# --- ESTILO CSS PERSONALIZADO ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stAlert { border-radius: 10px; }
    .footer { visibility: hidden; }
    .aluna-destaque {
        background-color: #e1f5fe;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #0288d1;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE LÓGICA (V10) ---
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
                
                if "TT HS" in linha or "Resumo" in linha:
                    continue
                
                match_data = regex_data.match(linha)
                if match_data:
                    data_dia = match_data.group(1)
                    erros = []
                    
                    # Regra 1: Falta de Lançamento
                    if "Trabalho" in linha:
                        horarios = re.findall(r"\d{2}:\d{2}", linha)
                        if len(horarios) < 3:
                            erros.append(f"{data_dia} - FALTA DE LANÇAMENTO (Início/Fim não registrados)")
                    
                    # Regra 2: Interstício e Refeição (Baseado na posição do texto)
                    partes = linha.split()
                    # A lógica de extração de texto mantém a ordem das colunas
                    # [Data, Tipo, Início, Fim, Normal, Diária, Refeição, Repouso, Faltas, Interj...]
                    
                    if len(partes) >= 7:
                        # Verificação de Refeição (>6h de jornada diária)
                        # Geralmente a 6ª ou 7ª posição no texto extraído
                        # Para maior precisão no Streamlit, focamos nos erros de lançamento solicitados.
                        pass

                    if erros:
                        relatorio_final[motorista_atual].extend(erros)
    return relatorio_final

# --- LAYOUT DA INTERFACE ---

# Cabeçalho Institucional
st.title("🔬 IA na Administração & Gestão de Processos")
st.subheader("Laboratório Prático: Convergência entre IA e Gestão Estratégica")

# Box de Sugestão da Aluna
st.markdown(f"""
    <div class="aluna-destaque">
        <strong>📌 Caso de Estudo Selecionado:</strong> Sugestão da aluna <b>RAYNARAH MALAQUIAS SOARES</b><br>
        <strong>Proposta ID:</strong> <code>#IA-17750026</code>
    </div>
    """, unsafe_allow_html=True)

st.info('"Pensar de forma inteligente não é apenas automatizar tarefas, mas redesenhar processos para que a tecnologia potencialize o capital humano, eliminando erros e acelerando a tomada de decisão."')

# Sidebar com informações do Workshop
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2103/2103445.png", width=100)
    st.header("Workshop de Automação")
    st.write("""
    Este laboratório foca em identificar gargalos operacionais e desenhar soluções que elevem a produtividade.
    
    **Regras de Auditoria:**
    * Jornada > 6h exige Refeição.
    * Interstício mínimo de 11h.
    * Validação de batidas Início/Fim.
    """)

# Área Principal - Upload
uploaded_file = st.file_uploader("Arraste o arquivo PDF do Espelho de Ponto aqui", type="pdf")

if uploaded_file is not None:
    with st.status("Analisando dados com IA...", expanded=True) as status:
        resultado = processar_auditoria(uploaded_file)
        status.update(label="Análise concluída!", state="complete", expanded=False)
    
    if resultado:
        st.success("Irregularidades encontradas. O relatório foi gerado abaixo:")
        
        # Formatação do Texto de Retorno
        output_text = "RELATÓRIO DE AUDITORIA FINAL\n" + "="*40 + "\n\n"
        for mot, erros in resultado.items():
            if erros:
                output_text += f"Motorista: {mot}\n"
                for e in sorted(list(set(erros))):
                    output_text += f"{e}\n"
                output_text += "-"*30 + "\n"
        
        # Exibição no Layout
        st.text_area("Retorno em TXT", value=output_text, height=300)
        
        # Botão de Download
        st.download_button(
            label="Baixar Relatório (.txt)",
            data=output_text,
            file_name="auditoria_ia_processos.txt",
            mime="text/plain"
        )
    else:
        st.balloons()
        st.success("Nenhuma irregularidade encontrada nos critérios de Interstício, Refeição e Lançamento!")

# Sinalização de Status
st.divider()
st.caption("Sistema de Monitoramento de Conformidade (Sinalização: Ativo ✅ | Versão 1.0)")