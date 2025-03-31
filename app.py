from flask import Flask, render_template, request, make_response
import pdfkit
import locale
import os
from datetime import datetime
import sys
import platform

app = Flask(__name__)

# Configuração do PDFKit unificada
PDFKIT_CONFIG = None

try:
    if platform.system() == "Windows":
        WKHTMLTOPDF_PATH = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
        if os.path.exists(WKHTMLTOPDF_PATH):
            PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)
    else:
        PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf')
    
    # Teste básico de configuração
    if PDFKIT_CONFIG:
        pdfkit.from_string('<html><body><h1>Test</h1></body></html>', False, configuration=PDFKIT_CONFIG)
    else:
        print("Aviso: Configuração do PDFKit não disponível. Funcionalidade de PDF estará limitada.")
except Exception as e:
    print(f"Erro na configuração do PDFKit: {str(e)}")

# Configuração de locale melhorada
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

@app.route('/', methods=['GET', 'POST'])
def index():
    valores = {
        'total_iara': '', 'luz_iara': '', 'agua_iara': '',
        'luz_rodrigo': '', 'agua_rodrigo': '', 'total_rodrigo': '',
        'error': None
    }

    if request.method == 'POST':
        try:
            def parse_currency(value):
                """Converte string monetária para float"""
                clean_value = value.replace("R$", "").replace(".", "").replace(",", ".").strip()
                return float(clean_value) if clean_value else 0.0
            
            valor_luz = parse_currency(request.form.get('luz', '0'))
            valor_agua = parse_currency(request.form.get('agua', '0'))

            # Cálculos
            valores.update({
                'luz_iara': valor_luz / 3,
                'agua_iara': valor_agua / 2,
                'luz_rodrigo': valor_luz * 2 / 3,
                'agua_rodrigo': valor_agua / 2
            })
            
            # Totais
            valores['total_iara'] = valores['luz_iara'] + valores['agua_iara']
            valores['total_rodrigo'] = valores['luz_rodrigo'] + valores['agua_rodrigo']

            # Formatação
            for key in valores:
                if key != 'error' and isinstance(valores[key], (int, float)):
                    valores[key] = format_currency(valores[key])
                
        except Exception as e:
            print(f"Erro no processamento: {str(e)}")
            valores['error'] = "Erro ao processar valores. Verifique os dados."

    return render_template('index.html', **valores)

@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    if not PDFKIT_CONFIG:
        return "Serviço de PDF não disponível.", 503

    try:
        dados = {
            'luz_iara': request.form.get('luz_iara', 'R$ 0,00'),
            'agua_iara': request.form.get('agua_iara', 'R$ 0,00'),
            'total_iara': request.form.get('total_iara', 'R$ 0,00'),
            'luz_rodrigo': request.form.get('luz_rodrigo', 'R$ 0,00'),
            'agua_rodrigo': request.form.get('agua_rodrigo', 'R$ 0,00'),
            'total_rodrigo': request.form.get('total_rodrigo', 'R$ 0,00'),
            'now': datetime.now().strftime("%d/%m/%Y %H:%M")
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

        pdf = pdfkit.from_string(
            render_template("iara_pdf.html", **dados),
            False,
            configuration=PDFKIT_CONFIG,
            options=pdf_options
        )
        
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=Conta_de_Agua_e_Luz.pdf'
        return response

    except Exception as e:
        print(f"Erro ao gerar PDF: {str(e)}")
        return "Erro ao gerar PDF. Tente novamente.", 500

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)), debug=False)
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
        sys.exit(0)