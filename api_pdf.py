from flask import Flask, request, send_file
from flask_cors import CORS
from fpdf import FPDF
from datetime import datetime
import io
import requests

app = Flask(__name__)
CORS(app)

LOGO_URL = "https://res.cloudinary.com/dzcaxmbjn/image/upload/v1773591878/presentes_180_x_50_px_720_x_200_px_1440_x_264_px_1_azuhgq.png"

@app.route('/gerar_pdf', methods=['POST'])
def gerar_pdf():
    try:
        dados = request.json
        
        # Cores da marca
        bg_dark = (5, 5, 5)
        bg_section = (20, 20, 20)
        purple = (124, 58, 237)
        cyan = (0, 229, 255)
        gray_text = (200, 200, 200)
        white = (255, 255, 255)

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Fundo Total Escuro
        pdf.set_fill_color(*bg_dark)
        pdf.rect(0, 0, 210, 297, 'F')
        
        # --- HEADER ---
        try:
            # Baixa o logo via requests e insere via stream
            img_response = requests.get(LOGO_URL)
            if img_response.status_code == 200:
                logo_bytes = io.BytesIO(img_response.content)
                # Centraliza o logo (210mm - 80mm largura / 2 = 65mm x)
                pdf.image(logo_bytes, x=65, y=10, w=80)
                pdf.ln(25)
            else:
                pdf.ln(10) # Falha ao baixar, pula espaço
        except Exception as e:
            print(f"Erro ao carregar imagem: {e}")
            pdf.ln(10) # Erro genérico, pula espaço

        # Título Principal (Roxo)
        pdf.set_text_color(*purple)
        pdf.set_font("Arial", 'B', 24)
        pdf.cell(0, 15, "PROPOSTA COMERCIAL", ln=True, align='C')
        pdf.ln(10)
        
        # --- SEÇÃO 1: INFORMAÇÕES DO CLIENTE ---
        pdf.set_fill_color(*bg_section)
        pdf.set_text_color(*cyan)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "  INFORMAÇÕES DO CLIENTE", ln=True, fill=True)
        
        pdf.set_text_color(*gray_text)
        pdf.set_font("Arial", '', 11)
        pdf.ln(2)
        pdf.cell(0, 8, f"  Cliente: {dados.get('cliente', 'N/A')}", ln=True)
        pdf.cell(0, 8, f"  Contato: {dados.get('contato', 'N/A')}", ln=True)
        pdf.cell(0, 8, f"  Data de Emissão: {datetime.now().strftime('%d/%m/%Y')}", ln=True)
        pdf.ln(10)
        
        # --- SEÇÃO 2: DETALHAMENTO DO PROJETO ---
        pdf.set_fill_color(*bg_section)
        pdf.set_text_color(*cyan)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "  DETALHAMENTO DO PROJETO", ln=True, fill=True)
        
        pdf.set_text_color(*white)
        pdf.set_font("Arial", '', 11)
        pdf.ln(2)
        # multi_cell para texto longo com quebra de linha automatica
        pdf.multi_cell(0, 7, dados.get('escopo', 'Sem escopo detalhado fornecido.'))
        pdf.ln(15)
        
        # --- SEÇÃO 3: INVESTIMENTO TOTAL ---
        pdf.set_fill_color(*bg_section)
        pdf.set_text_color(*cyan)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 12, "  INVESTIMENTO TOTAL", ln=True, fill=True)
        
        pdf.set_text_color(*purple)
        pdf.set_font("Arial", 'B', 20)
        pdf.set_y(pdf.get_y() - 12) # Alinha o valor na mesma linha do título invertendo a ordem
        pdf.cell(0, 12, f"{dados.get('total', 'R$ 0,00')}  ", ln=True, align='R')
        pdf.ln(25)
        
        # --- SEÇÃO 4: ASSINATURA ---
        current_y = pdf.get_y()
        # Garante que a assinatura não quebre de página
        if current_y > 240:
            pdf.add_page()
            current_y = 20
            
        pdf.set_draw_color(*purple)
        pdf.set_line_width(0.5)
        # Centraliza a linha de assinatura
        line_x = (210 - 100) / 2
        pdf.line(line_x, current_y, line_x + 100, current_y)
        
        pdf.set_text_color(*gray_text)
        pdf.set_font("Arial", '', 11)
        pdf.set_y(current_y + 3)
        pdf.cell(0, 7, "ACEITE DO CLIENTE", ln=True, align='C')
        pdf.cell(0, 7, dados.get('cliente', 'N/A'), ln=True, align='C')
        
        # Gera o PDF em memória
        pdf_output = pdf.output(dest='S')
        
        # FPDF pode retornar string ou bytes dependendo da versão/config. Garante latin-1.
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
        print(f"Erro crítico: {e}")
        return {"erro": str(e)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
