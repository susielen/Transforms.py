import streamlit as st
import pandas as pd
import pdfplumber
import io
from datetime import datetime

st.set_page_config(page_title="Meu Conversor Mágico", page_icon="🏦")

st.title("🏦 Conversor de Extratos do Gê")
st.write("Transforme seu PDF em arquivos que o computador entende!")

# 1. Subir o arquivo
arquivo_pdf = st.file_uploader("Arraste seu PDF aqui", type="pdf")

if arquivo_pdf is not None:
    with pdfplumber.open(arquivo_pdf) as pdf:
        # Pega a primeira página e extrai a tabela
        dados = pdf.pages[0].extract_table()
    
    if dados:
        # Organiza os dados (Ignora a primeira linha se for cabeçalho)
        df = pd.DataFrame(dados[1:], columns=dados[0])
        st.success("Arquivo lido com sucesso! 🎉")
        st.dataframe(df) # Mostra a tabelinha na tela

        # --- BOTÃO EXCEL ---
        buffer_xlsx = io.BytesIO()
        with pd.ExcelWriter(buffer_xlsx, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        st.download_button("📥 Baixar Excel (.xlsx)", buffer_xlsx.getvalue(), "extrato.xlsx")

        # --- BOTÃO TXT ---
        buffer_txt = df.to_csv(index=False, sep='\t')
        st.download_button("📥 Baixar Texto (.txt)", buffer_txt, "extrato.txt")

        # --- BOTÃO OFX (A parte especial!) ---
        # Criando o texto do OFX
        ofx_conteudo = """OFXHEADER:100
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
        # Adicionando cada linha da tabela no OFX
        for idx, linha in df.iterrows():
            # Aqui a gente finge que a primeira coluna é data e a segunda é valor
            ofx_conteudo += f"""<STMTTRN>
<TRNTYPE>OTHER</TRNTYPE>
<DTPOSTED>{datetime.now().strftime('%Y%m%d')}</DTPOSTED>
<TRNAMT>{linha[1]}</TRNAMT>
<MEMO>{linha[0]}</MEMO>
</STMTTRN>
"""
        ofx_conteudo += "</BANKTRANLIST></STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>"
        
        st.download_button("📥 Baixar Banco (.ofx)", ofx_conteudo, "extrato.ofx")

    else:
        st.error("Puxa, não encontrei nenhuma tabela nesse PDF. 😢")
