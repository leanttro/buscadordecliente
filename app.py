import streamlit as st
import requests
import os
import json
import time
from groq import Groq

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="ELO HUNTER", layout="wide", page_icon="🦅")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    .stApp { background-color: #050505; color: #E5E7EB; font-family: 'Inter', sans-serif; }
    
    div.stButton > button { 
        background-color: #E31937; color: white; border: none; 
        border-radius: 6px; font-weight: bold; width: 100%; 
    }
    div.stButton > button:hover { background-color: #C2132F; border-color: #C2132F; }
    
    .stTextInput > div > div > input { color: #fff; background-color: #1a1a1a; border-color: #333; }
    
    .lead-card {
        background-color: #151515 !important; padding: 20px; border-radius: 12px;
        border: 1px solid #333; margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    .status-alta { border-left: 6px solid #00cc99; }
    .status-media { border-left: 6px solid #ffcc00; }
    .status-baixa { border-left: 6px solid #ff3333; }

    .lead-title { font-size: 18px; font-weight: bold; color: #fff; margin-bottom: 5px; }
    .lead-link { color: #3b82f6; text-decoration: none; font-size: 14px; }
    .lead-link:hover { text-decoration: underline; color: #60a5fa; }
    
    .tag-produto { 
        background-color: #252525; color: #E31937; padding: 2px 8px; 
        border-radius: 4px; border: 1px solid #E31937; font-size: 11px; 
        text-transform: uppercase; font-weight: bold;
    }
    
    .ai-analysis {
        background-color: #2A1015; padding: 10px; border-radius: 6px; margin-top: 10px;
        border: 1px solid #333; color: #ccc; font-style: italic; font-size: 13px;
    }
    section[data-testid="stSidebar"] { background-color: #111; border-right: 1px solid #333; }
</style>
""", unsafe_allow_html=True)

# --- CARREGAR CHAVES ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "") 
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")

# --- FUNÇÕES ---

def search_google_serper(query, num_results=10):
    """Busca no Google usando a API da Serper.dev (imune a bloqueios de servidor)"""
    url = "https://google.serper.dev/search"
    
    # DORK: site:linkedin.com/posts garante que só pegamos posts do feed
    payload = json.dumps({
        "q": f'site:linkedin.com/posts {query} -intitle:jobs',
        "num": num_results,
        "gl": "br", # Geolocalização Brasil
        "hl": "pt-br" # Idioma Português
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

def analyze_lead_groq(title, snippet, groq_key):
    """Analisa o texto com Llama3 na Groq"""
    if not groq_key: 
        return {"classificacao": "ERRO", "motivo": "Falta chave Groq", "produto": "-"}
    
    client = Groq(api_key=groq_key)
    
    system_prompt = """
    Você é um caçador de leads da Elo Brindes.
    Analise o título e o snippet de um post do LinkedIn.
    
    Critérios:
    1. ALTA: Pede "indicação de brindes", "fornecedor", ou diz "vagas abertas"/"time crescendo" (Sinal de Kit Onboarding).
    2. MEDIA: Eventos corporativos, convenções, expansão.
    3. BAIXA: Procura de emprego, artigos genéricos.

    Responda APENAS JSON:
    {
        "classificacao": "ALTA" | "MEDIA" | "BAIXA",
        "motivo": "Explicação muito breve",
        "produto": "Sugestão (Kit Onboarding, Mochila, etc)"
    }
    """
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"TITULO: {title}\nSNIPPET: {snippet}"}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception:
        return {"classificacao": "BAIXA", "motivo": "Erro AI", "produto": "-"}

# --- INTERFACE ---

with st.sidebar:
    st.markdown(f"<h2 style='color: #E31937; text-align: center;'>🦅 ELO HUNTER</h2>", unsafe_allow_html=True)
    st.divider()
    
    if GROQ_API_KEY: st.success("✅ IA Conectada") 
    else: st.error("⚠️ Falta GROQ KEY")
    
    if SERPER_API_KEY: st.success("✅ Serper Google Ativo")
    else: st.error("⚠️ Falta SERPER KEY")

    st.divider()
    st.markdown("### 💡 Dicas")
    st.code("indicação brindes")
    st.code("estamos contratando")
    st.code("onboarding kit")

st.title("Prospecção LinkedIn (API Profissional)")
st.caption("Google Search via Serper + Groq AI")

c1, c2, c3 = st.columns([6, 1, 1])
with c1:
    termo = st.text_input("Busca:", placeholder="Ex: indicação fornecedor brindes...")
with c2:
    qtd = st.number_input("Qtd", 1, 20, 5)
with c3:
    st.write("##")
    btn = st.button("Buscar")

if btn:
    if not (GROQ_API_KEY and SERPER_API_KEY):
        st.error("Configure as chaves no Dokploy!")
    else:
        with st.spinner("Buscando leads..."):
            resultados = search_google_serper(termo, qtd)
            
            if not resultados:
                st.warning("Nenhum resultado encontrado.")
            else:
                prog = st.progress(0)
                for i, item in enumerate(resultados):
                    titulo = item.get('title', '')
                    link = item.get('link', '')
                    texto = item.get('snippet', '')
                    
                    analise = analyze_lead_groq(titulo, texto, GROQ_API_KEY)
                    
                    cls = analise.get('classificacao', 'BAIXA')
                    css = "status-baixa"
                    ico = "⚪"
                    
                    if cls == "ALTA": 
                        css = "status-alta"
                        ico = "🔥 OPORTUNIDADE"
                    elif cls == "MEDIA":
                        css = "status-media"
                        ico = "⚠️ POSSÍVEL"
                    
                    st.markdown(f"""
                    <div class="lead-card {css}">
                        <div style="display:flex; justify-content:space-between;">
                            <strong style="color:white;">{ico}</strong>
                            <span class="tag-produto">{analise.get('produto', '')}</span>
                        </div>
                        <div style="margin-top:8px;">
                            <a href="{link}" target="_blank" class="lead-title">{titulo}</a>
                        </div>
                        <div style="color:#aaa; font-size:0.9em; margin:5px 0;">{texto}</div>
                        <div class="ai-analysis">🤖 {analise.get('motivo', '')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    time.sleep(0.1) 
                    prog.progress((i+1)/len(resultados))