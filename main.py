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
    .side-info-card { background-color: white; padding: 30px; border-radius: 15px; border: 1px solid #e0e0e0; }
    .footer-credits { background-color: #ffffff; padding: 1rem; border-radius: 10px; text-align: center; margin-top: 2rem; border: 1px solid #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

def converter_minutos(h):
    if not h or h == "" or h == "00:00": return 0
    try:
        h = h.strip().split('\n')[0] # Pega apenas a primeira linha se houver quebra
        partes = h.split(':')
        return int(partes[0]) * 60 + int(partes[1])
    except: return 0

def auditoria_final(pdf_file):
    relatorio = {}
    
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            # Extrair nome do funcionário
            text = page.extract_text()
            func_match = re.search(r"Funcionário:\s*(.*?)(?=Admissão|CPF|$)", text)
            nome = func_match.group(1).strip() if func_match else "Desconhecido"
            if nome not in relatorio: relatorio[nome] = []

            # Extração de tabela com estratégia de texto para capturar campos vazios
            table = page.extract_table()
            if not table: continue

            for row in table:
                # row[0] costuma ser a Data, row[1] o Tipo
                if row[0] and re.match(r"^\d{2}/\d{2}/\d{2}", row[0]):
                    data_dia = row[0].split()[0]
                    tipo = row[1] if len(row) > 1 else ""
                    
                    if "Trabalho" in str(tipo):
                        # Mapeamento Transpedrosa nas colunas da tabela extraída:
                        # [2]Início/Fim, [3]J.Normal, [4]J.Diária, [5]Refeição, [6]Repouso, [7]Faltas, [8]Interj
                        
                        inicio_fim = row[2] if len(row) > 2 else ""
                        j_normal = row[3] if len(row) > 3 else ""
                        refeicao = row[5] if len(row) > 5 else ""
                        faltas = row[7] if len(row) > 7 else ""
                        interj = row[8] if len(row) > 8 else ""

                        # CRITÉRIO 1: Se tem 08:00 em Faltas, ele não trabalhou. Ignora auditoria.
                        if "08:00" in str(faltas):
                            continue

                        # CRITÉRIO 2: Se é Trabalho e não tem Início/Fim registrado
                        if not inicio_fim or ":" not in str(inicio_fim):
                            relatorio[nome].append(f"⚠️ {data_dia} - FALTA DE LANÇAMENTO (Início/Fim não registrados)")
                            continue

                        # CRITÉRIO 3: Refeição (Obrigatória se J.Normal > 6h)
                        min_normal = converter_minutos(j_normal)
                        if min_normal > 360: # Maior que 6 horas
                            min_ref = converter_minutos(refeicao)
                            if min_ref == 0:
                                relatorio[nome].append(f"🍱 {data_dia} - FALTA INTERVALO REFEIÇÃO")
                            elif min_ref > 120:
                                relatorio[nome].append(f"🍱 {data_dia} - REFEIÇÃO EXCEDEU 2H ({refeicao.strip()})")

                        # CRITÉRIO 4: Interstício (Mínimo 11h)
                        if interj:
                            min_interj = converter_minutos(interj)
                            if 0 < min_interj < 660: # Menor que 11h
                                relatorio[nome].append(f"⏱️ {data_dia} - INTERSTÍCIO REDUZIDO ({interj.strip()})")
                                
    return relatorio

# --- INTERFACE ---
col1, col2 = st.columns([1, 1])
with col1: st.image("https://portalinstitucional-assets.azureedge.net/strapi/assets/Logo_Anhanguera_Horizontal_170x60px_1_d985ea5183.svg", width=220)
with col2: st.markdown("<div style='text-align: right; padding-top: 20px;'><p style='color: #004a99; font-weight: bold; margin-bottom: 0;'>Desenvolvimento e Análise</p><p style='font-size: 1.2em; color: #333;'>Prof. Cleidson Daniel</p></div>", unsafe_allow_html=True)

st.markdown("""<div class="concept-card"><h1>IA na Administração & Gestão de Processos</h1><p>Workshop: Laboratório prático focado na <b>convergência entre Inteligência Artificial e gestão estratégica</b>.</p></div>""", unsafe_allow_html=True)

c_main, c_side = st.columns([2, 1.2])

with c_side:
    st.markdown(f"""<div class="side-info-card"><h3>Proposta Selecionada</h3><p><b>Aluna:</b> RAYNARAH MALAQUIAS SOARES</p><hr><h5>📡 Monitoramento:</h5><div style='font-size:0.85em'>✅ Ignorar Faltas Lançadas<br>✅ Refeição Obrigatória (Max 2h)<br>✅ Interstício Mínimo (11h)</div></div>""", unsafe_allow_html=True)

with c_main:
    st.subheader("📁 Auditoria de Documentos")
    up = st.file_uploader("Upload PDF", type="pdf", label_visibility="collapsed")
    if up:
        with st.status("Auditando...", expanded=False):
            res = auditoria_final(up)
        if res:
            for mot, errs in res.items():
                if errs:
                    with st.expander(f"👤 {mot}"):
                        for e in sorted(list(set(errs))): st.error(e)
        else: st.success("✅ Nenhuma inconsistência detectada nos dias trabalhados.")

st.markdown('<div class="footer-credits"><p style="font-size: 0.8em; color: #999;">Workshop IA Aplicada | Versão 1.5 | Status: Online</p></div>', unsafe_allow_html=True)