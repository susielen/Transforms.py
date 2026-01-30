import streamlit as st
import pdfplumber
import re
import time
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Conversor OFX Inteligente", page_icon="💰")

# CSS para o visual minimalista e botão verde
st.markdown("""
    <style>
    div.stDownloadButton > button:first-child {
        background-color: #28a745;
        color: white;
        border-radius: 4px;
        border: none;
        padding: 6px 16px;
        font-size: 14px;
        font-weight: 500;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

st.title("🏦 Conversor OFX")

col1, col2 = st.columns([1, 2])

with col1:
    banco = st.selectbox("Banco:", [
        "Santander", "Sicoob", "Itaú", "BB", "Caixa", 
        "Inter", "Mercado Pago", "Sicredi", "XP", "Nubank", "Outro"
    ])

with col2:
    arquivo_pdf = st.file_uploader("", type="pdf")

if arquivo_pdf:
    # --- ANIMAÇÃO DE TRANSFORMAÇÃO ---
    with st.empty():
        # Exibe uma mensagem e uma animação (usando um emoji grande ou link de GIF)
        st.markdown("<h3 style='text-align: center;'>🤖 Robô processando o dinheiro...</h3>", unsafe_allow_html=True)
        # Você pode trocar este link por qualquer GIF de moedas que desejar
        st.image("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJueXZ6ZnduOHp1eHByZzZueXpueXpueXpueXpueXpueXpueXpueSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/L39V0i49H6qGvT48uT/giphy.gif", width=200)
        
        # Simula um pequeno tempo de "trabalho" para a animação aparecer
        time.sleep(2)
        
        transacoes = []
        with pdfplumber.open(arquivo_pdf) as pdf:
            for pagina in pdf.pages:
                texto = pagina.extract_text()
                if texto:
                    for linha in texto.split('\n'):
                        m_data = re.search(r'(\d{2}/\d{2})', linha)
                        m_valor = re.search(r'(-?\d?\.?\d+,\d{2})', linha)
                        if m_data and m_valor:
                            v = m_valor.group(1).replace('.', '').replace(',', '.')
                            d = linha.replace(m_data.group(1), '').replace(m_valor.group(1), '').strip()
                            transacoes.append({'v': v, 'd': d})
        st.empty() # Limpa a animação após terminar

    if transacoes:
        st.success(f"✅ {len(transacoes)} lançamentos transformados com sucesso!")
        
        # Gerador do OFX
        dt = datetime.now().strftime('%Y%m%d')
        ofx = f"OFXHEADER:100\nDATA:OFXSGML\nVERSION:102\nENCODING:USASCII\nCHARSET:1252\n<OFX><BANKMSGSRSV1><STMTTRNRS><STMTRS><CURDEF>BRL</CURDEF><BANKTRANLIST>\n"
        for t in transacoes:
            ofx += f"<STMTTRN><TRNTYPE>OTHER</TRNTYPE><DTPOSTED>{dt}</DTPOSTED><TRNAMT>{t['v']}</TRNAMT><MEMO>{t['d'][:32]}</MEMO></STMTTRN>\n"
        ofx += "</BANKTRANLIST></STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>"
        
        st.download_button(
            label="Baixar OFX",
            data=ofx,
            file_name=f"extrato_{banco.lower()}.ofx",
            mime="application/x-ofx"
        )
