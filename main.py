import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO

# Configuração da página
st.set_page_config(page_title="Auditoria Transpedrosa", layout="wide")

def limpar_texto(valor):
    if valor is None: return ""
    return str(valor).replace('\n', ' ').strip()

def processar_pdf(file_bytes):
    relatorio = {}
    regex_data = re.compile(r"^\d{2}/\d{2}/\d{2}")
    
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        paginas = pdf.pages
        progresso = st.progress(0)
        
        for i, pagina in enumerate(paginas):
            texto_pag = pagina.extract_text()
            if not texto_pag or "Resumo" in texto_pag:
                progresso.progress((i + 1) / len(paginas))
                continue

            motorista_atual = "Desconhecido"
            for linha_txt in texto_pag.split('\n'):
                if "Funcionário:" in linha_txt:
                    motorista_atual = linha_txt.split("Funcionário:")[1].split("Admissão:")[0].strip()
                    if motorista_atual not in relatorio:
                        relatorio[motorista_atual] = []

            tabela = pagina.extract_table()
            if tabela:
                for linha in tabela:
                    data_bruta = limpar_texto(linha[0])
                    if not regex_data.match(data_bruta): continue

                    tipo = limpar_texto(linha[1]).upper()
                    if "TRABALHO" in tipo:
                        jornada, j_normal, j_diaria, refeicao = (
                            limpar_texto(linha[2]), limpar_texto(linha[3]), 
                            limpar_texto(linha[4]), limpar_texto(linha[5])
                        )
                        if not (jornada and j_normal and j_diaria and refeicao):
                            relatorio[motorista_atual].append(f"{data_bruta} - PROBLEMA LANÇAMENTO")
            
            progresso.progress((i + 1) / len(paginas))
    return relatorio

# --- INTERFACE WEB ---
st.title("🚛 Auditoria de Ponto - Transpedrosa")
st.write("Faça o upload do PDF para identificar falhas de lançamento.")

arquivo_pdf = st.file_uploader("Escolha o arquivo PDF", type="pdf")

if arquivo_pdf:
    if st.button("Analisar PDF"):
        resultados = processar_pdf(arquivo_pdf.read())
        
        st.subheader("Resultados da Auditoria")
        
        conteudo_txt = "RELATÓRIO DE INCONSISTÊNCIAS\n" + "="*30 + "\n\n"
        tem_erro = False
        
        for motorista, erros in resultados.items():
            if erros:
                tem_erro = True
                with st.expander(f"🔴 Motorista: {motorista}"):
                    for e in erros:
                        st.write(e)
                        conteudo_txt += f"Motorista: {motorista}\n{e}\n\n"
        
        if not tem_erro:
            st.success("✅ Nenhuma inconsistência encontrada!")
        else:
            st.download_button(
                label="Baixar Relatório TXT",
                data=conteudo_txt,
                file_name="inconsistencias.txt",
                mime="text/plain"
            )