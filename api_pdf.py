from flask import Flask, request, send_file
from flask_cors import CORS
from fpdf import FPDF
from datetime import datetime
import io
import os

app = Flask(__name__)
CORS(app)

LOGO_PATH = "static/logo.png"

@app.route('/gerar_pdf', methods=['POST'])
def gerar_pdf():
    try:
        dados = request.json
        
        color_bg_main = (10, 10, 15)       
        color_header_bg = (124, 58, 237)   
        color_text_header = (255, 255, 255)
        color_cyan_brand = (0, 229, 255)   
        color_text_base = (220, 220, 220) 
        color_border = (60, 60, 70)       

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        pdf.set_fill_color(*color_bg_main)
        pdf.rect(0, 0, 210, 297, 'F')
        
        pdf.set_fill_color(*color_header_bg)
        pdf.rect(0, 0, 210, 45, 'F') 
        
        if os.path.exists(LOGO_PATH):
            pdf.image(LOGO_PATH, x=75, y=10, w=60)
            pdf.ln(25) 
        else:
            print(f"Aviso: Logo não encontrado em {LOGO_PATH}")
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
        pdf.cell(0, 8, f"    Cliente: {dados.get('cliente', 'Não Informado')}", ln=True)
        pdf.cell(0, 8, f"    Contato: {dados.get('contato', 'Não Informado')}", ln=True)
        pdf.ln(12)

        pdf.set_text_color(*color_cyan_brand)
        pdf.set_font("Arial", 'B', 13)
        pdf.cell(0, 10, "  DETALHAMENTO DO PROJETO", ln=True)
        
        pdf.set_draw_color(*color_border)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        
        pdf.set_text_color(255, 255, 255) 
        pdf.set_font("Arial", '', 11)
        pdf.ln(5)
        
        current_y = pdf.get_y()
        escopo_texto = dados.get('escopo', 'Nenhum detalhamento fornecido.')
        
        pdf.set_fill_color(20, 20, 25)
        pdf.set_x(20) 
        pdf.multi_cell(170, 7, escopo_texto, align='L')
        pdf.ln(15)

        pdf.set_left_margin(0) 
        
        pdf.set_fill_color(*color_bg_main)
        total_y = pdf.get_y()
        pdf.set_draw_color(*color_header_bg)
        pdf.set_line_width(0.8)
        pdf.rect(60, total_y, 90, 25, 'D')
        
        pdf.set_y(total_y + 5)
        pdf.set_text_color(*color_cyan_brand)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 7, "INVESTIMENTO TOTAL", ln=True, align='C')
        
        pdf.set_text_color(*color_text_header)
        pdf.set_font("Arial", 'B', 22)
        pdf.cell(0, 12, dados.get('total', 'R$ 0,00'), ln=True, align='C')
        pdf.ln(25)
        
        pdf.set_left_margin(15)
        current_y = pdf.get_y()
        if current_y > 230:
            pdf.add_page()
            current_y = 20
            
        pdf.set_draw_color(*color_header_bg)
        pdf.set_line_width(0.5)
        line_x = (210 - 100) / 2
        pdf.line(line_x, current_y, line_x + 100, current_y)
        
        pdf.set_text_color(*color_text_base)
        pdf.set_font("Arial", '', 11)
        pdf.set_y(current_y + 3)
        pdf.cell(0, 7, "ACEITE DO CLIENTE", ln=True, align='C')
        pdf.cell(0, 7, dados.get('cliente', 'Cliente'), ln=True, align='C')
        
        pdf_output = pdf.output(dest='S')
        
        if isinstance(pdf_output, str):
            pdf_bytes = pdf_output.encode('latin-1')
        else:
            pdf_bytes = pdf_output

        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"Proposta_{dados.get('cliente', 'Cliente').replace(' ', '_')}.pdf"
        )
    except Exception as e:
        print(f"Erro crítico no PDF: {e}")
        return {"erro": str(e)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
