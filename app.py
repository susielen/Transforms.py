import streamlit as st
import pandas as pd
import pdfplumber
import re
import io
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Conversor para Modelo Excel", page_icon="📊")

# Estilo do botão verde
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
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Gerador de Planilha Modelo")

# Escolha do Robô
tipo_robo = st.radio(
    "Escolha o robô:",
    ["Robô OFX", "Robô Excel (Modelo Sistema)"],
    horizontal=True
)

lista_bancos = ["Santander", "Sicoob", "Itaú", "Banco do Brasil", "Caixa", "Inter", "Mercado Pago", "Sicredi", "XP", "Nubank", "Outro"]
banco = st.selectbox("Banco:", lista_bancos)

arquivo_pdf = st.file_uploader("Suba o PDF do extrato:", type="pdf")

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
                        data = tem_data.group(1)
                        valor_str = tem_valor.group(1)
                        v_num = float(valor_str.replace('.', '').replace(',', '.'))
                        desc = linha.replace(data, '').replace(valor_str, '').strip()
                        
                        # Lógica para o Fornecedor (Banco):
                        # Se saiu dinheiro (< 0), é um CRÉDITO para o banco.
                        # Se entrou dinheiro (> 0), é um DÉBITO para o banco.
                        credito = abs(v_num) if v_num < 0 else 0
                        debito = v_num if v_num > 0 else 0
                        
                        transacoes.append({
                            "Data": data,
                            "Histórico": desc[:50],
                            "Documento": "", # Coluna Documento vazia como no modelo
                            "Débito": debito,
                            "Crédito": credito,
                            "Valor_Original": v_num # Usado apenas para o OFX
                        })

    if transacoes:
        st.info(f"Processado: {len(transacoes)} itens encontrados.")

        if tipo_robo == "Robô OFX":
            data_ofx = datetime.now().strftime('%Y%m%d')
            ofx = "OFXHEADER:100\nDATA:OFXSGML\nVERSION:102\nENCODING:USASCII\nCHARSET:1252\n<OFX><BANKMSGSRSV1><STMTTRNRS><STMTRS><CURDEF>BRL</CURDEF><BANKTRANLIST>"
            for t in transacoes:
                ofx += f"<STMTTRN><TRNTYPE>OTHER</TRNTYPE><DTPOSTED>{data_ofx}</DTPOSTED><TRNAMT>{t['Valor_Original']}</TRNAMT><MEMO>{t['Histórico']}</MEMO></STMTTRN>"
            ofx += "</BANKTRANLIST></STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>"
            st.download_button("📥 Baixar OFX", ofx, f"extrato_{banco.lower()}.ofx")

        else:
            # Monta exatamente no modelo enviado: Data, Histórico, Documento, Débito, Crédito
            df_final = pd.DataFrame(transacoes)[["Data", "Histórico", "Documento", "Débito", "Crédito"]]
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_final.to_excel(writer, index=False, sheet_name='Extrato')
            
            st.write("### Prévia da Planilha:")
            st.dataframe(df_final.head())
            
            st.download_button(
                label="📥 Baixar Planilha Modelo",
                data=output.getvalue(),
                file_name=f"modelo_extrato_{banco.lower()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.warning("Nenhum dado encontrado no arquivo.")

st.divider()
st.caption("Regra: Saída = Crédito (Banco) | Entrada = Débito (Banco)")
