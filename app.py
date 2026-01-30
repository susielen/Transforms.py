import streamlit as st
import pandas as pd
import pdfplumber
import io
from datetime import datetime

# Configuração da página (deixa o site com um nome e ícone bonitos)
st.set_page_config(page_title="Conversor Mágico", page_icon="🏦")

st.title("🏦 Conversor de Extratos do Gê")
st.write("Transforme seu PDF em arquivos que o computador entende (XLSX, TXT e OFX)!")

# 1. Lugar para colocar o arquivo
arquivo_pdf = st.file_uploader("Arraste seu PDF aqui", type="pdf")

if arquivo_pdf is not None:
    dados_finais = []
    
    with pdfplumber.open(arquivo_pdf) as pdf:
        for pagina in pdf.pages:
            # Tenta extrair como tabela primeiro
            tabela = pagina.extract_table()
            if tabela:
                dados_finais.extend(tabela)
            else:
                # Se falhar, tenta ler o texto bruto e organizar
                texto = pagina.extract_text()
                if texto:
                    linhas = texto.split('\n')
                    for linha in linhas:
                        dados_finais.append(linha.split())

    if dados_finais:
        # Criamos a nossa tabelinha (DataFrame)
        df = pd.DataFrame(dados_finais)
        
        st.success("Consegui ler o arquivo! 🎉")
        st.write("Veja uma prévia dos dados encontrados:")
        st.dataframe(df.head(10)) # Mostra só as 10 primeiras linhas para não travar

        st.divider()
        st.subheader("📥 Escolha como quer baixar:")

        # --- PREPARAÇÃO DO EXCEL ---
        buffer_xlsx = io.BytesIO()
        with pd.ExcelWriter(buffer_xlsx, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, header=False)
        st.download_button("📊 Baixar em Excel (.xlsx)", buffer_xlsx.getvalue(), "extrato_convertido.xlsx")

        # --- PREPARAÇÃO DO TXT ---
        buffer_txt = df.to_csv(index=False, sep='\t', header=False)
        st.download_button("📄 Baixar em Texto (.txt)", buffer_txt, "extrato_convertido.txt")

        # --- PREPARAÇÃO DO OFX (A língua do banco) ---
        ofx_cabecalho = """OFXHEADER:100
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
        corpo_ofx = ""
        for idx, linha in df.iterrows():
            if len(linha) >= 2: # Só adiciona se tiver pelo menos data e valor
                corpo_ofx += f"""<STMTTRN>
<TRNTYPE>OTHER</TRNTYPE>
<DTPOSTED>{datetime.now().strftime('%Y%m%d')}</DTPOSTED>
<TRNAMT>{str(linha[1]).replace(',', '.')}</TRNAMT>
<MEMO>{str(linha[0])}</MEMO>
</STMTTRN>
"""
        ofx_final = ofx_cabecalho + corpo_ofx + "</BANKTRANLIST></STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>"
        
        st.download_button("💰 Baixar para Banco (.ofx)", ofx_final, "extrato_convertido.ofx")
        
    else:
        st.error("Puxa, ainda não consegui ler os dados. O PDF pode estar protegido ou ser apenas uma imagem. 😢")

st.info("Lembre-se: No seu controle, se o dinheiro entra é positivo (+), se sai é negativo (-).")
