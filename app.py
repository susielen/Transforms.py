import streamlit as st
import pandas as pd
import pdfplumber
import re
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Conversor Profissional OFX", page_icon="🏦")

# Estilo para o botão ficar igual ao outro projeto (Verde e Grande)
st.markdown("""
    <style>
    div.stDownloadButton > button:first-child {
        background-color: #28a745;
        color: white;
        height: 3em;
        width: 100%;
        border-radius: 10px;
        border: none;
        font-size: 20px;
        font-weight: bold;
        transition: 0.3s;
    }
    div.stDownloadButton > button:first-child:hover {
        background-color: #218838;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏦 Conversor de Extratos")

# Lista de bancos
lista_de_bancos = [
    "Santander", "Sicoob", "Itaú", "Banco do Brasil", "Caixa", 
    "Inter", "Mercado Pago", "Sicredi", "XP", "Nubank", 
    "Outro Banco" 
]

banco_escolhido = st.selectbox("Selecione o seu banco:", lista_de_bancos)

arquivo_pdf = st.file_uploader(f"Suba o PDF do {banco_escolhido} aqui", type="pdf")

if arquivo_pdf is not None:
    transacoes = []
    
    with pdfplumber.open(arquivo_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                for linha in texto.split('\n'):
                    tem_data = re.search(r'(\d{2}/\d{2})', linha)
                    tem_valor = re.search(r'(-?\d?\.?\d+,\d{2})', linha)
                    
                    if tem_data and tem_valor:
                        v = tem_valor.group(1).replace('.', '').replace(',', '.')
                        d = linha.replace(tem_data.group(1), '').replace(tem_valor.group(1), '').strip()
                        transacoes.append({'valor': v, 'desc': d})

    if transacoes:
        st.info(f"Processamento concluído: {len(transacoes)} transações encontradas.")
        
        # Montando o arquivo OFX
        data_ofx = datetime.now().strftime('%Y%m%d')
        ofx_body = f"""OFXHEADER:100\nDATA:OFXSGML\nVERSION:102\nENCODING:USASCII\nCHARSET:1252\n<OFX><BANKMSGSRSV1><STMTTRNRS><STMTRS><CURDEF>BRL</CURDEF><BANKTRANLIST>"""
        
        for t in transacoes:
            ofx_body += f"<STMTTRN><TRNTYPE>OTHER</TRNTYPE><DTPOSTED>{data_ofx}</DTPOSTED><TRNAMT>{t['valor']}</TRNAMT><MEMO>{t['desc'][:32]}</MEMO></STMTTRN>"
        
        ofx_body += "</BANKTRANLIST></STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>"
        
        # O Botão que agora está bonitão
        st.download_button(
            label=f"📥 BAIXAR ARQUIVO OFX ({banco_escolhido.upper()})",
            data=ofx_body,
            file_name=f"extrato_{banco_escolhido.lower()}.ofx",
            mime="application/x-ofx"
        )
    else:
        st.warning("Nenhuma transação identificada. Verifique se o arquivo está correto.")

# Seu lembrete de 5 anos
st.divider()
st.caption("Regra: Para o fornecedor o crédito é positivo e o débito negativo; para o cliente o crédito é negativo e o débito positivo.")
