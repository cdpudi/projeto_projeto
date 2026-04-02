import streamlit as st
import pdfplumber
import re

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="IA na Gestão de Processos", page_icon="🤖", layout="wide")

# --- ESTILO CSS APROVADO ---
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

def to_min(h):
    try:
        h = str(h).strip().split('\n')[0]
        p = h.split(':')
        return int(p[0]) * 60 + int(p[1])
    except: return 0

def auditoria_definitiva(pdf_file):
    relatorio = {}
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            texto = page.extract_text()
            # Nome do Motorista
            m_nome = re.search(r"Funcionário:\s*(.*?)(?=Admissão|CPF|$)", texto)
            nome = m_nome.group(1).strip() if m_nome else "Desconhecido"
            if nome not in relatorio: relatorio[nome] = []

            linhas = texto.split('\n')
            for l in linhas:
                if re.match(r"^\d{2}/\d{2}/\d{2}", l) and "Trabalho" in l:
                    # 1. Identifica a Data
                    data = l.split()[0]
                    
                    # 2. Captura todos os horários HH:MM da linha
                    h_total = re.findall(r"\d{2}:\d{2}", l)
                    
                    # REGRA DE FALTA (Bruno 03/03 e Geraldo 04/03)
                    # No PDF, se houver '08:00' na coluna de falta, a linha terá poucos horários
                    if "08:00" in l and len(h_total) <= 3:
                        continue

                    # Se não tem horários de batida, mas o tipo é Trabalho e não é falta lançada
                    if len(h_total) < 2:
                        relatorio[nome].append(f"⚠️ {data} - FALTA DE LANÇAMENTO")
                        continue

                    # 3. MAPEAMENTO POR CONTEÚDO (Não por posição)
                    try:
                        idx_norm = h_total.index("08:00")
                        diaria = h_total[idx_norm + 1] if len(h_total) > idx_norm+1 else "00:00"
                        
                        # Analisamos o que vem depois da Diária
                        sobras = h_total[idx_norm + 2:]
                        
                        ref, interj = "00:00", "00:00"
                        
                        for s in sobras:
                            m = to_min(s)
                            # Se for um valor baixo (até 3h), é Refeição
                            if 0 < m <= 180 and ref == "00:00":
                                ref = s
                            # Se for um valor alto (acima de 9h), é Interj
                            elif m >= 540:
                                interj = s
                        
                        # 4. APLICAÇÃO DAS REGRAS
                        # Refeição (Se Normal > 6h)
                        if to_min(ref) == 0:
                            relatorio[nome].append(f"🍱 {data} - FALTA INTERVALO REFEIÇÃO")
                        elif to_min(ref) > 120:
                            relatorio[nome].append(f"🍱 {data} - REFEIÇÃO EXCEDEU 2H ({ref})")
                        
                        # Interstício (Mínimo 11h)
                        if interj != "00:00" and to_min(interj) < 660:
                            relatorio[nome].append(f"⏱️ {data} - INTERSTÍCIO REDUZIDO ({interj})")
                            
                    except: continue
    return relatorio

# --- INTERFACE (LAYOUT ORIGINAL Anhanguera) ---
col_logo, col_adm = st.columns([1, 1])
with col_logo:
    st.image("https://portalinstitucional-assets.azureedge.net/strapi/assets/Logo_Anhanguera_Horizontal_170x60px_1_d985ea5183.svg", width=220)
with col_adm:
    st.markdown("<div style='text-align: right; padding-top: 20px;'><p style='color: #004a99; font-weight: bold; margin-bottom: 0;'>Desenvolvimento e Análise</p><p style='font-size: 1.2em; color: #333;'>Prof. Cleidson Daniel</p></div>", unsafe_allow_html=True)

st.markdown("""
    <div class="concept-card">
        <h1>IA na Administração & Gestão de Processos</h1>
        <p>Workshop: Laboratório prático focado na <b>convergência entre Inteligência Artificial e gestão estratégica</b>.</p>
        <div class="quote-section">"Pensar de forma inteligente não é apenas automatizar tarefas, mas redesenhar processos..."</div>
    </div>
    """, unsafe_allow_html=True)

c_main, c_side = st.columns([2, 1.2])

with c_side:
    st.markdown(f"""
        <div class="side-info-card">
            <h3 style='color: #004a99; margin-top:0;'>Proposta Selecionada</h3>
            <p><b>Aluna:</b> RAYNARAH MALAQUIAS SOARES<br><b>ID:</b> <code>#IA-17750026</code></p>
            <h5 style='color: #004a99;'>📡 Monitoramento:</h5>
            <div class="monitoring-item">✅ Filtro de Faltas Lançadas</div>
            <div class="monitoring-item">✅ Interstício Mínimo (11h)</div>
            <div class="monitoring-item">✅ Refeição Obrigatória (Máx 2h)</div>
            <div style="text-align: center; margin-top: 20px;"><span class="status-badge">Sinalização: Ativa ✅</span></div>
        </div>
        """, unsafe_allow_html=True)

with c_main:
    st.subheader("📁 Auditoria de Documentos")
    up = st.file_uploader("Upload PDF", type="pdf", label_visibility="collapsed")
    if up:
        with st.status("Auditando via IA..."):
            res = auditoria_definitiva(up)
        if res:
            for mot, errs in res.items():
                if errs:
                    with st.expander(f"👤 {mot}"):
                        for e in sorted(list(set(errs))): st.error(e)
        else: st.success("✅ Tudo em conformidade nos dias trabalhados.")

st.markdown('<div class="footer-credits"><p style="font-size: 0.8em; color: #999;">Workshop IA Aplicada | Versão Final | Status: Online</p></div>', unsafe_allow_html=True)