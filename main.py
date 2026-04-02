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
    .status-badge { padding: 6px 12px; border-radius: 20px; font-size: 13px; background-color: #28a745; color: white; font-weight: bold; }
    .footer-credits { background-color: #ffffff; padding: 1rem; border-radius: 10px; text-align: center; margin-top: 2rem; border: 1px solid #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

def converter_minutos(h):
    if not h: return 0
    try:
        partes = h.split(':')
        return int(partes[0]) * 60 + int(partes[1])
    except: return 0

def auditoria_transpedrosa(pdf_file):
    relatorio = {}
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            # Captura nome do funcionário
            func_match = re.search(r"Funcionário:\s*(.*?)(?=Admissão|CPF|$)", text)
            nome = func_match.group(1).strip() if func_match else "Desconhecido"
            if nome not in relatorio: relatorio[nome] = []

            linhas = text.split('\n')
            for linha in linhas:
                if re.match(r"^\d{2}/\d{2}/\d{2}", linha) and "Trabalho" in linha:
                    partes = linha.split()
                    data_dia = partes[0]
                    
                    # Pegamos todos os horários HH:MM da linha
                    horas = re.findall(r"\d{2}:\d{2}", linha)
                    
                    if len(horas) >= 3:
                        # 1. Localizar Marco Zero (Jornada Normal 08:00)
                        try:
                            idx_8 = horas.index("08:00")
                            # Diária: sempre após o 08:00
                            v_diaria = horas[idx_8 + 1] if len(horas) > idx_8 + 1 else "00:00"
                            
                            # Refeição: Vamos verificar se existe um valor de refeição real
                            # No caso do Bruno, o 01:03 aparece após a Diária.
                            # No caso do Marcelo, após a Diária já pula para o Interj (12:03).
                            
                            proximo_valor = horas[idx_8 + 2] if len(horas) > idx_8 + 2 else "00:00"
                            min_proximo = converter_minutos(proximo_valor)
                            
                            refeicao = "00:00"
                            interj = "00:00"

                            # LÓGICA DE DECISÃO:
                            # Se o valor após a diária for pequeno (até 2h), é REFEIÇÃO.
                            # Se for grande (perto de 11h), a refeição foi PULADA e o valor é o INTERSTÍCIO.
                            if 0 < min_proximo <= 150: # Até 2h30 para margem de erro
                                refeicao = proximo_valor
                                # O próximo depois da refeição seria o Interj
                                if len(horas) > idx_8 + 3:
                                    interj = horas[idx_8 + 3]
                            else:
                                # Se o valor é alto, ele já é o Interstício
                                interj = proximo_valor
                                refeicao = "00:00"

                            # --- VALIDAÇÕES ---
                            # A) Refeição (Obrigatória se Normal > 6h)
                            if converter_minutos(refeicao) == 0:
                                relatorio[nome].append(f"🍱 {data_dia} - FALTA INTERVALO REFEIÇÃO")
                            elif converter_minutos(refeicao) > 120:
                                relatorio[nome].append(f"🍱 {data_dia} - REFEIÇÃO EXCEDEU 2H ({refeicao})")

                            # B) Interstício (Mínimo 11h)
                            if interj != "00:00":
                                if converter_minutos(interj) < 660:
                                    relatorio[nome].append(f"⏱️ {data_dia} - INTERSTÍCIO REDUZIDO ({interj})")
                        except ValueError:
                            pass
    return relatorio

# --- INTERFACE ---
col1, col2 = st.columns([1, 1])
with col1: st.image("https://portalinstitucional-assets.azureedge.net/strapi/assets/Logo_Anhanguera_Horizontal_170x60px_1_d985ea5183.svg", width=220)
with col2: st.markdown("<div style='text-align: right; padding-top: 20px;'><p style='color: #004a99; font-weight: bold; margin-bottom: 0;'>Desenvolvimento e Análise</p><p style='font-size: 1.2em; color: #333;'>Prof. Cleidson Daniel</p></div>", unsafe_allow_html=True)

st.markdown("""<div class="concept-card"><h1>IA na Administração & Gestão de Processos</h1><p>Workshop: Laboratório prático focado na <b>convergência entre Inteligência Artificial e gestão estratégica</b>.</p></div>""", unsafe_allow_html=True)

c_main, c_side = st.columns([2, 1.2])

with c_side:
    st.markdown(f"""<div class="side-info-card"><h3>Proposta Selecionada</h3><p><b>Aluna:</b> RAYNARAH MALAQUIAS SOARES</p><hr><h5>📡 Monitoramento:</h5><div style='font-size:0.85em'>✅ Validação de Interstício (11h)<br>✅ Verificação de Intervalo Alimentação<br>✅ Auditoria de Jornada Diária</div></div>""", unsafe_allow_html=True)

with c_main:
    st.subheader("📁 Auditoria de Documentos")
    up = st.file_uploader("Upload PDF", type="pdf", label_visibility="collapsed")
    if up:
        with st.status("Analisando..."):
            res = auditoria_transpedrosa(up)
        if res:
            for mot, errs in res.items():
                if errs:
                    with st.expander(f"👤 {mot}"):
                        for e in sorted(list(set(errs))): st.error(e)
        else: st.success("✅ Tudo em conformidade.")

st.markdown('<div class="footer-credits"><p style="font-size: 0.8em; color: #999;">Workshop IA Aplicada | Versão 1.4 | Status: Online</p></div>', unsafe_allow_html=True)