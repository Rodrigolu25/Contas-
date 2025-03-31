from flask import Flask, render_template, request, make_response
import pdfkit
import locale
import os
from datetime import datetime

app = Flask(__name__)

# Configuração do PDFKit
PDFKIT_CONFIG = None
WKHTMLTOPDF_PATH = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"  # Ajuste conforme necessário

if os.path.exists(WKHTMLTOPDF_PATH):
    try:
        PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)
        # Teste para verificar se o wkhtmltopdf está funcionando
        pdfkit.from_string('<html><body><h1>Test</h1></body></html>', False, configuration=PDFKIT_CONFIG)
    except Exception as e:
        print(f"Erro na configuração do PDFKit: {str(e)}")
        PDFKIT_CONFIG = None
else:
    print(f"Erro: Caminho do wkhtmltopdf não encontrado em {WKHTMLTOPDF_PATH}")

@app.route('/', methods=['GET', 'POST'])
def index():
    total_iara = total_rodrigo = luz_iara = agua_iara = luz_rodrigo = agua_rodrigo = ""

    if request.method == 'POST':
        try:
            valor_luz_texto = request.form.get('luz', '').replace("R$", "").replace(".", "").replace(",", ".").strip()
            valor_agua_texto = request.form.get('agua', '').replace("R$", "").replace(".", "").replace(",", ".").strip()

            valor_luz = float(valor_luz_texto) if valor_luz_texto else 0
            valor_agua = float(valor_agua_texto) if valor_agua_texto else 0

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

            locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
            total_iara = locale.currency(total_iara, grouping=True, symbol=True)
            luz_iara = locale.currency(luz_iara, grouping=True, symbol=True)
            agua_iara = locale.currency(agua_iara, grouping=True, symbol=True)
            luz_rodrigo = locale.currency(luz_rodrigo, grouping=True, symbol=True)
            agua_rodrigo = locale.currency(agua_rodrigo, grouping=True, symbol=True)
            total_rodrigo = locale.currency(total_rodrigo, grouping=True, symbol=True)
        
        except Exception as e:
            print(f"Erro no processamento: {str(e)}")
            return render_template('index.html', error="Ocorreu um erro ao processar os valores. Verifique os dados e tente novamente.")

    return render_template('index.html', total_iara=total_iara, luz_iara=luz_iara, agua_iara=agua_iara,
                           luz_rodrigo=luz_rodrigo, agua_rodrigo=agua_rodrigo, total_rodrigo=total_rodrigo)

@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    if not PDFKIT_CONFIG:
        return "Serviço de PDF não disponível. Contate o administrador.", 503

    try:
        luz_iara = request.form.get('luz_iara', 'R$ 0,00')
        agua_iara = request.form.get('agua_iara', 'R$ 0,00')
        total_iara = request.form.get('total_iara', 'R$ 0,00')
        luz_rodrigo = request.form.get('luz_rodrigo', 'R$ 0,00')
        agua_rodrigo = request.form.get('agua_rodrigo', 'R$ 0,00')
        total_rodrigo = request.form.get('total_rodrigo', 'R$ 0,00')

        rendered_html = render_template("iara_pdf.html", luz_iara=luz_iara, agua_iara=agua_iara, total_iara=total_iara,
                                        luz_rodrigo=luz_rodrigo, agua_rodrigo=agua_rodrigo, total_rodrigo=total_rodrigo,
                                        now=datetime.now())

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
        response.headers['Content-Disposition'] = 'attachment; filename=Conta de Água e Luz.pdf'
        
        return response

    except Exception as e:
        app.logger.error(f"Erro ao gerar PDF: {str(e)}")
        return f"Erro ao gerar PDF: {str(e)}", 500

if __name__ == '__main__':
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
        except:
            print("Aviso: Não foi possível configurar o locale para português brasileiro.")
    
    app.run(debug=True)
