from flask import Flask, request, send_file
from flask_cors import CORS
from fpdf import FPDF
from datetime import datetime
import io

app = Flask(__name__)
CORS(app)

@app.route('/gerar_pdf', methods=['POST'])
def gerar_pdf():
    dados = request.json
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(5, 5, 5)
    pdf.rect(0, 0, 210, 297, 'F')
    
    pdf.set_text_color(124, 58, 237)
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 15, "LEANTTRO | PROPOSTA", ln=True, align='C')
    
    pdf.set_draw_color(124, 58, 237)
    pdf.line(10, 30, 200, 30)
    
    pdf.ln(10)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"CLIENTE: {dados.get('cliente', 'N/A')}", ln=True)
    pdf.cell(0, 10, f"CONTATO: {dados.get('contato', 'N/A')}", ln=True)
    pdf.cell(0, 10, f"DATA: {datetime.now().strftime('%d/%m/%Y')}", ln=True)
    
    pdf.ln(5)
    pdf.set_text_color(0, 229, 255)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "DETALHAMENTO DO PROJETO", ln=True)
    
    pdf.set_text_color(200, 200, 200)
    pdf.set_font("Arial", '', 11)
    pdf.multi_cell(0, 7, dados.get('escopo', 'Sem escopo detalhado.'))
    
    pdf.ln(10)
    pdf.set_fill_color(20, 20, 20)
    pdf.set_text_color(0, 229, 255)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 15, f"INVESTIMENTO TOTAL: {dados.get('total', 'R$ 0,00')}", ln=True, align='R', fill=True)
    
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"Proposta_{dados.get('cliente', 'Cliente').replace(' ', '_')}.pdf"
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
