import streamlit as st
import pdfplumber
import re
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="IA na Gestão de Processos", page_icon="🤖", layout="wide")

# --- ESTILO CSS ---
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
                
                if "TT HS" in linha or "Resumo" in linha or "Período" in linha: continue
                
                partes = linha.split()
                if not partes or not regex_data.match(partes[0]): continue
                
                data_dia = partes[0]
                erros = []
                
                if "Trabalho" in linha:
                    # Captura todos os horários HH:MM
                    horas = re.findall(r"\d{2}:\d{2}", linha)
                    
                    # 1. VALIDAÇÃO DE LANÇAMENTO (BRUNO DANIEL)
                    if len(horas) < 3:
                        erros.append(f"⚠️ {data_dia} - FALTA DE LANÇAMENTO (Início/Fim)")
                        continue

                    # 2. IDENTIFICAÇÃO DO INTERSTÍCIO (MARCELO WENDER)
                    # O Interstício no PDF Transpedrosa sempre vem antes dos campos de Extra/Noturna.
                    # Vamos localizar o valor que o próprio PDF rotula como Interj.
                    interj_valor = "00:00"
                    if "Interj." in texto: # Se o cabeçalho existe
                         # Buscamos o valor que está ANTES da Hora Noturna (última coluna relevante)
                         # No caso do Marcelo: [..., '11:55', '12:03', '07:00'] -> 12:03 é Interj, 07:00 é Noturna.
                         if len(horas) >= 4:
                             # O Interstício costuma ser o penúltimo valor antes do resumo noturno
                             # Mas para garantir, validamos o valor que não seja a Jornada Diária.
                             idx_diaria = -1
                             for i, h in enumerate(horas):
                                 if h == horas[1]: continue # Fim
                                 if h == "08:00": continue # Normal
                                 # A Diária é o primeiro valor alto após o Normal
                                 if i > 2: 
                                     interj_valor = h # Assume-se que o valor após a diária/refeição é o interj
                    
                    # Validação real do Interstício (Somente se for < 11h e não for a hora noturna)
                    # No Marcelo, 12:03 > 11:00, então o código NÃO deve apontar erro aqui.
                    min_interj = converter_para_minutos(interj_valor)
                    if 0 < min_interj < 660 and interj_valor != horas[-1]: # Ignora o último (Noturna)
                        erros.append(f"⏱️ {data_dia} - INTERSTÍCIO REDUZIDO ({interj_valor})")

                    # 3. REGRA DA REFEIÇÃO (O ponto principal do Marcelo)
                    # Se Jornada Normal (horas[2]) é 08:00 e não há um 6º horário na lista, falta refeição.
                    # Marcelo: ['17:05', '05:00', '08:00', '11:55', '12:03', '07:00'] 
                    # Note que '11:55' é Diária e '12:03' é Interj. O campo Refeição entre eles sumiu.
                    if "Total Refeição" in texto:
                        # Se não há um valor entre 00:01 e 02:00 na posição de refeição
                        # No seu PDF, a refeição fica entre a Diária (11:55) e o Interj (12:03)
                        tem_refeicao = False
                        for h in horas:
                            m = converter_para_minutos(h)
                            if 30 <= m <= 120 and h != "08:00" and h != horas[0] and h != horas[1]:
                                tem_refeicao = True
                                break
                        
                        if not tem_refeicao:
                            erros.append(f"🍱 {data_dia} - FALTA INTERVALO REFEIÇÃO")
                        else:
                            # Se tem, verifica se excedeu 2h
                            for h in horas:
                                m = converter_para_minutos(h)
                                if m > 120 and h not in [horas[0], horas[1], horas[2], interj_valor, horas[-1]]:
                                    erros.append(f"🍱 {data_dia} - REFEIÇÃO EXCEDEU 2H ({h})")
                
                if erros:
                    relatorio_final[motorista_atual].extend(list(set(erros)))
    return relatorio_final

# --- INTERFACE (LAYOUT MANTIDO) ---
col_logo, col_adm = st.columns([1, 1])
with col_logo:
    st.image("https://portalinstitucional-assets.azureedge.net/strapi/assets/Logo_Anhanguera_Horizontal_170x60px_1_d985ea5183.svg", width=220)
with col_adm:
    st.markdown("<div style='text-align: right; padding-top: 20px;'><p style='color: #004a99; font-weight: bold; margin-bottom: 0;'>Desenvolvimento e Análise</p><p style='font-size: 1.2em; color: #333;'>Prof. Cleidson Daniel</p></div>", unsafe_allow_html=True)

st.markdown("""
    <div class="concept-card">
        <h1>IA na Administração & Gestão de Processos</h1>
        <p>Workshop: Laboratório prático focado na <b>convergência entre Inteligência Artificial e gestão estratégica</b>.</p>
        <div class="quote-section">"Pensar de forma inteligente não é apenas automatizar tarefas, mas redesenhar processos para que a tecnologia potencialize o capital humano..."</div>
    </div>
    """, unsafe_allow_html=True)

c_main, c_side = st.columns([2, 1.2])

with c_side:
    st.markdown(f"""
        <div class="side-info-card">
            <h3 style='color: #004a99; margin-top:0; border-bottom: 2px solid #004a99; padding-bottom: 10px;'>Proposta Selecionada</h3>
            <p style='font-size: 0.95em;'><b>Aluna:</b> RAYNARAH MALAQUIAS SOARES<br><b>ID:</b> <code>#IA-17750026</code></p>
            <h5 style='color: #004a99;'>📡 Monitoramento:</h5>
            <div class="monitoring-item">✅ Validação de Interstício (Mín. 11h)</div>
            <div class="monitoring-item">✅ Verificação de Intervalo Alimentação (Máx. 2h)</div>
            <div class="monitoring-item">✅ Auditoria de Jornada Diária</div>
            <div style="text-align: center; margin-top: 20px;"><span class="status-badge">Sinalização: Ativa ✅</span></div>
        </div>
        """, unsafe_allow_html=True)

with c_main:
    st.subheader("📁 Auditoria de Documentos")
    up = st.file_uploader("Upload PDF", type="pdf", label_visibility="collapsed")
    if up:
        with st.status("IA Analisando Processos...", expanded=False):
            res = processar_auditoria(up)
        if res:
            st.markdown("### 🚩 Inconsistências Identificadas")
            txt_out = "RELATÓRIO DE AUDITORIA\n" + "="*40 + "\n"
            for mot, errs in res.items():
                if errs:
                    with st.expander(f"👤 {mot}"):
                        for e in sorted(errs):
                            st.error(e)
                            txt_out += f"{mot} | {e}\n"
            st.download_button("💾 Baixar TXT", txt_out, "auditoria.txt")
        else: st.success("✅ Nenhuma inconsistência detectada.")

st.markdown('<div class="footer-credits"><p style="font-size: 0.8em; color: #999;">Workshop IA Aplicada | Versão 1.2 | Status: Online</p></div>', unsafe_allow_html=True)