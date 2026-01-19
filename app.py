import streamlit as st
import requests
import os
import json
import time
import textwrap
from groq import Groq

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="LEANTTRO HUNTER", layout="wide", page_icon="🚀")

# --- ESTILO VISUAL (IDENTIDADE LEANTTRO NEON) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600;700&family=Chakra+Petch:wght@400;700&display=swap');
    
    .stApp { background-color: #050505; color: #E5E7EB; font-family: 'Kanit', sans-serif; }
    
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

    /* Card do Lead */
    .lead-card {
        background-color: #0a0a0a !important; padding: 25px; border-radius: 8px;
        border: 1px solid #222; margin-bottom: 20px;
        position: relative; overflow: hidden;
    }
    .lead-card:hover { border-color: #D2FF00; }
    
    /* Scores */
    .score-hot { border-left: 4px solid #D2FF00; } /* Quente */
    .score-warm { border-left: 4px solid #fff; }    /* Morno */
    .score-cold { border-left: 4px solid #333; }    /* Frio */

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
    
    h1, h2, h3 { font-family: 'Chakra Petch', sans-serif; font-style: italic; }
    a { text-decoration: none !important; }
</style>
""", unsafe_allow_html=True)

# --- CARREGAR CHAVES ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "") 
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")

# --- FUNÇÕES ---

def search_google_serper(query, period, num_results=10):
    """
    Busca no Google/Serper com filtro de tempo (tbs).
    period: 'qdr:d' (24h), 'qdr:w' (semana), 'qdr:m' (mês) ou '' (qualquer data)
    """
    url = "https://google.serper.dev/search"
    
    payload_dict = {
        "q": query,
        "num": num_results,
        "gl": "br", 
        "hl": "pt-br"
    }
    
    # Se tiver filtro de tempo, adiciona ao payload
    if period:
        payload_dict["tbs"] = period

    payload = json.dumps(payload_dict)
    
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code == 200:
            return response.json().get("organic", [])
        else:
            st.error(f"Erro Serper: {response.text}")
            return []
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return []

def analyze_lead_groq(title, snippet, link, groq_key):
    """Analisa o post e tenta extrair o autor"""
    if not groq_key: 
        return {"score": 0, "autor": "Desc.", "produto_recomendado": "ERRO CHAVE", "argumento_venda": "Sem chave Groq"}
    
    client = Groq(api_key=groq_key)
    
    # MENU DE SERVIÇOS LEANTTRO
    LEANTTRO_PORTFOLIO = """
    1. OUTSOURCING/FREELANCE: Desenvolvimento Python, Automação, Dashboards.
    2. SITES/LANDING PAGES: Criação rápida para eventos ou lançamentos.
    3. E-COMMERCE: Lojas virtuais.
    4. AUTOMAÇÃO: Chatbots e IA.
    """

    system_prompt = f"""
    ATUE COMO: Head de Vendas da 'Leanttro Digital'.
    
    CONTEXTO: O usuário buscou por POSTAGENS no LinkedIn/Google.
    
    TAREFAS:
    1. Tente identificar o NOME DA PESSOA que fez o post (Geralmente está no título antes de "no LinkedIn" ou "on LinkedIn").
    2. Analise se é uma oportunidade de venda ou vaga de emprego.
    3. Defina um SCORE (0-100) de quão quente é esse lead para oferecer serviços de TI/Dev.
    
    SAÍDA JSON OBRIGATÓRIA:
    {{
        "autor": "Nome da Pessoa (ou Empresa)",
        "score": (0-100),
        "resumo_post": "O que a pessoa está procurando? (max 10 palavras)",
        "produto_recomendado": "Qual serviço Leanttro se encaixa?",
        "argumento_venda": "Abordagem para chamar a atenção dessa pessoa."
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
        return {"score": 0, "autor": "Erro", "produto_recomendado": "Erro AI", "argumento_venda": str(e)}

# --- INTERFACE ---

with st.sidebar:
    st.markdown(f"<h1 style='color: #fff; text-align: center; font-style: italic;'>LEAN<span style='color:#D2FF00'>TTRO</span>.<br><span style='font-size:14px; color:#666'>HUNTER V2</span></h1>", unsafe_allow_html=True)
    st.divider()
    
    if GROQ_API_KEY: st.success("🟢 IA Conectada") 
    else: st.error("🔴 Falta GROQ KEY")
    
    if SERPER_API_KEY: st.success("🟢 Google Search Ativo")
    else: st.error("🔴 Falta SERPER KEY")

    st.divider()
    st.markdown("### 🎯 Modo Postagem")
    st.info("A opção 'LinkedIn (Postagens)' busca dentro do feed. Use termos como 'Contratando', 'Preciso de dev', 'Indicação'.")

st.markdown("<h2 style='color:white'>O QUE VAMOS <span style='color:#D2FF00'>CAÇAR</span> HOJE?</h2>", unsafe_allow_html=True)

# Layout de Busca
c1, c2, c3, c4 = st.columns([3, 3, 2, 1])

with c1:
    origem = st.selectbox("Onde buscar?", [
        "LinkedIn (Postagens/Feed)", 
        "LinkedIn (Empresas)", 
        "Google (Geral)",
        "Instagram (Perfis)"
    ])
with c2:
    termo = st.text_input("Termo de Busca:", placeholder="Ex: contratando dev python, preciso de site...")
with c3:
    tempo = st.selectbox("Período (Recência):", [
        "Últimas 24 Horas (qdr:d)",
        "Última Semana (qdr:w)",
        "Último Mês (qdr:m)",
        "Qualquer data"
    ])
with c4:
    qtd = st.number_input("Qtd", 1, 50, 5)

st.write("##")
btn = st.button("RASTREAR OPORTUNIDADES")

if btn and termo:
    if not (GROQ_API_KEY and SERPER_API_KEY):
        st.error("⚠️ Configure as chaves de API no Dokploy (Environment)!")
    else:
        # TRATAMENTO DO FILTRO DE TEMPO
        periodo_api = ""
        if "24 Horas" in tempo: periodo_api = "qdr:d"
        elif "Semana" in tempo: periodo_api = "qdr:w"
        elif "Mês" in tempo: periodo_api = "qdr:m"

        # LÓGICA DE FILTRO DE REDES SOCIAIS
        query_final = termo
        
        if origem == "LinkedIn (Empresas)":
            query_final = f'site:linkedin.com/company "{termo}"'
        elif origem == "LinkedIn (Postagens/Feed)":
            # Busca focada em POSTS
            query_final = f'site:linkedin.com/postsOrFeed "{termo}"' 
            # Dica: site:linkedin.com/posts costuma pegar posts individuais
            # Às vezes o Google indexa melhor como site:linkedin.com/feed ou apenas a palavra chave + site:linkedin.com
            query_final = f'site:linkedin.com/posts "{termo}"'
            
        elif origem == "Instagram (Perfis)":
            query_final = f'site:instagram.com "{termo}"'

        st.caption(f"🔎 Buscando por: `{query_final}` | Filtro: `{tempo}`")

        with st.spinner("🕵️ Minando dados recentes..."):
            resultados = search_google_serper(query_final, periodo_api, qtd)
            
            if not resultados:
                st.warning("Nenhum sinal encontrado. Tente aumentar o período de tempo.")
            else:
                prog = st.progress(0)
                for i, item in enumerate(resultados):
                    titulo = item.get('title', '')
                    link = item.get('link', '')
                    snippet = item.get('snippet', '')
                    data_pub = item.get('date', 'Data não ident.') # Serper as vezes retorna a data
                    
                    # Analisa com a nova inteligência Leanttro
                    analise = analyze_lead_groq(titulo, snippet, link, GROQ_API_KEY)
                    
                    score = analise.get('score', 0)
                    autor = analise.get('autor', 'Desconhecido')
                    
                    # Define estilo baseado no Score
                    css_class = "score-cold"
                    icon = "❄️"
                    if score >= 80:
                        css_class = "score-hot"
                        icon = "🔥 HOT"
                    elif score >= 50:
                        css_class = "score-warm"
                        icon = "⚠️ MORNO"
                    
                    # CARD BLINDADO COM TEXTWRAP
                    card_html = textwrap.dedent(f"""
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
                    """)
                    
                    st.markdown(card_html, unsafe_allow_html=True)
                    
                    time.sleep(0.1) 
                    prog.progress((i+1)/len(resultados))