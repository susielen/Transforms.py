import streamlit as st
import pdfplumber
import re
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Conversor OFX Profissional", page_icon="🏦")

# Estilo para o botão de download verde e discreto
st.markdown("""
    <style>
    div.stDownloadButton > button:first-child {
        background-color: #28a745;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 5px 15px;
        font-size: 14px;
        font-weight: 500;
        transition: 0.2s;
    }
    div.stDownloadButton > button:first-child:hover {
        background-color: #218838;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏦 Conversor de Extrato para OFX")
st.write("Selecione o banco e transforme seu PDF em um arquivo para o banco.")

# Lista de Bancos que você solicitou
lista_bancos = [
    "Santander", "Sicoob", "Itaú", "Banco do Brasil", "Caixa", 
    "Inter", "Mercado Pago", "Sicredi", "XP", "Nubank", "Outro"
]

banco_escolhido = st.selectbox("Banco do Extrato:", lista_bancos)

arquivo_pdf = st.file_uploader(f"Suba o PDF do {banco_escolhido} aqui", type="pdf")

def gerar_conteudo_ofx(transacoes):
    """Gera a estrutura do arquivo OFX conforme o padrão bancário"""
    data_hoje = datetime.now().strftime('%Y%m%d')
    ofx = f"""OFXHEADER:100
DATA:OFXSGML
VERSION:102
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE
<OFX>
<BANKMSGSRSV1>
<STMTTRNRS>
<STMTRS>
<CURDEF>BRL</CURDEF>
<BANKTRANLIST>
"""
    for t in transacoes:
        ofx += f"""<STMTTRN>
<TRNTYPE>OTHER</TRNTYPE>
<DTPOSTED>{data_hoje}</DTPOSTED>
<TRNAMT>{t['valor']}</TRNAMT>
<MEMO>{t['desc'][:32]}</MEMO>
</STMTTRN>
"""
    ofx += """</BANKTRANLIST>
</STMTRS>
</STMTTRNRS>
</BANKMSGSRSV1>
</OFX>"""
    return ofx

if arquivo_pdf is not None:
    transacoes_detectadas = []
    
    with pdfplumber.open(arquivo_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                linhas = texto.split('\n')
                for linha in linhas:
                    # O robô procura por: Data (00/00) e Valor (0,00 ou 0.000,00)
                    tem_data = re.search(r'(\d{2}/\d{2})', linha)
                    tem_valor = re.search(r'(-?\d?\.?\d+,\d{2})', linha)
                    
                    if tem_data and tem_valor:
                        # Limpa o valor para o formato americano (1234.56) que o OFX usa
                        valor_limpo = tem_valor.group(1).replace('.', '').replace(',', '.')
                        # Pega o que sobrou da linha como descrição
                        descricao = linha.replace(tem_data.group(1), '').replace(tem_valor.group(1), '').strip()
                        
                        transacoes_detectadas.append({
                            'valor': valor_limpo,
                            'desc': descricao
                        })

    if transacoes_detectadas:
        st.info(f"Sucesso! Encontrei {len(transacoes_detectadas)} lançamentos no extrato do {banco_escolhido}.")
        
        conteudo_ofx = gerar_conteudo_ofx(transacoes_detectadas)
        
        # Botão discreto para baixar
        st.download_button(
            label="📥 Baixar Arquivo OFX",
            data=conteudo_ofx,
            file_name=f"extrato_{banco_escolhido.lower().replace(' ', '_')}.ofx",
            mime="application/x-ofx"
        )
    else:
        st.warning("Não consegui identificar transações. Verifique se o PDF está legível e não é uma foto.")

st.divider()
st.caption("Nota: Este robô gera arquivos no padrão OFX para integração bancária.")
