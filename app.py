import streamlit as st
import pdfplumber
import re
import time
from datetime import datetime

st.set_page_config(page_title="OFX Transforms", page_icon="🤖")

st.title("🤖 OFX Transforms")

# --- ABA SUSPENSA COM FOCO NA ORDEM DE SELEÇÃO ---
with st.expander("⚠️ LEIA ANTES DE COMEÇAR (Clique aqui)"):
    st.warning("Para evitar erros no Sistema Domínio, siga esta ordem:")
    st.write("""
        1. **Primeiro:** Selecione o **Banco** correto.
        2. **Segundo:** Selecione o **Ano** do extrato (ex: 2025).
        3. **Por último:** Arraste o arquivo **PDF** para o campo abaixo.
        
        *Isso garante que o robô coloque o 'carimbo' de data e o nome do arquivo corretamente.*
    """)

# Seletores de Banco e Ano
col1, col2 = st.columns(2)
with col1:
    banco_selecionado = st.selectbox("1º Selecione o Banco:", ["Santander", "Sicoob", "Itau", "BB", "Caixa", "Inter", "Nubank", "Outro"])
with col2:
    ano_extrato = st.selectbox("2º Selecione o Ano:", ["2025", "2024", "2026"])

# Upload do PDF
arquivo_pdf = st.file_uploader("3º Arraste seu PDF aqui", type="pdf")

if arquivo_pdf:
    transacoes = []
    palavras_proibidas = ["SALDO", "RESUMO", "TOTAL", "DEMONSTRATIVO"]
    palavras_permitidas = ["APLICACAO", "RESGATE", "RENDIMENTO"]

    with pdfplumber.open(arquivo_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                for linha in texto.split('\n'):
                    linha_up = linha.upper()
                    
                    deve_pular = False
                    for prob in palavras_proibidas:
                        if prob in linha_up:
                            deve_pular = True
                            for perm in palavras_permitidas:
                                if perm in linha_up:
                                    deve_pular = False
                                    break
                            break
                    if deve_pular: continue

                    m_data = re.search(r'(\d{2}/\d{2})', linha)
                    m_valor = re.search(r'(-?\s?\d?\.?\d+,\d{2}\s?-?|D|C)', linha)
                    
                    if m_data and m_valor:
                        valor_str = m_valor.group(0).strip()
                        e_negativo = '-' in valor_str or 'D' in linha_up
                        
                        apenas_numeros = re.sub(r'[^\d,]', '', valor_str)
                        valor_final = apenas_numeros.replace(',', '.')
                        
                        if e_negativo:
                            valor_final = f"-{valor_final}"
                        
                        desc = linha.replace(m_data.group(0), '').replace(m_valor.group(0), '').strip()
                        transacoes.append({'v': valor_final, 'd': desc[:32], 'data': m_data.group(0)})

    if transacoes:
        st.success(f"✅ Robô concluiu a leitura!")
        
        with st.expander("🔍 Conferir dados antes de baixar"):
            st.table(transacoes[:10])

        # Organização do Nome do Arquivo
        mes_num = transacoes[0]['data'][3:5]
        meses_nome = {"01":"Janeiro","02":"Fevereiro","03":"Marco","04":"Abril","05":"Maio","06":"Junho",
                      "07":"Julho","08":"Agosto","09":"Setembro","10":"Outubro","11":"Novembro","12":"Dezembro"}
        nome_mes = meses_nome.get(mes_num, "Mes")
        nome_arquivo = f"Extrato_{banco_selecionado}_{nome_mes}_{ano_extrato}.ofx"

        # Estrutura OFX (Padrão SGML para Domínio)
        dt_agora = datetime.now().strftime('%Y%m%d%H%M%S')
        ofx = "OFXHEADER:100\nDATA:OFXSGML\nVERSION:102\nSECURITY:NONE\nENCODING:USASCII\nCHARSET:1252\nCOMPRESSION:NONE\nOLDFILEUID:NONE\nNEWFILEUID:NONE\n\n"
        ofx += "<OFX>\n<SIGNONMSGSRSV1>\n<SONRS>\n<STATUS><CODE>0</CODE><SEVERITY>INFO</SEVERITY></STATUS>\n"
        ofx += f"<DTSERVER>{dt_agora}</DTSERVER>\n<LANGUAGE>POR</LANGUAGE>\n</SONRS>\n</SIGNONMSGSRSV1>\n"
        ofx += "<BANKMSGSRSV1>\n<STMTTRNRS>\n<STMTRS>\n<CURDEF>BRL</CURDEF>\n"
        ofx += "<BANKACCTFROM>\n<BANKID>9999</BANKID>\n<ACCTID>000000</ACCTID>\n<ACCTTYPE>CHECKING</ACCTTYPE>\n</BANKACCTFROM>\n<BANKTRANLIST>\n"
        
        for i, t in enumerate(transacoes):
            dt_posted = f"{ano_extrato}{t['data'][3:5]}{t['data'][0:2]}120000"
            ofx += f"<STMTTRN>\n<TRNTYPE>OTHER</TRNTYPE>\n<DTPOSTED>{dt_posted}</DTPOSTED>\n"
            ofx += f"<TRNAMT>{t['v']}</TRNAMT>\n<FITID>{dt_agora}{i}</FITID>\n<MEMO>{t['d']}</MEMO>\n</STMTTRN>\n"

        ofx += "</BANKTRANLIST>\n</STMTRS>\n</STMTTRNRS>\n</BANKMSGSRSV1>\n</OFX>"

        st.download_button(label=f"📥 Baixar Arquivo: {nome_arquivo}", data=ofx, file_name=nome_arquivo)
