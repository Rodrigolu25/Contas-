from flask import Flask, render_template, request, make_response
import pdfkit
import locale
import os
from datetime import datetime

app = Flask(__name__)

# Configuração adaptável do PDFKit para diferentes ambientes
PDFKIT_CONFIG = None

# Verifica se estamos no Render (variável de ambiente específica)
IS_RENDER = os.getenv('RENDER', '').lower() == 'true'

if IS_RENDER:
    # Configuração para o Render (usando o pacote system-installed)
    try:
        PDFKIT_CONFIG = pdfkit.configuration()
    except Exception as e:
        print(f"Erro na configuração do PDFKit no Render: {str(e)}")
else:
    # Configuração para desenvolvimento local
    WKHTMLTOPDF_PATH = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    if os.path.exists(WKHTMLTOPDF_PATH):
        try:
            PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)
            # Teste básico
            pdfkit.from_string('<html><body><h1>Test</h1></body></html>', False, configuration=PDFKIT_CONFIG)
        except Exception as e:
            print(f"Erro na configuração local do PDFKit: {str(e)}")

@app.route('/', methods=['GET', 'POST'])
def index():
    total_iara = total_rodrigo = luz_iara = agua_iara = luz_rodrigo = agua_rodrigo = ""

    if request.method == 'POST':
        try:
            valor_luz_texto = request.form.get('luz', '').replace("R$", "").replace(".", "").replace(",", ".").strip()
            valor_agua_texto = request.form.get('agua', '').replace("R$", "").replace(".", "").replace(",", ".").strip()

            valor_luz = float(valor_luz_texto) if valor_luz_texto else 0
            valor_agua = float(valor_agua_texto) if valor_agua_texto else 0

            # Cálculos
            iaraluz = valor_luz / 3
            iaraagua = valor_agua / 2
            luz_iara = iaraluz
            agua_iara = iaraagua
            total_iara = luz_iara + agua_iara

            rodrigoluz = valor_luz / 3 * 2
            rodrigoagua = valor_agua / 2
            luz_rodrigo = rodrigoluz
            agua_rodrigo = rodrigoagua
            total_rodrigo = rodrigoluz + rodrigoagua

            # Formatação de moeda com fallback
            try:
                locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
            except:
                locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
            
            def format_currency(value):
                try:
                    return locale.currency(value, grouping=True, symbol=True)
                except:
                    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            total_iara = format_currency(total_iara)
            luz_iara = format_currency(luz_iara)
            agua_iara = format_currency(agua_iara)
            luz_rodrigo = format_currency(luz_rodrigo)
            agua_rodrigo = format_currency(agua_rodrigo)
            total_rodrigo = format_currency(total_rodrigo)
        
        except Exception as e:
            print(f"Erro no processamento: {str(e)}")
            return render_template('index.html', error="Ocorreu um erro ao processar os valores. Verifique os dados e tente novamente.")

    return render_template('index.html', 
                         total_iara=total_iara, 
                         luz_iara=luz_iara, 
                         agua_iara=agua_iara,
                         luz_rodrigo=luz_rodrigo, 
                         agua_rodrigo=agua_rodrigo, 
                         total_rodrigo=total_rodrigo)

@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    if not PDFKIT_CONFIG:
        return "Serviço de PDF não disponível. Contate o administrador.", 503

    try:
        # Obter dados do formulário
        data = {field: request.form.get(field, 'R$ 0,00') 
               for field in ['luz_iara', 'agua_iara', 'total_iara', 
                            'luz_rodrigo', 'agua_rodrigo', 'total_rodrigo']}

        rendered_html = render_template(
            "iara_pdf.html",
            **data,
            now=datetime.now().strftime("%d/%m/%Y %H:%M")
        )

        options = {
            'page-size': 'A4',
            'margin-top': '15mm',
            'margin-right': '15mm',
            'margin-bottom': '15mm',
            'margin-left': '15mm',
            'encoding': 'UTF-8',
            'quiet': '',
            'enable-local-file-access': None
        }

        pdf = pdfkit.from_string(rendered_html, False, configuration=PDFKIT_CONFIG, options=options)
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=Conta_de_Agua_e_Luz.pdf'
        
        return response

    except Exception as e:
        print(f"Erro ao gerar PDF: {str(e)}")
        return f"Erro ao gerar PDF: {str(e)}", 500

if __name__ == '__main__':
    # Configuração de locale com fallbacks
    for loc in ['pt_BR.UTF-8', 'Portuguese_Brazil.1252', '']:
        try:
            locale.setlocale(locale.LC_ALL, loc)
            break
        except:
            continue
    
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))