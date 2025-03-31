from flask import Flask, render_template, request, send_file
import pdfkit
import locale
import os
from datetime import datetime
import sys
import platform
import io

app = Flask(__name__)

# Configuração do PDFKit
def get_pdfkit_config():
    try:
        if platform.system() == "Windows":
            WKHTMLTOPDF_PATH = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
            if os.path.exists(WKHTMLTOPDF_PATH):
                return pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)
        else:
            return pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf')
        return None
    except Exception as e:
        print(f"Erro na configuração do PDFKit: {str(e)}")
        return None

PDFKIT_CONFIG = get_pdfkit_config()

# Configuração de locale
def configure_locale():
    locales = ['pt_BR.UTF-8', 'Portuguese_Brazil.1252', 'pt_BR', 'Portuguese', '']
    for loc in locales:
        try:
            locale.setlocale(locale.LC_ALL, loc)
            break
        except (locale.Error, NameError):
            continue

configure_locale()

def format_currency(value):
    """Formata valores monetários com fallback robusto"""
    try:
        return locale.currency(value, grouping=True, symbol=True)
    except:
        try:
            return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except:
            return f"R$ {value:.2f}"

def parse_currency(value):
    """Converte string monetária para float"""
    if not value or value == 'R$ 0,00':
        return 0.0
    clean_value = value.replace("R$", "").replace(".", "").replace(",", ".").strip()
    return float(clean_value) if clean_value else 0.0

@app.route('/', methods=['GET', 'POST'])
def index():
    valores = {
        'total_iara': 'R$ 0,00', 
        'luz_iara': 'R$ 0,00', 
        'agua_iara': 'R$ 0,00',
        'luz_rodrigo': 'R$ 0,00', 
        'agua_rodrigo': 'R$ 0,00', 
        'total_rodrigo': 'R$ 0,00',
        'error': None
    }

    if request.method == 'POST':
        try:
            valor_luz = parse_currency(request.form.get('luz', '0'))
            valor_agua = parse_currency(request.form.get('agua', '0'))

            # Cálculos
            luz_iara = valor_luz / 3
            agua_iara = valor_agua / 2
            luz_rodrigo = valor_luz * 2 / 3
            agua_rodrigo = valor_agua / 2
            
            # Totais
            total_iara = luz_iara + agua_iara
            total_rodrigo = luz_rodrigo + agua_rodrigo

            # Formatação
            valores.update({
                'luz_iara': format_currency(luz_iara),
                'agua_iara': format_currency(agua_iara),
                'total_iara': format_currency(total_iara),
                'luz_rodrigo': format_currency(luz_rodrigo),
                'agua_rodrigo': format_currency(agua_rodrigo),
                'total_rodrigo': format_currency(total_rodrigo)
            })
                
        except Exception as e:
            print(f"Erro no processamento: {str(e)}")
            valores['error'] = "Erro ao processar valores. Verifique os dados."

    return render_template('index.html', **valores)

@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    if not PDFKIT_CONFIG:
        return "Serviço de PDF não disponível.", 503

    try:
        # Get current datetime for the report
        now = datetime.now()
        
        # Prepare data for template
        dados = {
            'luz_iara': request.form.get('luz_iara', 'R$ 0,00'),
            'agua_iara': request.form.get('agua_iara', 'R$ 0,00'),
            'total_iara': request.form.get('total_iara', 'R$ 0,00'),
            'luz_rodrigo': request.form.get('luz_rodrigo', 'R$ 0,00'),
            'agua_rodrigo': request.form.get('agua_rodrigo', 'R$ 0,00'),
            'total_rodrigo': request.form.get('total_rodrigo', 'R$ 0,00'),
            'now': now  # Pass the datetime object directly
        }

        pdf_options = {
            'page-size': 'A4',
            'margin-top': '15mm',
            'margin-right': '15mm',
            'margin-bottom': '15mm',
            'margin-left': '15mm',
            'encoding': 'UTF-8',
            'quiet': '',
            'enable-local-file-access': None
        }

        rendered = render_template("iara_pdf.html", **dados)
        pdf = pdfkit.from_string(
            rendered,
            False,
            configuration=PDFKIT_CONFIG,
            options=pdf_options
        )
        
        return send_file(
            io.BytesIO(pdf),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'Contas_{now.strftime("%Y%m%d_%H%M")}.pdf'
        )

    except Exception as e:
        print(f"Erro ao gerar PDF: {str(e)}")
        return "Erro ao gerar PDF. Tente novamente.", 500

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)), debug=False)
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
        sys.exit(0)