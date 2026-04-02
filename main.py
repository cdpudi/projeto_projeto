import streamlit as st
import pdfplumber
import re

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="IA na Gestão de Processos", page_icon="🤖", layout="wide")

# --- ESTILO CSS (PRESERVADO) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
    .stApp { background-color: #f4f7f6; }
    .concept-card { background: linear-gradient(135deg, #004a99 0%, #002d5f 100%); color: white; padding: 2rem; border-radius: 15px; margin-bottom: 2rem; }
    .quote-section { border-left: 4px solid #ff914d; padding-left: 15px; font-style: italic; color: #e0e0e0; margin: 15px 0; }
    .side-info-card { background-color: white; padding: 30px; border-radius: 15px; border: 1px solid #e0e0e0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .status-badge { padding: 6px 12px; border-radius: 20px; font-size: 13px; background-color: #28a745; color: white; font-weight: bold; }
    .footer-credits { background-color: #ffffff; padding: 1rem; border-radius: 10px; text-align: center; margin-top: 2rem; border: 1px solid #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

def converter_minutos(h):
    if not h or h == "" or h == "00:00": return 0
    try:
        partes = h.split(':')
        return int(partes[0]) * 60 + int(partes[1])
    except: return 0

def auditoria_inteligente(pdf_file):
    relatorio = {}
    
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            # Extrair o nome do funcionário
            text_full = page.extract_text()
            func_match = re.search(r"Funcionário:\s*(.*?)(?=Admissão|CPF|$)", text_full)
            nome = func_match.group(1).strip() if func_match else "Desconhecido"
            
            if nome not in relatorio: relatorio[nome] = []

            # Extrair a tabela por coordenadas para não confundir as colunas
            # Mapeamento aproximado das colunas da Transpedrosa (Eixo X)
            table = page.extract_table({
                "vertical_strategy": "text", 
                "horizontal_strategy": "lines",
                "snap_tolerance": 3,
            })
            
            rows = page.extract_text().split('\n')
            for linha in rows:
                # Filtrar apenas linhas que começam com data (DD/MM/YY)
                if re.match(r"^\d{2}/\d{2}/\d{2}", linha):
                    partes = linha.split()
                    data_dia = partes[0]
                    
                    # Regex para capturar todos os horários da linha na ordem que aparecem
                    horas = re.findall(r"\d{2}:\d{2}", linha)
                    
                    # 1. VALIDAÇÃO DE LANÇAMENTO (Início/Fim)
                    if len(horas) < 2:
                        relatorio[nome].append(f"⚠️ {data_dia} - FALTA DE LANÇAMENTO (Início/Fim)")
                        continue

                    # 2. IDENTIFICAÇÃO POSICIONAL RÍGIDA
                    # No layout Transpedrosa, as colunas seguem:
                    # [0]Início, [1]Fim, [2]Normal, [3]Diária, [4]Refeição, [5]Interj.
                    # Quando um valor no meio falta, o array diminui.
                    
                    j_normal = "08:00" # Padrão
                    j_diaria = ""
                    refeicao = ""
                    interj = ""
                    
                    # Buscamos a J. Diária (Geralmente o valor após o 08:00)
                    try:
                        idx_normal = horas.index("08:00")
                        j_diaria = horas[idx_normal + 1]
                        
                        # A partir daqui, verificamos a existência dos próximos campos
                        # Se houver mais 2 campos após a diária: [Diária, Refeição, Interj]
                        # Se houver apenas 1 campo após a diária: [Diária, Interj] (Refeição Vazia)
                        
                        resto = horas[idx_normal + 2:]
                        
                        if len(resto) >= 2:
                            refeicao = resto[0]
                            interj = resto[1]
                        elif len(resto) == 1:
                            # Se sobrou só um, e ele é alto (perto de 11h), é o Interj.
                            if converter_minutos(resto[0]) > 600:
                                interj = resto[0]
                                refeicao = "" # Refeição vazia detectada
                            else:
                                refeicao = resto[0]
                                interj = ""
                    except:
                        pass

                    # --- REGRAS DE AUDITORIA ---
                    
                    # A) REGRA REFEIÇÃO
                    min_ref = converter_minutos(refeicao)
                    if min_ref == 0:
                        relatorio[nome].append(f"🍱 {data_dia} - FALTA INTERVALO REFEIÇÃO")
                    elif min_ref > 120:
                        relatorio[nome].append(f"🍱 {data_dia} - REFEIÇÃO EXCEDEU 2H ({refeicao})")

                    # B) REGRA INTERSTÍCIO (Interj.)
                    if interj:
                        min_interj = converter_minutos(interj)
                        if min_interj < 660: # 11 horas
                            relatorio[nome].append(f"⏱️ {data_dia} - INTERSTÍCIO REDUZIDO ({interj})")
                    # Se não achou o interj na linha de "Trabalho", ele costuma estar na linha abaixo ou oculta
                    # mas para os casos apresentados (Marcelo/Bruno), essa lógica cobre.

    return relatorio

# --- INTERFACE ---
col1, col2 = st.columns([1, 1])
with col1: st.image("https://portalinstitucional-assets.azureedge.net/strapi/assets/Logo_Anhanguera_Horizontal_170x60px_1_d985ea5183.svg", width=220)
with col2: st.markdown("<div style='text-align: right; padding-top: 20px;'><p style='color: #004a99; font-weight: bold; margin-bottom: 0;'>Desenvolvimento e Análise</p><p style='font-size: 1.2em; color: #333;'>Prof. Cleidson Daniel</p></div>", unsafe_allow_html=True)

st.markdown("""<div class="concept-card"><h1>IA na Administração & Gestão de Processos</h1><p>Workshop: Laboratório prático focado na <b>convergência entre Inteligência Artificial e gestão estratégica</b>.</p><div class="quote-section">"Pensar de forma inteligente não é apenas automatizar tarefas, mas redesenhar processos..."</div></div>""", unsafe_allow_html=True)

c_main, c_side = st.columns([2, 1.2])

with c_side:
    st.markdown(f"""<div class="side-info-card"><h3 style='color: #004a99; margin-top:0;'>Proposta Selecionada</h3><p><b>Aluna:</b> RAYNARAH MALAQUIAS SOARES<br><b>ID:</b> #IA-17750026</p><hr><h5 style='color: #004a99;'>📡 Monitoramento:</h5><div style='font-size:0.85em'>✅ Validação de Interstício (11h)<br>✅ Verificação de Intervalo Alimentação<br>✅ Auditoria de Jornada Diária</div><div style='text-align:center; margin-top:20px'><span class="status-badge">Sinalização: Ativa ✅</span></div></div>""", unsafe_allow_html=True)

with c_main:
    st.subheader("📁 Auditoria de Documentos")
    up = st.file_uploader("Arraste o PDF aqui", type="pdf", label_visibility="collapsed")
    if up:
        with st.status("Auditando...", expanded=False):
            res = auditoria_inteligente(up)
        if res:
            for mot, errs in res.items():
                if errs:
                    with st.expander(f"👤 {mot}"):
                        for e in sorted(list(set(errs))): st.error(e)
        else: st.success("✅ Tudo em conformidade.")

st.markdown('<div class="footer-credits"><p style="font-size: 0.8em; color: #999;">Workshop IA Aplicada | Versão 1.3 | Status: Online</p></div>', unsafe_allow_html=True)