import streamlit as st
import pdfplumber
import re

# --- CONFIGURAÇÃO E INTERFACE (PRESERVADOS) ---
st.set_page_config(page_title="IA na Gestão de Processos", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
    .stApp { background-color: #f4f7f6; }
    .concept-card { background: linear-gradient(135deg, #004a99 0%, #002d5f 100%); color: white; padding: 2rem; border-radius: 15px; margin-bottom: 2rem; }
    .footer-credits { background-color: #ffffff; padding: 1rem; border-radius: 10px; text-align: center; margin-top: 2rem; border: 1px solid #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

def conv_min(h):
    try:
        h = str(h).strip().split()[0]
        if ':' not in h: return 0
        partes = h.split(':')
        return int(partes[0]) * 60 + int(partes[1])
    except: return 0

def analisar_pdf(pdf_file):
    relatorio = {}
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            # Identifica o motorista
            match_nome = re.search(r"Funcionário:\s*(.*?)(?=Admissão|CPF|$)", text)
            nome = match_nome.group(1).strip() if match_nome else "Desconhecido"
            if nome not in relatorio: relatorio[nome] = []

            linhas = text.split('\n')
            for l in linhas:
                # 1. Verifica se a linha começa com data
                if re.match(r"^\d{2}/\d{2}/\d{2}", l):
                    dados = l.split()
                    data_dia = dados[0]
                    
                    # 2. Verifica se é dia de TRABALHO
                    if "Trabalho" not in l: continue
                    
                    # 3. REGRA BRUNO (03/03) e GERALDO (04/03): Verifica se houve FALTA
                    # Se houver '08:00' que não seja a Jornada Normal, checamos se é falta
                    tem_falta_cheia = False
                    # No PDF, o 08:00 da falta aparece geralmente após campos vazios
                    if "08:00" in dados:
                        # Se a linha for curta ou tiver 08:00 repetido, é indício de falta
                        if l.count("08:00") >= 1 and len(re.findall(r"\d{2}:\d{2}", l)) < 4:
                            tem_falta_cheia = True
                    
                    if tem_falta_cheia: continue

                    # 4. CAPTURA DE HORÁRIOS (Somente HH:MM)
                    horarios = re.findall(r"\d{2}:\d{2}", l)
                    
                    # Se não tem ao menos 3 horários (Início, Fim, Normal), é falta de lançamento
                    if len(horarios) < 3:
                        relatorio[nome].append(f"⚠️ {data_dia} - FALTA DE LANÇAMENTO")
                        continue

                    # 5. IDENTIFICAÇÃO POR CONTEÚDO (NÃO POR POSIÇÃO)
                    # Marco zero: 08:00 (Jornada Normal)
                    try:
                        idx_normal = horarios.index("08:00")
                        # J. Diária é o próximo após o 08:00
                        j_diaria = horarios[idx_normal + 1] if len(horarios) > idx_normal + 1 else None
                        
                        # Restante após a diária
                        sobras = horarios[idx_normal + 2:]
                        
                        v_refeicao = "00:00"
                        v_interj = "00:00"

                        if len(sobras) >= 2:
                            # Se sobrou 2, o primeiro é refeição, o segundo é interj
                            v_refeicao = sobras[0]
                            v_interj = sobras[1]
                        elif len(sobras) == 1:
                            # Se sobrou só 1, checamos o valor:
                            val = conv_min(sobras[0])
                            if val > 600: # Mais de 10h? É Interj.
                                v_interj = sobras[0]
                                v_refeicao = "00:00"
                            else: # É valor baixo? É refeição.
                                v_refeicao = sobras[0]
                        
                        # 6. VALIDAÇÕES FINAIS
                        # Refeição
                        m_ref = conv_min(v_refeicao)
                        if m_ref == 0:
                            relatorio[nome].append(f"🍱 {data_dia} - FALTA INTERVALO REFEIÇÃO")
                        elif m_ref > 120:
                            relatorio[nome].append(f"🍱 {data_dia} - REFEIÇÃO EXCEDEU 2H ({v_refeicao})")
                        
                        # Interstício (Geraldo 02/03)
                        m_int = conv_min(v_interj)
                        if 0 < m_int < 660: # 11 horas = 660 min
                            relatorio[nome].append(f"⏱️ {data_dia} - INTERSTÍCIO REDUZIDO ({v_interj})")
                            
                    except: continue

    return relatorio

# --- INTERFACE ---
col1, col2 = st.columns([1, 1])
with col1: st.image("https://portalinstitucional-assets.azureedge.net/strapi/assets/Logo_Anhanguera_Horizontal_170x60px_1_d985ea5183.svg", width=220)
with col2: st.markdown("<div style='text-align: right; padding-top: 20px;'><p style='color: #004a99; font-weight: bold; margin-bottom: 0;'>Desenvolvimento e Análise</p><p style='font-size: 1.2em; color: #333;'>Prof. Cleidson Daniel</p></div>", unsafe_allow_html=True)

st.markdown("""<div class="concept-card"><h1>IA na Administração & Gestão de Processos</h1><p>Workshop: Laboratório de Auditoria Digital.</p></div>""", unsafe_allow_html=True)

up = st.file_uploader("Upload PDF", type="pdf")
if up:
    res = analisar_pdf(up)
    if res:
        for m, errs in res.items():
            if errs:
                with st.expander(f"👤 {m}"):
                    for e in sorted(list(set(errs))): st.error(e)
    else: st.success("✅ Documento auditado: Nenhuma infração encontrada nos dias trabalhados.")

st.markdown('<div class="footer-credits"><p style="font-size: 0.8em; color: #999;">Workshop IA Aplicada | Versão 1.6 | Aluna: Raynarah Malaquias</p></div>', unsafe_allow_html=True)