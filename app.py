import streamlit as st
import requests
import os
import json
import time
import concurrent.futures
import pandas as pd
import re
import random
from io import BytesIO
from groq import Groq
import urllib3

# Desabilita avisos de SSL inseguro para não poluir o log
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="LEANTTRO | Buscador de Oportunidades", layout="wide", page_icon="🚀")

# --- ESTILO VISUAL (IDENTIDADE LEANTTRO NEON - MANTIDA INTACTA) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600;700&family=Chakra+Petch:wght@400;700&display=swap');
    
    header {
        visibility: hidden;
        height: 0px;
    }
    div[data-testid="stHeader"] {
        visibility: hidden;
        height: 0px;
    }
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
    
    .stApp { background-color: #050505; color: #E5E7EB; font-family: 'Kanit', sans-serif; }
    
    section[data-testid="stSidebar"] {
        background-color: #2e2e2e !important;
    }
    
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] label {
        color: #ffffff !important;
    }

    .stCode pre, .stCode code {
        background-color: #111 !important;
        color: #D2FF00 !important;
        border: 1px solid #444 !important;
    }

    .stTextInput label, .stSelectbox label, .stNumberInput label, .stTextArea label {
        color: #ffffff !important;
        font-size: 14px !important;
    }
    
    .custom-info-box {
        background-color: #1a1a1a;
        border-left: 4px solid #D2FF00;
        padding: 15px;
        color: #ffffff !important;
        font-size: 14px;
        margin-bottom: 20px;
        border-radius: 4px;
        border: 1px solid #444;
        line-height: 1.5;
    }

    div.stButton > button { 
        background-color: #D2FF00; color: #000; border: none; 
        border-radius: 4px; font-weight: 800; width: 100%; 
        text-transform: uppercase; font-style: italic;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover { 
        background-color: #ffffff; 
        box-shadow: 0 0 15px rgba(210, 255, 0, 0.5);
        transform: skewX(-5deg);
    }
    
    .stTextInput > div > div > input { color: #fff; background-color: #111; border: 1px solid #333; }
    .stNumberInput > div > div > input { color: #fff; background-color: #111; border: 1px solid #333; }
    .stSelectbox > div > div { background-color: #111; color: white; border: 1px solid #333; }
    .stTextArea > div > div > textarea { color: #fff; background-color: #111; border: 1px solid #333; }

    .lead-card {
        background-color: #0a0a0a !important; padding: 25px; border-radius: 8px;
        border: 1px solid #222; margin-bottom: 20px;
        position: relative; overflow: hidden;
    }
    .lead-card:hover { border-color: #D2FF00; }
    
    .score-hot { border-left: 4px solid #D2FF00; } 
    .score-warm { border-left: 4px solid #fff; }    
    .score-cold { border-left: 4px solid #333; }    

    .lead-title { font-family: 'Chakra Petch', sans-serif; font-size: 20px; font-weight: bold; color: #fff; margin-bottom: 5px; text-decoration: none; display: block; }
    .lead-title:hover { color: #D2FF00; }
    
    .tag-nicho { 
        background-color: #1a1a1a; color: #bbb; padding: 2px 8px; 
        border-radius: 4px; font-size: 10px; font-family: monospace;
        border: 1px solid #333; margin-right: 5px;
    }

    .recommendation-box {
        background-color: #111; border: 1px dashed #444; 
        padding: 10px; margin-top: 15px; border-radius: 4px;
    }
    .rec-title { color: #D2FF00; font-weight: bold; font-size: 12px; font-family: monospace; }
    .rec-text { font-size: 13px; color: #ddd; margin-top: 4px; }
    
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #111; border: 1px solid #333; color: #888; border-radius: 4px; }
    .stTabs [aria-selected="true"] { background-color: #D2FF00 !important; color: #000 !important; font-weight: bold; }

    h1, h2, h3 { font-family: 'Chakra Petch', sans-serif; font-style: italic; }
    a { text-decoration: none !important; }
</style>
""", unsafe_allow_html=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "") 
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")

SUGESTOES_STRATEGICAS = {
    "Sites de Freelance (Workana/99)": [
        "procuro criador de cardápio digital", 
        "preciso de designer para logo urgente", 
        "indicação para fazer menu de whatsapp", 
        "alguém para criar site simples hoje", 
        "procuro arte rápida para lanchonete" 
    ],
    "LinkedIn (Postagens/Feed)": [
        "preciso de cardápio digital",
        "busco designer para logo",
        "indicação criador de catálogo" , 
        "alguém para fazer menu whatsapp",
        "preciso de site simples urgente", 
        "urgente arte para redes sociais" 
    ],
    "LinkedIn (Empresas)": [
        "Hamburgueria Delivery", 
        "Confeitaria", 
        "Pizzaria",
        "Loja de Roupas", 
        "Marmitaria" 
    ],
    "Instagram/Negócios (Estratégia Maps)": [
        "hamburgueria delivery", 
        "doceria gourmet", 
        "loja de roupas", 
        "marmitaria", 
        "artesanato", 
        "confeitaria artesanal" 
    ],
    "Google (Geral)": [
        "contratar criador de cardápio digital",
        "designer freelancer logo urgente",
        "fazer catálogo whatsapp",
        "orçamento site simples",
        "preciso de arte para lanchonete"
    ]
}

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Leads')
    return output.getvalue()

def extrair_email(texto):
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', str(texto))
    return match.group(0) if match else None

def extrair_whatsapp(texto):
    padrao = r'(?:(?:\+|00)?55\s?)?(?:\(?([1-9][0-9])\)?\s?)?(?:((?:9\d|[2-9])\d{3})\-?(\d{4}))'
    match = re.search(padrao, str(texto))
    if match:
        ddd, parte1, parte2 = match.groups()
        if not ddd: ddd = "11" 
        numero_limpo = f"55{ddd}{parte1}{parte2}".replace(" ", "").replace("-", "")
        return numero_limpo
    return None

def limpar_nome_insta(titulo):
    if "•" in titulo: return titulo.split("•")[0].strip()
    if "-" in titulo: return titulo.split("-")[0].strip()
    return titulo[:50]

def search_google_serper(query, period, num_results=10):
    url = "https://google.serper.dev/search"
    payload_dict = {
        "q": query,
        "num": num_results,
        "gl": "br", 
        "hl": "pt-br"
    }
    if period:
        payload_dict["tbs"] = period
    payload = json.dumps(payload_dict)
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code != 200:
            return []
        return response.json().get("organic", [])
    except Exception:
        return []

def analyze_lead_groq(title, snippet, link, groq_key):
    if not groq_key: 
        return {"score": 0, "autor": "Desc.", "produto_recomendado": "ERRO CHAVE", "argumento_venda": "Sem chave Groq"}
    client = Groq(api_key=groq_key)
    system_prompt = f"""
    ATUE COMO: Head de Vendas da 'Leanttro Digital', focado em fechar negócios RÁPIDOS hoje.
    SEUS PRODUTOS (LEANTTRO.COM):
    1. CATÁLOGOS E MENUS: "Cardápio digital", "Catálogo para WhatsApp", "Menu online".
    2. DESIGN RÁPIDO: "Logo urgente", "Arte para lanchonete", "Post para redes sociais".
    3. SITES SIMPLES: "Site rápido", "Link na bio estruturado", "Landing page simples".
    TAREFAS:
    1. Identifique o NOME e o TIPO DE OPORTUNIDADE.
    2. CALCULE O SCORE (0-100).
    SAÍDA JSON OBRIGATÓRIA:
    {{
        "autor": "Nome (ou Empresa)",
        "score": (0-100),
        "resumo_post": "Resumo em 10 palavras",
        "produto_recomendado": "Serviço Leanttro",
        "argumento_venda": "Argumento matador"
    }}
    """
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"TITULO: {title}\nSNIPPET: {snippet}\nLINK: {link}"}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception:
        return {"score": 0, "autor": "Erro", "produto_recomendado": "Erro IA", "argumento_venda": "Falha na análise"}

def process_single_item(item):
    titulo = item.get('title', '')
    link = item.get('link', '')
    snippet = item.get('snippet', '')
    data_pub = item.get('date', 'Data n/d')
    analise = analyze_lead_groq(titulo, snippet, link, GROQ_API_KEY)
    return {
        "item": item,
        "analise": analise,
        "titulo": titulo,
        "link": link,
        "snippet": snippet,
        "data_pub": data_pub
    }

with st.sidebar:
    st.markdown(f"<h1 style='color: #fff; text-align: center; font-style: italic;'>LEAN<span style='color:#D2FF00'>TTRO</span>.<br><span style='font-size:14px; color:#fff'>Intelligence Hub</span></h1>", unsafe_allow_html=True)
    st.divider()
    if GROQ_API_KEY: st.success("🟢 IA Conectada") 
    else: st.error("🔴 Falta GROQ KEY")
    if SERPER_API_KEY: st.success("🟢 Google Search Ativo")
    else: st.error("🔴 Falta SERPER KEY")
    st.divider()
    st.markdown("### 🎯 Modo de Caça")
    st.markdown("""
    <div class="custom-info-box">
        <b>Prioridade Leanttro:</b><br>
        1. <b>Projetos Rápidos (🔥):</b> Catálogos e Logos Urgentes.<br>
        2. <b>Projetos Maiores (⚠️):</b> Sistemas e E-commerces.
    </div>
    """, unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📡 RADAR DE OPORTUNIDADES (IA)", "⛏️ MINERADOR SNIPER (B2B + WHATSAPP)"])

with tab1:
    st.markdown("<h2 style='color:white'>RADAR DE <span style='color:#D2FF00'>OPORTUNIDADES</span></h2>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns([3, 3, 2, 1])
    with c1:
        origem = st.selectbox("Onde buscar?", list(SUGESTOES_STRATEGICAS.keys()))
    with st.sidebar:
        st.markdown("### 💡 Sugestões para esta Fonte")
        dicas_atuais = SUGESTOES_STRATEGICAS.get(origem, [])
        for dica in dicas_atuais:
            st.code(dica, language="text")
    with c2:
        termo = st.text_input("Termo ou Nicho:", placeholder="Copie uma sugestão ao lado...")
    with c3:
        tempo = st.selectbox("Período:", ["Últimas 24 Horas", "Última Semana", "Último Mês", "Qualquer data"])
    with c4:
        qtd = st.number_input("Qtd", 1, 50, 8)
    st.write("##")
    btn = st.button("RASTREAR OPORTUNIDADES", key="btn_radar")
    if btn and termo:
        if not (GROQ_API_KEY and SERPER_API_KEY):
            st.error("⚠️ Configure as chaves de API!")
        else:
            periodo_api = ""
            if "24 Horas" in tempo: periodo_api = "qdr:d"
            elif "Semana" in tempo: periodo_api = "qdr:w"
            elif "Mês" in tempo: periodo_api = "qdr:m"
            query_final = termo
            if origem == "LinkedIn (Empresas)":
                query_final = f'site:linkedin.com/company "{termo}"'
            elif origem == "LinkedIn (Postagens/Feed)":
                query_final = f'site:linkedin.com/posts "{termo}"'
            elif origem == "Sites de Freelance (Workana/99)":
                query_final = f'(site:workana.com OR site:99freelas.com.br) "{termo}"'
            elif origem == "Instagram/Negócios (Estratégia Maps)":
                query_final = f'site:instagram.com "{termo}"'
            st.caption(f"🔎 Buscando: `{query_final}` | Fonte: `{origem}`")
            resultados = search_google_serper(query_final, periodo_api, qtd)
            if not resultados:
                st.warning("Nenhum sinal encontrado.")
            else:
                bar_text = st.empty()
                prog = st.progress(0)
                processed_results = []
                data_export = []
                bar_text.text("🕵️ IA analisando leads...")
                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    future_to_item = {executor.submit(process_single_item, item): item for item in resultados}
                    completed = 0
                    for future in concurrent.futures.as_completed(future_to_item):
                        try:
                            data = future.result()
                            processed_results.append(data)
                            analise_data = data['analise']
                            data_export.append({
                                "Titulo": data['titulo'],
                                "Link": data['link'],
                                "Score": analise_data.get('score'),
                                "Autor": analise_data.get('autor'),
                                "Resumo": analise_data.get('resumo_post'),
                                "Produto": analise_data.get('produto_recomendado'),
                                "Argumento": analise_data.get('argumento_venda')
                            })
                        except Exception:
                            pass
                        completed += 1
                        prog.progress(completed / len(resultados))
                bar_text.empty() 
                processed_results.sort(key=lambda x: x['analise'].get('score', 0), reverse=True)
                if data_export:
                    df_radar = pd.DataFrame(data_export)
                    st.download_button(label="📥 BAIXAR RELATÓRIO", data=to_excel(df_radar), file_name="radar_leanttro.xlsx", key="dl_radar")
                for p in processed_results:
                    analise = p['analise']
                    score = analise.get('score', 0)
                    autor = analise.get('autor', 'Desconhecido')
                    link = p['link']
                    titulo = p['titulo']
                    snippet = p['snippet']
                    data_pub = p['data_pub']
                    css_class = "score-cold"
                    icon = "❄️"
                    if score >= 80:
                        css_class = "score-hot"
                        icon = "🔥 HOT"
                    elif score >= 50:
                        css_class = "score-warm"
                        icon = "⚠️ MORNO"
                    card_html = f"""
                    <div class="lead-card {css_class}">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span style="color: #D2FF00; font-weight:bold; font-family:monospace;">{icon} SCORE: {score}</span>
                            <span class="tag-nicho">Autor: {autor}</span>
                        </div>
                        <a href="{link}" target="_blank" style="background:#222; color:#fff; padding:5px 10px; text-decoration:none; border-radius:4px; font-size:12px;">VER POST 🔗</a>
                    </div>
                    <div style="margin-top:10px;">
                        <a href="{link}" target="_blank" class="lead-title">{titulo}</a>
                    </div>
                    <div style="color:#666; font-size:11px; margin-bottom:5px;">🕒 {data_pub} | {snippet[:200]}...</div>
                    <div class="recommendation-box">
                        <div class="rec-title">// ESTRATÉGIA:</div>
                        <div style="color: #fff; font-weight:bold;">OFERTAR: {analise.get('produto_recomendado', 'N/A').upper()}</div>
                        <div class="rec-text"><span style="color:#666">RESUMO:</span> {analise.get('resumo_post', '')}</div>
                        <div class="rec-text" style="color:#D2FF00; margin-top:5px;">💡 " {analise.get('argumento_venda', '')} "</div>
                    </div>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)

with tab2:
    st.markdown("<h2 style='color:white'>MINERADOR <span style='color:#D2FF00'>LOCAL</span></h2>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: nicho = st.text_input("Nicho:", value="Advocacia")
    with c2: cidade = st.text_input("Cidade Base:", value="São Paulo")
    bairros_txt = st.text_area("Bairros:", value="Centro, Pinheiros", height=100)
    if "leads_zap" not in st.session_state: st.session_state["leads_zap"] = []
    if st.button("🚀 INICIAR VARREDURA", key="btn_zap_mine"):
        lista_bairros = [b.strip() for b in bairros_txt.split(',') if b.strip()]
        novos_leads = []
        progress_text = st.empty()
        bar = st.progress(0)
        for i, bairro in enumerate(lista_bairros):
            progress_text.text(f"📡 Escaneando: {bairro}...")
            queries = [f'site:instagram.com "{nicho}" "{bairro}" "{cidade}" "whatsapp"']
            for q in queries:
                resultados = search_google_serper(q, period="", num_results=15)
                for r in resultados:
                    texto = (r.get('title', '') + " " + r.get('snippet', '')).lower()
                    zap = extrair_whatsapp(texto)
                    if zap:
                        exists = any(l['Whatsapp'] == zap for l in st.session_state["leads_zap"])
                        if not exists:
                            novos_leads.append({"Empresa": limpar_nome_insta(r.get('title', '')), "Nicho": nicho, "Bairro": bairro, "Whatsapp": zap, "Link": r.get('link')})
            bar.progress((i + 1) / len(lista_bairros))
            time.sleep(0.5)
        st.session_state["leads_zap"].extend(novos_leads)
        st.success(f"🔥 {len(novos_leads)} NOVOS LEADS!")

    if st.session_state["leads_zap"]:
        df = pd.DataFrame(st.session_state["leads_zap"])
        st.dataframe(df, width='stretch')
        if st.button("🔥 DISPARAR CAMPANHA"):
            st.info("Iniciando disparos...")
            sucessos, erros = 0, 0
            msg_bar = st.progress(0)
            for idx, row in df.iterrows():
                try:
                    msg = f"Olá {row['Empresa'].split(' ')[0]}, tudo bem? Vi que atendem no {row['Bairro']}. Seu site está fora do ar?"
                    # Adicionado verify=False para ignorar erro de certificado SSL
                    res = requests.post("https://wppapi.leanttro.com/disparar", json={"number": row['Whatsapp'], "message": msg}, timeout=10, verify=False)
                    if res.status_code == 200: sucessos += 1
                    else: erros += 1
                except Exception: erros += 1
                msg_bar.progress((idx + 1) / len(df))
                time.sleep(10)
            st.success(f"Fim! ✅ {sucessos} | ❌ {erros}")