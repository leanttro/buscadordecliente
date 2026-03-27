from flask import Flask, request, send_file
from flask_cors import CORS
from fpdf import FPDF
from datetime import datetime
import io
import os

app = Flask(__name__)
CORS(app)

LOGO_PATH = "static/logo.png"

def limpar_texto(texto):
    if not texto:
        return "Não informado"
    subs = {
        '•': '-', '–': '-', '—': '-', '“': '"', '”': '"', 
        "‘": "'", "’": "'", 'º': 'o', 'ª': 'a'
    }
    for k, v in subs.items():
        texto = texto.replace(k, v)
    return texto.encode('latin-1', 'ignore').decode('latin-1')

@app.route('/gerar_pdf', methods=['POST'])
def gerar_pdf():
    try:
        dados = request.json
        
        cliente_nome = limpar_texto(dados.get('cliente', ''))
        cliente_contato = limpar_texto(dados.get('contato', ''))
        escopo = limpar_texto(dados.get('escopo', ''))
        total = limpar_texto(dados.get('total', 'R$ 0,00'))
        
        color_bg_main = (10, 10, 15)       
        color_top_bar = (56, 52, 52)         
        color_accent_purple = (124, 58, 237) 
        color_text_header = (255, 255, 255)
        color_cyan_brand = (0, 229, 255)   
        color_text_base = (200, 200, 200) 
        color_border = (40, 40, 50)       

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()
        
        pdf.set_fill_color(*color_bg_main)
        pdf.rect(0, 0, 210, 297, 'F')
        
        pdf.set_fill_color(*color_top_bar)
        pdf.rect(0, 0, 210, 40, 'F') 
        
        pdf.set_draw_color(*color_accent_purple)
        pdf.set_line_width(0.5)
        pdf.line(0, 40, 210, 40)
        
        if os.path.exists(LOGO_PATH):
            pdf.image(LOGO_PATH, x=75, y=8, w=60)
        pdf.ln(35) 

        pdf.set_text_color(*color_text_header)
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "PROPOSTA COMERCIAL", ln=True, align='C')
        pdf.ln(8) 

        margem = 20
        pdf.set_left_margin(margem)
        pdf.set_right_margin(margem)
        
        pdf.set_text_color(*color_text_base)
        pdf.set_font("Arial", '', 9)
        data_atual = datetime.now().strftime('%d/%m/%Y')
        pdf.cell(0, 5, f"Data de Emissão: {data_atual}", ln=True, align='R')
        pdf.ln(8)

        pdf.set_fill_color(*color_bg_main)
        pdf.set_text_color(*color_cyan_brand)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 8, "DADOS DO CLIENTE", ln=True)
        
        pdf.set_draw_color(*color_border)
        pdf.set_line_width(0.3)
        pdf.line(margem, pdf.get_y(), 210-margem, pdf.get_y()) 
        pdf.ln(4)
        
        pdf.set_text_color(*color_text_base)
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 6, f"Empresa / Responsável: {cliente_nome}", ln=True)
        pdf.cell(0, 6, f"Contato: {cliente_contato}", ln=True)
        pdf.ln(10)

        pdf.set_text_color(*color_cyan_brand)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 8, "DETALHAMENTO DO PROJETO", ln=True)
        pdf.line(margem, pdf.get_y(), 210-margem, pdf.get_y())
        pdf.ln(6)
        
        pdf.set_text_color(*color_text_header)
        pdf.set_font("Arial", '', 10)
        
        linhas = escopo.split('\n')
        for linha in linhas:
            if linha.strip():
                pdf.multi_cell(0, 6, linha.strip(), align='L')
            else:
                pdf.ln(3) 
        
        pdf.ln(15)

        pdf.set_left_margin(0)
        pdf.set_right_margin(0)
        
        y_box = pdf.get_y()
        largura_box = 100
        x_box = (210 - largura_box) / 2
        
        pdf.set_fill_color(18, 18, 24) 
        pdf.set_draw_color(*color_accent_purple)
        pdf.set_line_width(0.5)
        pdf.rect(x_box, y_box, largura_box, 28, 'DF')
        
        pdf.set_y(y_box + 5)
        pdf.set_text_color(*color_cyan_brand)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 6, "INVESTIMENTO TOTAL", ln=True, align='C')
        
        pdf.set_text_color(*color_text_header)
        pdf.set_font("Arial", 'B', 18)
        pdf.cell(0, 10, total, ln=True, align='C')
        
        pdf_output = pdf.output(dest='S')
        
        if isinstance(pdf_output, str):
            pdf_bytes = pdf_output.encode('latin-1')
        else:
            pdf_bytes = pdf_output

        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"Proposta_{cliente_nome.replace(' ', '_')}.pdf"
        )
    except Exception as e:
        print(f"Erro crítico no PDF: {e}")
        return {"erro": str(e)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
