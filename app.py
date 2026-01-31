import streamlit as st
import pdfplumber
import re
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="OFX Transforms", page_icon="🤖")

st.title("🤖 OFX Transforms Final")

# --- 1. ABA SUSPENSA EXPLICATIVA ---
with st.expander("⚠️ LEIA O PASSO A PASSO (Clique aqui)"):
    st.warning("Para o arquivo sair perfeito para o Domínio, siga esta ordem:")
    st.write("""
        1. **Selecione o Banco:** Escolha o banco na lista abaixo.
        2. **Selecione o Ano:** Como você está usando extratos de **2025**, mude para 2025 no seletor.
        3. **Suba o PDF:** O robô vai ler as datas e valores e criar o arquivo OFX.
        4. **Conferência:** Olhe a tabela de prévia para ver se as 'Aplicações' e 'Resgates' aparecem.
    """)

# --- 2. SELETORES (BANCO E ANO) ---
col1, col2 = st.columns(2)
with col1:
    banco_sel = st.selectbox("1º Passo: Selecione o Banco", ["Santander", "Sicoob", "Itau", "BB", "Caixa", "Inter", "Nubank", "Outro"])
with col2:
    ano_extrato = st.selectbox("2º Passo: Selecione o Ano", ["2025", "2024", "2026"])

# --- 3. UPLOAD DO ARQUIVO ---
arquivo_pdf = st.file_uploader("3º Passo: Arraste seu PDF aqui", type="pdf")

if arquivo_pdf:
    transacoes = []
    # Filtros de inteligência
    palavras_proibidas = ["SALDO", "RESUMO", "TOTAL", "DEMONSTRATIVO"]
    palavras_permitidas = ["APLICACAO", "RESGATE", "RENDIMENTO"]

    with pdfplumber.open(arquivo_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                for linha in texto.split('\n'):
                    linha_up = linha.upper()
                    
                    # Lógica de Filtragem (Ignora lixo, mantém o que você pediu)
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

                    # Busca Data (DD/MM) e Valor (com vírgula)
                    m_data = re.search(r'(\d{2}/\d{2})', linha)
                    m_valor = re.search(r'(-?\s?\d?\.?\d+,\d{2}\s?-?|D|C)', linha)
                    
                    if m_data and m_valor:
                        valor_str = m_valor.group(0).strip()
                        # Regra do sinal: se tiver '-', 'D' ou for débito, valor fica negativo
                        e_negativo = '-' in valor_str or 'D' in linha_up
                        
                        apenas_numeros = re.sub(r'[^\d,]', '', valor_str)
                        valor_final = apenas_numeros.replace(',', '.')
                        
                        if e_negativo:
                            valor_final = f"-{valor_final}"
                        
                        # Limpa a descrição para o Domínio (limite 32 caracteres)
                        desc = linha.replace(m_data.group(0), '').replace(m_valor.group(0), '').strip()
                        transacoes.append({'v': valor_final, 'd': desc[:32], 'data': m_data.group(0)})

    if transacoes:
        st.success(f"✅ Robô concluiu a leitura de {len(transacoes)} itens!")
        
        # --- 4. PRÉVIA PARA CONFERÊNCIA ---
        with st.expander("🔍 Conferir itens capturados (Aplicações, Resgates, etc)"):
            st.table(transacoes)

        # Nome automático do arquivo baseado no mês da primeira transação
        mes_num = transacoes[0]['data'][3:5]
        meses_nome = {"01":"Janeiro","02":"Fevereiro","03":"Marco","04":"Abril","05":"Maio","06":"Junho",
                      "07":"Julho","08":"Agosto","09":"Setembro","10":"Outubro","11":"Novembro","12":"Dezembro"}
        nome_mes = meses_nome.get(mes_num, "Mes")
        nome_arquivo = f"Extrato_{banco_sel}_{nome_mes}_{ano_extrato}.ofx"

        # --- 5. GERAÇÃO DO OFX (PADRÃO SGML/DOMÍNIO) ---
        dt_agora = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # Cabeçalho técnico do OFX
        ofx = "OFXHEADER:100\nDATA:OFXSGML\nVERSION:102\nSECURITY:NONE\nENCODING:USASCII\nCHARSET:1252\nCOMPRESSION:NONE\nOLDFILEUID:NONE\nNEWFILEUID:NONE\n\n"
        ofx += "<OFX>\n<SIGNONMSGSRSV1>\n<SONRS>\n<STATUS><CODE>0</CODE><SEVERITY>INFO</SEVERITY></STATUS>\n"
        ofx += f"<DTSERVER>{dt_agora}</DTSERVER>\n<LANGUAGE>POR</LANGUAGE>\n</SONRS>\n</SIGNONMSGSRSV1>\n"
        ofx += "<BANKMSGSRSV1>\n<STMTTRNRS>\n<STMTRS>\n<CURDEF>BRL</CURDEF>\n"
        ofx += "<BANKACCTFROM>\n<BANKID>9999</BANKID>\n<ACCTID>000000</ACCTID>\n<ACCTTYPE>CHECKING</ACCTTYPE>\n</BANKACCTFROM>\n<BANKTRANLIST>\n"
        
        for i, t in enumerate(transacoes):
            # Monta a data com o ano selecionado pelo usuário
            dt_posted = f"{ano_extrato}{t['data'][3:5]}{t['data'][0:2]}120000"
            ofx += f"<STMTTRN>\n<TRNTYPE>OTHER</TRNTYPE>\n<DTPOSTED>{dt_posted}</DTPOSTED>\n"
            ofx += f"<TRNAMT>{t['v']}</TRNAMT>\n<FITID>{dt_agora}{i}</FITID>\n<MEMO>{t['d']}</MEMO>\n</STMTTRN>\n"

        ofx += "</BANKTRANLIST>\n</STMTRS>\n</STMTTRNRS>\n</BANKMSGSRSV1>\n</OFX>"

        # Botão de download
        st.download_button(
            label=f"📥 Baixar Arquivo: {nome_arquivo}", 
            data=ofx, 
            file_name=nome_arquivo,
            mime="text/plain"
        )
