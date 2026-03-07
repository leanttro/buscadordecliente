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

# --- FIX SSL: Ignora avisos de certificados autoassinados ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="LEANTTRO | Buscador de Oportunidades", layout="wide", page_icon="🚀")

# --- ESTILO VISUAL (IDENTIDADE LEANTTRO NEON - MANTIDA INTACTA) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600;700&family=Chakra+Petch:wght@400;700&display=swap');
    
    /* --- FIX: REMOVER BARRA BRANCA DO TOPO --- */
    header {
        visibility: hidden;
        height: 0px;
    }
    div[data-testid="stHeader"] {
        visibility: hidden;
        height: 0px;
    }
    /* Ajusta o padding para o conteúdo subir e ocupar o espaço vazio */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
    
    /* --- CONFIGURAÇÃO GERAL --- */
    .stApp { background-color: #050505; color: #E5E7EB; font-family: 'Kanit', sans-serif; }
    
    /* --- BARRA LATERAL (SIDEBAR) --- */
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

    /* --- CORREÇÃO DE VISIBILIDADE: CAIXAS DE CÓDIGO (st.code) --- */
    .stCode pre, .stCode code {
        background-color: #111 !important;
        color: #D2FF00 !important; /* Verde Neon */
        border: 1px solid #444 !important;
    }

    /* --- TEXTOS/LABELS DOS INPUTS (BRANCO) --- */
    .stTextInput label, .stSelectbox label, .stNumberInput label, .stTextArea label {
        color: #ffffff !important;
        font-size: 14px !important;
    }
    
    /* Caixa de Informação Customizada */
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

    /* Botão Principal Neon */
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
    
    /* Inputs */
    .stTextInput > div > div > input { color: #fff; background-color: #111; border: 1px solid #333; }
    .stNumberInput > div > div > input { color: #fff; background-color: #111; border: 1px solid #333; }
    .stSelectbox > div > div { background-color: #111; color: white; border: 1px solid #333; }
    .stTextArea > div > div > textarea { color: #fff; background-color: #111; border: 1px solid #333; }

    /* Card do Lead */
    .lead-card {
        background-color: #0a0a0a !important; padding: 25px; border-radius: 8px;
        border: 1px solid #222; margin-bottom: 20px;
        position: relative; overflow: hidden;
    }
    .lead-card:hover { border-color: #D2FF00; }
    
    /* Scores */
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
    
    /* ESTILO DAS ABAS (TABS) */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #111; border: 1px solid #333; color: #888; border-radius: 4px; }
    .stTabs [aria-selected="true"] { background-color: #D2FF00 !important; color: #000 !important; font-weight: bold; }

    h1, h2, h3 { font-family: 'Chakra Petch', sans-serif; font-style: italic; }
    a { text-decoration: none !important; }
</style>
""", unsafe_allow_html=True)

# --- CARREGAR CHAVES ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "") 
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")

# --- ESTRATÉGIA DE SUGESTÕES (ATUALIZADA PARA DINHEIRO RÁPIDO) ---
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

# --- FUNÇÕES AUXILIARES ---

def to_excel(df):
    """Converte DataFrame para bytes de Excel para download"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Leads')
    return output.getvalue()

def extrair_email(texto):
    """Extrai e-mail de um texto usando Regex"""
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', str(texto))
    return match.group(0) if match else None

def extrair_whatsapp(texto):
    """
    Regex agressivo para pegar celulares do Brasil (com ou sem 55, com ou sem parênteses).
    Foca em números que começam com 9 (celulares).
    """
    padrao = r'(?:(?:\+|00)?55\s?)?(?:\(?([1-9][0-9])\)?\s?)?(?:((?:9\d|[2-9])\d{3})\-?(\d{4}))'
    match = re.search(padrao, str(texto))
    
    if match:
        ddd, parte1, parte2 = match.groups()
        if not ddd: ddd = "11" 
        numero_limpo = f"55{ddd}{parte1}{parte2}".replace(" ", "").replace("-", "")
        return numero_limpo
    return None

def limpar_nome_insta(titulo):
    """Limpa o título do Instagram/Social"""
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
    except Exception as e:
        return []

def analyze_lead_groq(title, snippet, link, groq_key):
    """Analisa o post e tenta extrair o autor e contexto"""
    if not groq_key: 
        return {"score": 0, "autor": "Desc.", "produto_recomendado": "ERRO CHAVE", "argumento_venda": "Sem chave Groq"}
    
    client = Groq(api_key=groq_key)
    
    system_prompt = f"""
    ATUE COMO: Head de Vendas da 'Leanttro Digital', focado em fechar negócios RÁPIDOS hoje.
    
    SEUS PRODUTOS (LEANTTRO.COM) - PRIORIDADE 1 (DINHEIRO RÁPIDO HOJE):
    1. CATÁLOGOS E MENUS: "Cardápio digital", "Catálogo para WhatsApp", "Menu online".
    2. DESIGN RÁPIDO: "Logo urgente", "Arte para lanchonete", "Post para redes sociais".
    3. SITES SIMPLES: "Site rápido", "Link na bio estruturado", "Landing page simples".
    
    OBJETIVO SECUNDÁRIO - PRIORIDADE 2 (PROJETOS MAIORES):
    - "E-commerce completo", "Sistemas complexos", "Automação", "Dashboard".
    
    TAREFAS:
    1. Identifique o NOME e o TIPO DE OPORTUNIDADE.
    2. CALCULE O SCORE:
       - URGENTE/RÁPIDO (Catálogo, Logo, Site simples para HOJE) = SCORE ALTO (80-100). 🔥
       - PROJETO MAIOR (E-commerce, Sistema, Vaga) = SCORE MÉDIO (50-79). ⚠️
       - LIXO/IRRELEVANTE = SCORE BAIXO (0-49). ❄️
    
    SAÍDA JSON OBRIGATÓRIA:
    {{
        "autor": "Nome (ou Empresa)",
        "score": (0-100),
        "resumo_post": "Resumo em 10 palavras",
        "produto_recomendado": "Serviço Leanttro (Catálogo, Logo, Site Simples)",
        "argumento_venda": "Foque em entrega IMEDIATA e facilidade. Ex: 'Entrego seu catálogo rodando hoje mesmo no WhatsApp'."
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
    except Exception as e:
        return {"score": 0, "autor": "Erro", "produto_recomendado": "Erro IA", "argumento_venda": "Falha na análise"}

def process_single_item(item):
    """Função wrapper para rodar em paralelo"""
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

# --- INTERFACE PRINCIPAL ---

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

# ABA 1: O SEU BUSCADOR ORIGINAL (IA + SERPER)
with tab1:
    st.markdown("<h2 style='color:white'>RADAR DE <span style='color:#D2FF00'>OPORTUNIDADES</span></h2>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns([3, 3, 2, 1])
    with c1: origem = st.selectbox("Onde buscar?", list(SUGESTOES_STRATEGICAS.keys()))
    with st.sidebar:
        st.markdown("### 💡 Sugestões para esta Fonte")
        dicas_atuais = SUGESTOES_STRATEGICAS.get(origem, [])
        for dica in dicas_atuais:
            st.code(dica, language="text")
    with c2: termo = st.text_input("Termo ou Nicho:", placeholder="Copie uma sugestão ao lado...")
    with c3: tempo = st.selectbox("Período:", ["Últimas 24 Horas", "Última Semana", "Último Mês", "Qualquer data"])
    with c4: qtd = st.number_input("Qtd", 1, 50, 8)
    st.write("##")
    btn = st.button("RASTREAR OPORTUNIDADES", key="btn_radar")
    if btn and termo:
        if not (GROQ_API_KEY and SERPER_API_KEY):
            st.error("⚠️ Configure as chaves de API no Dokploy!")
        else:
            periodo_api = ""
            if "24 Horas" in tempo: periodo_api = "qdr:d"
            elif "Semana" in tempo: periodo_api = "qdr:w"
            elif "Mês" in tempo: periodo_api = "qdr:m"
            query_final = termo
            if origem == "LinkedIn (Empresas)": query_final = f'site:linkedin.com/company "{termo}"'
            elif origem == "LinkedIn (Postagens/Feed)": query_final = f'site:linkedin.com/posts "{termo}"'
            elif origem == "Sites de Freelance (Workana/99)": query_final = f'(site:workana.com OR site:99freelas.com.br) "{termo}"'
            elif origem == "Instagram/Negócios (Estratégia Maps)": query_final = f'site:instagram.com "{termo}"'
            st.caption(f"🔎 Buscando: `{query_final}` | Fonte: `{origem}`")
            resultados = search_google_serper(query_final, periodo_api, qtd)
            if not resultados: st.warning("Nenhum sinal encontrado.")
            else:
                bar_text = st.empty()
                prog = st.progress(0)
                processed_results = []
                data_export = [] 
                bar_text.text("🕵️ IA analisando leads em paralelo...")
                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    future_to_item = {executor.submit(process_single_item, item): item for item in resultados}
                    completed = 0
                    for future in concurrent.futures.as_completed(future_to_item):
                        try:
                            data = future.result()
                            processed_results.append(data)
                            analise_data = data['analise']
                            data_export.append({
                                "Titulo": data['titulo'], "Link": data['link'], "Score": analise_data.get('score'),
                                "Autor": analise_data.get('autor'), "Resumo": analise_data.get('resumo_post'),
                                "Produto": analise_data.get('produto_recommended'), "Argumento": analise_data.get('argumento_venda')
                            })
                        except Exception as exc: st.error(f"Erro: {exc}")
                        completed += 1
                        prog.progress(completed / len(resultados))
                bar_text.empty() 
                processed_results.sort(key=lambda x: x['analise'].get('score', 0), reverse=True)
                if data_export:
                    st.download_button(label="📥 BAIXAR RELATÓRIO", data=to_excel(pd.DataFrame(data_export)), file_name="radar.xlsx")
                for p in processed_results:
                    analise = p['analise']
                    score = analise.get('score', 0)
                    css_class = "score-cold"
                    icon = "❄️"
                    if score >= 80: css_class = "score-hot"; icon = "🔥 HOT"
                    elif score >= 50: css_class = "score-warm"; icon = "⚠️ MORNO"
                    card_html = f"""
                    <div class="lead-card {css_class}">
                    <div style="display:flex; justify-content:space-between;">
                        <div><span style="color: #D2FF00; font-weight:bold;">{icon} SCORE: {score}</span></div>
                        <a href="{p['link']}" target="_blank" style="background:#222; color:#fff; padding:5px; border-radius:4px; font-size:12px;">VER POST 🔗</a>
                    </div>
                    <a href="{p['link']}" target="_blank" class="lead-title">{p['titulo']}</a>
                    <div style="color:#666; font-size:11px;">🕒 {p['data_pub']}</div>
                    <div class="recommendation-box">
                        <div style="color: #fff; font-weight:bold;">OFERTAR: {analise.get('produto_recomendado', '').upper()}</div>
                        <div class="rec-text" style="color:#D2FF00;">💡 "{analise.get('argumento_venda', '')}"</div>
                    </div>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)

# ABA 2: MINERADOR SNIPER (B2B + WHATSAPP) - ATUALIZADO
with tab2:
    st.markdown("<h2 style='color:white'>MINERADOR <span style='color:#D2FF00'>LOCAL</span></h2>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: nicho = st.text_input("Nicho:", value="Advocacia Trabalhista")
    with c2: cidade = st.text_input("Cidade Base:", value="São Paulo")
    bairros_txt = st.text_area("Lista de Bairros:", value="Centro, Pinheiros, Vila Madalena", height=100)
    if "leads_zap" not in st.session_state: st.session_state["leads_zap"] = []
    if st.button("🚀 INICIAR VARREDURA", key="btn_zap_mine"):
        lista_bairros = [b.strip() for b in bairros_txt.split(',') if b.strip()]
        for i, bairro in enumerate(lista_bairros):
            queries = [f'site:instagram.com "{nicho}" "{bairro}" "{cidade}" "whatsapp"']
            for q in queries:
                resultados = search_google_serper(q, period="", num_results=20)
                for r in resultados:
                    texto = (r.get('title', '') + " " + r.get('snippet', '')).lower()
                    zap = extrair_whatsapp(texto)
                    if zap and not any(l['Whatsapp'] == zap for l in st.session_state["leads_zap"]):
                        st.session_state["leads_zap"].append({
                            "Empresa": limpar_nome_insta(r.get('title', '')), "Nicho": nicho,
                            "Bairro": bairro, "Whatsapp": zap, "Link": r.get('link')
                        })
        st.success(f"Encontrados: {len(st.session_state['leads_zap'])}")
    if st.session_state["leads_zap"]:
        df = pd.DataFrame(st.session_state["leads_zap"])
        st.dataframe(df, width='stretch')
        if st.button("🔥 DISPARAR CAMPANHA (IP EXTERNO)"):
            sucessos, erros = 0, 0
            for idx, row in df.iterrows():
                try:
                    payload = {"number": row['Whatsapp'], "message": f"Opa {row['Empresa'].split(' ')[0]}, tudo bem? Vi que atendem no {row['Bairro']}..."}
                    # FIX: USANDO IP EXTERNO E PORTA 3000 CONFORME LOGS E DOCKERFILE
                    res = requests.post("http://213.199.56.207:3000/disparar", json=payload, timeout=20)
                    if res.status_code == 200: sucessos += 1
                    else: erros += 1
                except Exception as e: erros += 1
                time.sleep(10)
            st.success(f"Finalizado! ✅ {sucessos} | ❌ {erros}")