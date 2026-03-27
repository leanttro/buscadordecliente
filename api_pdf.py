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
        
        cliente_raw = dados.get('cliente', 'Não Informado')
        contato_raw = dados.get('contato', 'Não Informado')
        escopo_raw = dados.get('escopo', 'Nenhum detalhamento fornecido.')
        total_raw = dados.get('total', 'R$ 0,00')

        cliente_nome = limpar_texto(cliente_raw)
        cliente_contato = limpar_texto(contato_raw)
        escopo_texto = limpar_texto(escopo_raw)
        total = limpar_texto(total_raw)
        
        color_bg_main = (10, 10, 15)       
        color_top_bar = (56, 52, 52)         
        color_accent_purple = (124, 58, 237) 
        color_text_header = (255, 255, 255)
        color_cyan_brand = (0, 229, 255)   
        color_text_base = (220, 220, 220) 
        color_border = (60, 60, 70)       

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        pdf.set_fill_color(*color_bg_main)
        pdf.rect(0, 0, 210, 297, 'F')
        
        pdf.set_fill_color(*color_top_bar)
        pdf.rect(0, 0, 210, 45, 'F') 
        
        if os.path.exists(LOGO_PATH):
            pdf.image(LOGO_PATH, x=75, y=10, w=60)
            pdf.ln(25) 
        else:
            pdf.ln(15) 

        pdf.set_text_color(*color_text_header)
        pdf.set_font("Arial", 'B', 18)
        pdf.cell(0, 12, "PROPOSTA COMERCIAL PROFISSIONAL", ln=True, align='C')
        pdf.ln(8) 

        pdf.set_left_margin(15)
        pdf.set_right_margin(15)
        
        pdf.set_text_color(*color_text_base)
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 5, f"Data: {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='R')
        pdf.ln(5)

        pdf.set_fill_color(*color_bg_main)
        pdf.set_text_color(*color_cyan_brand)
        pdf.set_font("Arial", 'B', 13)
        pdf.cell(0, 10, "  DADOS DO CLIENTE", ln=True)
        
        pdf.set_draw_color(*color_cyan_brand)
        pdf.set_line_width(0.3)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y()) 
        
        pdf.set_text_color(*color_text_base)
        pdf.set_font("Arial", '', 11)
        pdf.ln(5)
        
        current_y = pdf.get_y()
        pdf.set_fill_color(20, 20, 25) 
        pdf.rect(15, current_y, 180, 22, 'F')
        
        pdf.set_y(current_y + 3)
        pdf.cell(0, 8, f"    Cliente: {cliente_nome}", ln=True)
        pdf.cell(0, 8, f"    Contato: {cliente_contato}", ln=True)
        pdf.ln(12)

        pdf.set_text_color(*color_cyan_brand)
        pdf.set_font("Arial", 'B', 13)
        pdf.cell(0, 10, "  DETALHAMENTO DO PROJETO", ln=True)
        
        pdf.set_draw_color(*color_border)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        
        pdf.set_text_color(255, 255, 255) 
        pdf.set_font("Arial", '', 11)
        pdf.ln(5)
        
        pdf.set_fill_color(20, 20, 25)
        pdf.set_x(15) 
        
        escopo_formatado = f"\n  {escopo_texto.replace(chr(10), chr(10) + '  ')}\n"
        pdf.multi_cell(180, 7, escopo_formatado, align='L', fill=True)
        pdf.ln(15)

        pdf.set_left_margin(0) 
        pdf.set_right_margin(0)
        
        pdf.set_fill_color(*color_bg_main)
        total_y = pdf.get_y()
        pdf.set_draw_color(*color_accent_purple)
        pdf.set_line_width(0.8)
        
        largura_box = 90
        x_box = (210 - largura_box) / 2
        pdf.rect(x_box, total_y, largura_box, 25, 'D')
        
        pdf.set_y(total_y + 5)
        pdf.set_text_color(*color_cyan_brand)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 7, "INVESTIMENTO TOTAL", ln=True, align='C')
        
        pdf.set_text_color(*color_text_header)
        pdf.set_font("Arial", 'B', 22)
        pdf.cell(0, 12, total, ln=True, align='C')
        
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
