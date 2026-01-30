import streamlit as st
import pdfplumber
import re
import io
from datetime import datetime

# Configuração da página para um visual mais amplo e moderno
st.set_page_config(
    page_title="Conversor OFX Pro", 
    page_icon="🏦", 
    layout="centered"
)

# Estilização CSS para deixar o layout "bonitão"
st.markdown("""
    <style>
    /* Cor de fundo e fontes */
    .main {
        background-color: #f8f9fa;
    }
    /* Estilo do Título */
    .main-title {
        color: #1e3a8a;
        font-size: 40px;
        font-weight: 700;
        text-align: center;
        margin-bottom: 10px;
    }
    /* Subtítulo */
    .sub-title {
        color: #64748b;
        text-align: center;
        margin-bottom: 30px;
    }
    /* Botão de Download personalizado */
    div.stDownloadButton > button:first-child {
        background-color: #10b981;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 12px 30px;
        font-size: 16px;
        font-weight: 600;
        width: 100%;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: all 0.3s;
    }
    div.stDownloadButton > button:first-child:hover {
        background-color: #059669;
        transform: translateY(-2px);
    }
    /* Estilização da caixa de upload */
    section[data-testid="stFileUploadDropzone"] {
        border: 2px dashed #cbd5e1;
        border-radius: 12px;
        background-color: white;
    }
    </style>
""", unsafe_allow_html=True)

# Cabeçalho formatado
st.markdown('<p class="main-title">🏦 Conversor OFX Pro</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Transforme seus extratos PDF em arquivos OFX prontos para o sistema em segundos.</p>', unsafe_allow_html=True)

# Organização em colunas para a seleção
col1, col2 = st.columns([1, 1])

with col1:
    lista_bancos = [
        "Santander", "Sicoob", "Itaú", "Banco do Brasil", "Caixa", 
        "Inter", "Mercado Pago", "Sicredi", "XP", "Nubank", "Outro"
    ]
    banco_escolhido = st.selectbox("Selecione o Banco:", lista_bancos)

with col2:
    st.info(f"O arquivo será salvo como: \n`extrato_{banco_escolhido.lower()}.ofx`")

# Área de Upload com destaque
st.markdown("### 📄 Passo 1: Envie seu arquivo")
arquivo_pdf = st.file_uploader("", type="pdf", help="Arraste ou selecione o PDF original do banco.")

def gerar_ofx(transacoes):
    data_hoje = datetime.now().strftime('%Y%m%d')
    ofx = f"""OFXHEADER:100\nDATA:OFXSGML\nVERSION:102\nENCODING:USASCII\nCHARSET:1252\n<OFX><BANKMSGSRSV1><STMTTRNRS><STMTRS><CURDEF>BRL</CURDEF><BANKTRANLIST>\n"""
    for t in transacoes:
        ofx += f"<STMTTRN><TRNTYPE>OTHER</TRNTYPE><DTPOSTED>{data_hoje}</DTPOSTED><TRNAMT>{t['valor']}</TRNAMT><MEMO>{t['desc'][:32]}</MEMO></STMTTRN>\n"
    ofx += "</BANKTRANLIST></STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>"
    return ofx

if arquivo_pdf:
    with st.spinner('O robô está lendo o PDF...'):
        transacoes = []
        with pdfplumber.open(arquivo_pdf) as pdf:
            for pagina in pdf.pages:
                texto = pagina.extract_text()
                if texto:
                    for linha in texto.split('\n'):
                        tem_data = re.search(r'(\d{2}/\d{2})', linha)
                        tem_valor = re.search(r'(-?\d?\.?\d+,\d{2})', linha)
                        if tem_data and tem_valor:
                            v_limpo = tem_valor.group(1).replace('.', '').replace(',', '.')
                            desc = linha.replace(tem_data.group(1), '').replace(tem_valor.group(1), '').strip()
                            transacoes.append({'valor': v_limpo, 'desc': desc})

        if transacoes:
            st.markdown("---")
            st.markdown("### 📥 Passo 2: Baixe o resultado")
            
            # Container visual para o sucesso
            st.success(f"Tudo pronto! Identificamos **{len(transacoes)}** transações no seu extrato.")
            
            # Mostra uma prévia elegante em tabela
            with st.expander("👁️ Ver prévia dos dados"):
                st.table(transacoes[:5]) # Mostra apenas as 5 primeiras para não poluir
            
            conteudo_ofx = gerar_ofx(transacoes)
            
            st.download_button(
                label="BAIXAR ARQUIVO OFX AGORA",
                data=conteudo_ofx,
                file_name=f"extrato_{banco_escolhido.lower()}.ofx",
                mime="application/x-ofx"
            )
        else:
            st.error("Não encontramos transações. O PDF pode estar protegido ou ser uma imagem.")

# Rodapé minimalista
st.markdown("---")
st.caption("Central de Conversão | © 2026 - Desenvolvido para eficiência contábil.")
