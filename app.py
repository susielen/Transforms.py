import streamlit as st
import pandas as pd
import pdfplumber
import re
from datetime import datetime

st.set_page_config(page_title="Conversor Multi-Bancos OFX", page_icon="🏦")

st.title("🏦 Conversor de Extratos por Banco")
st.write("Escolha o seu banco e suba o PDF para gerar o arquivo OFX!")

# 1. Seleção do Banco (As gavetas da nossa caixa)
banco_escolhido = st.selectbox(
    "De qual banco é o seu extrato?",
    ["Santander", "Sicoob", "Itaú", "Banco do Brasil", "Caixa", "Inter", "Mercado Pago", "Sicredi", "XP", "Nubank"]
)

arquivo_pdf = st.file_uploader(f"Arraste o PDF do {banco_escolhido} aqui", type="pdf")

def gerar_ofx(transacoes):
    data_hoje = datetime.now().strftime('%Y%m%d')
    ofx = """OFXHEADER:100
DATA:OFXSGML
VERSION:102
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE
<OFX><BANKMSGSRSV1><STMTTRNRS><STMTRS><CURDEF>BRL</CURDEF><BANKTRANLIST>
"""
    for t in transacoes:
        ofx += f"""<STMTTRN>
<TRNTYPE>OTHER</TRNTYPE>
<DTPOSTED>{data_hoje}</DTPOSTED>
<TRNAMT>{t['valor']}</TRNAMT>
<MEMO>{t['desc'][:32]}</MEMO>
</STMTTRN>
"""
    ofx += "</BANKTRANLIST></STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>"
    return ofx

if arquivo_pdf is not None:
    transacoes_encontradas = []
    
    with pdfplumber.open(arquivo_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                linhas = texto.split('\n')
                for linha in linhas:
                    # O robozinho procura: DATA (00/00) e VALOR (0,00)
                    tem_data = re.search(r'(\d{2}/\d{2})', linha)
                    tem_valor = re.search(r'(-?\d?\.?\d+,\d{2})', linha)
                    
                    if tem_data and tem_valor:
                        v = tem_valor.group(1).replace('.', '').replace(',', '.')
                        d = linha.replace(tem_data.group(1), '').replace(tem_valor.group(1), '').strip()
                        transacoes_encontradas.append({'valor': v, 'desc': d})

    if transacoes_encontradas:
        st.success(f"Li o extrato do {banco_escolhido} com sucesso! 🎉")
        st.balloons()
        
        ofx_data = gerar_ofx(transacoes_encontradas)
        
        st.download_button(
            label=f"📥 Baixar OFX para {banco_escolhido}",
            data=ofx_data,
            file_name=f"extrato_{banco_escolhido.lower().replace(' ', '_')}.ofx",
            mime="application/x-ofx"
        )
    else:
        st.error(f"Não consegui identificar os dados no formato do {banco_escolhido}. Verifique se o PDF está legível.")

st.info("💡 Lembre-se: Para o cliente, Crédito é negativo (-) e Débito é positivo (+).")
