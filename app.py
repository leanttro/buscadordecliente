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
    
    /* Forçar links a não terem sublinhado padrão */
    a { text-decoration: none !important; }
</style>
""", unsafe_allow_html=True)

# --- CARREGAR CHAVES ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "") 
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")

# --- FUNÇÕES ---

def search_google_serper(query, num_results=10):
    """Busca no Google/Serper"""
    url = "https://google.serper.dev/search"
    
    payload = json.dumps({
        "q": query,
        "num": num_results,
        "gl": "br", 
        "hl": "pt-br"
    })
    
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
    """Analisa o lead com a IA"""
    if not groq_key: 
        return {"score": 0, "produto_recomendado": "ERRO CHAVE", "argumento_venda": "Sem chave Groq"}
    
    client = Groq(api_key=groq_key)
    
    # MENU DE SERVIÇOS LEANTTRO
    LEANTTRO_PORTFOLIO = """
    1. WEB PRESENCE: Sites Institucionais, Landing Pages (Advogados, Médicos, Prestadores).
    2. E-COMMERCE: Lojas Virtuais (Varejo, Auto-peças, Roupas).
    3. EVENTOS: Sites para Casamentos/Festas com RSVP e Lista de Presentes (Buffets, Espaços, Assessoria).
    4. AUTOMAÇÃO/DADOS: Dashboards, Integrações n8n, Chatbots (Empresas com processos manuais, Logística, Imobiliárias).
    """

    system_prompt = f"""
    ATUE COMO: Consultor Sênior da 'Leanttro Digital'.
    OBJETIVO: Analisar resultados de busca (Google/Linkedin/Instagram) para vender tecnologia.
    
    PORTFÓLIO:
    {LEANTTRO_PORTFOLIO}
    
    REGRAS DE ANÁLISE:
    - Se a fonte for INSTAGRAM/LINKEDIN: O cliente PROVAVELMENTE não tem site ou é fraco. 
      -> Argumento: "Profissionalize sua marca, saia do amadorismo das redes sociais."
    
    - Buffets/Festas -> Foco: SITE DE FESTAS (RSVP/Presentes).
    - Varejo/Loja Física -> Foco: LOJA VIRTUAL (Venda dormindo).
    - Serviços (Adv/Med) -> Foco: SITE INSTITUCIONAL (Autoridade).
    - Empresas Operacionais -> Foco: AUTOMAÇÃO/DADOS.
    
    SAÍDA JSON OBRIGATÓRIA:
    {{
        "score": (0-100),
        "nicho_detectado": "Ex: Advocacia Trabalhista",
        "dor_principal": "Ex: Só usa Instagram, sem site profissional",
        "produto_recomendado": "Ex: Site Institucional",
        "argumento_venda": "Pitch curto de 1 frase focado na dor."
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
        return {"score": 0, "produto_recomendado": "Erro AI", "argumento_venda": str(e)}

# --- INTERFACE ---

with st.sidebar:
    st.markdown(f"<h1 style='color: #fff; text-align: center; font-style: italic;'>LEAN<span style='color:#D2FF00'>TTRO</span>.<br><span style='font-size:14px; color:#666'>BUSCADOR DE CLIENTES</span></h1>", unsafe_allow_html=True)
    st.divider()
    
    if GROQ_API_KEY: st.success("🟢 IA Conectada") 
    else: st.error("🔴 Falta GROQ KEY")
    
    if SERPER_API_KEY: st.success("🟢 Google Search Ativo")
    else: st.error("🔴 Falta SERPER KEY")

    st.divider()
    st.markdown("### 🎯 Dicas de Ouro")
    st.info("Buscar no LinkedIn/Instagram traz empresas que muitas vezes NÃO TEM SITE. É o melhor lead!")

st.markdown("<h2 style='color:white'>QUEM VAMOS <span style='color:#D2FF00'>DIGITALIZAR</span> HOJE?</h2>", unsafe_allow_html=True)

# Layout de Busca
c1, c2, c3 = st.columns([2, 4, 1])

with c1:
    origem = st.selectbox("Onde buscar?", ["Google (Web Geral)", "LinkedIn (Empresas)", "Instagram (Perfis)"])
with c2:
    termo = st.text_input("Nicho / Termo:", placeholder="Ex: Logística, Buffet Infantil, Dentista...")
with c3:
    qtd = st.number_input("Qtd", 1, 50, 5)

st.write("##")
btn = st.button("RASTREAR OPORTUNIDADES")

if btn and termo:
    if not (GROQ_API_KEY and SERPER_API_KEY):
        st.error("⚠️ Configure as chaves de API no Dokploy (Environment)!")
    else:
        # LÓGICA DE FILTRO DE REDES SOCIAIS
        query_final = termo
        if origem == "LinkedIn (Empresas)":
            query_final = f'site:linkedin.com/company "{termo}"'
        elif origem == "Instagram (Perfis)":
            query_final = f'site:instagram.com "{termo}"'

        st.caption(f"🔎 Buscando por: `{query_final}`")

        with st.spinner("🕵️ Minando dados..."):
            resultados = search_google_serper(query_final, qtd)
            
            if not resultados:
                st.warning("Nenhum sinal encontrado. Tente termos mais amplos.")
            else:
                prog = st.progress(0)
                for i, item in enumerate(resultados):
                    titulo = item.get('title', '')
                    link = item.get('link', '')
                    snippet = item.get('snippet', '')
                    
                    # Analisa com a nova inteligência Leanttro
                    analise = analyze_lead_groq(titulo, snippet, link, GROQ_API_KEY)
                    
                    score = analise.get('score', 0)
                    
                    # Define estilo baseado no Score
                    css_class = "score-cold"
                    icon = "❄️"
                    if score >= 80:
                        css_class = "score-hot"
                        icon = "🔥 HOT"
                    elif score >= 50:
                        css_class = "score-warm"
                        icon = "⚠️ MORNO"
                    
                    # --- CORREÇÃO DEFINITIVA DO ERRO VISUAL ---
                    # Usamos textwrap.dedent para garantir que o HTML não tenha espaços no início das linhas
                    card_html = textwrap.dedent(f"""
                        <div class="lead-card {css_class}">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <div>
                                    <span style="color: #D2FF00; font-weight:bold; font-family:monospace;">{icon} SCORE: {score}/100</span>
                                    <span class="tag-nicho">{analise.get('nicho_detectado', 'Geral')}</span>
                                </div>
                                <a href="{link}" target="_blank" style="background:#222; color:#fff; padding:5px 10px; text-decoration:none; border-radius:4px; font-size:12px;">VISITAR {origem.split()[0].upper()} 🔗</a>
                            </div>
                            
                            <div style="margin-top:10px;">
                                <a href="{link}" target="_blank" class="lead-title">{titulo}</a>
                            </div>
                            <div style="color:#888; font-size:12px; margin:5px 0;">{snippet[:200]}...</div>
                            
                            <div class="recommendation-box">
                                <div class="rec-title">// DIAGNÓSTICO LEANTTRO:</div>
                                <div style="color: #fff; font-weight:bold;">VENDER: {analise.get('produto_recomendado', 'N/A').upper()}</div>
                                <div class="rec-text"><span style="color:#666">DOR:</span> {analise.get('dor_principal', '')}</div>
                                <div class="rec-text" style="color:#D2FF00; margin-top:5px;">💡 " {analise.get('argumento_venda', '')} "</div>
                            </div>
                        </div>
                    """)
                    
                    st.markdown(card_html, unsafe_allow_html=True)
                    
                    time.sleep(0.1) 
                    prog.progress((i+1)/len(resultados))