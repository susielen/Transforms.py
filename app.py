import streamlit as st
import pandas as pd
import pdfplumber
import re
import io

st.set_page_config(page_title="Importação de Extrato", layout="wide")

# Estilo do botão verde
st.markdown("""
    <style>
    div.stDownloadButton > button:first-child {
        background-color: #28a745; color: white; border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📑 Importação de Extrato Bancário")

# --- MEMÓRIA CONTÁBIL ---
if 'memoria' not in st.session_state:
    st.session_state.memoria = {}

# --- INTERFACE ---
col1, col2 = st.columns(2)
with col1:
    banco = st.selectbox("Banco:", ["Santander", "Sicoob", "Itaú", "BB", "Caixa", "Inter", "Nubank", "Outro"])
with col2:
    competencia = st.text_input("Competência (Ex: 01/01/2023):", "01/01/2023")

arquivo_pdf = st.file_uploader("Suba o PDF do extrato:", type="pdf")

if arquivo_pdf:
    dados = []
    with pdfplumber.open(arquivo_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                for linha in texto.split('\n'):
                    tem_data = re.search(r'(\d{2}/\d{2})', linha)
                    tem_valor = re.search(r'(-?\d?\.?\d+,\d{2})', linha)
                    
                    if tem_data and tem_valor:
                        data = tem_data.group(1) + "/" + competencia.split('/')[-1]
                        valor_str = tem_valor.group(1)
                        v_num = float(valor_str.replace('.', '').replace(',', '.'))
                        hist = linha.replace(tem_data.group(1), '').replace(valor_str, '').strip()[:50]
                        
                        # Lógica da Imagem:
                        # Se entrou (>0) -> DEBITO (Soma)
                        # Se saiu (<0) -> CREDITO (Subtrai)
                        debito = abs(v_num) if v_num > 0 else ""
                        credito = abs(v_num) if v_num < 0 else ""
                        
                        # Busca na memória
                        conta = st.session_state.memoria.get(hist, "")
                        
                        dados.append({
                            "Data": data,
                            "Historico": hist,
                            "Conta Contábil": conta,
                            "Documento": "",
                            "Valor Debito (Soma)": debito,
                            "Valor Credito (Subtrai)": credito
                        })

    if dados:
        df = pd.DataFrame(dados)
        st.write("### Edite as Contas Contábeis:")
        # Tabela editável para o usuário preencher
        df_editado = st.data_editor(df, num_rows="dynamic", use_container_width=True)

        if st.button("💾 Ensinar Contas ao Robô"):
            for _, r in df_editado.iterrows():
                if r["Conta Contábil"]:
                    st.session_state.memoria[r["Historico"]] = r["Conta Contábil"]
            st.success("Memória atualizada!")

        # Criar o Excel no formato da imagem
        output = io.BytesIO()
        # Aqui montamos o layout com cabeçalho igual à imagem
        df_excel = df_editado[["Data", "Historico", "Documento", "Valor Debito (Soma)", "Valor Credito (Subtrai)", "Conta Contábil"]]
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_excel.to_excel(writer, index=False, startrow=4) # Deixa espaço para o cabeçalho
            # O código acima gera o corpo, o cabeçalho pode ser ajustado conforme a necessidade do sistema
            
        st.download_button("📥 Baixar Planilha para Sistema", output.getvalue(), f"importacao_{banco}.xlsx")
