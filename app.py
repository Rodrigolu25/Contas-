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

# Configuração do PDFKit
try:
    if IS_RENDER:
        # No Render, assumimos que wkhtmltopdf está instalado no sistema
        PDFKIT_CONFIG = pdfkit.configuration()
    else:
        # Configuração para desenvolvimento local
        WKHTMLTOPDF_PATH = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
        if os.path.exists(WKHTMLTOPDF_PATH):
            PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)
            # Teste básico
            pdfkit.from_string('<html><body><h1>Test</h1></body></html>', False, configuration=PDFKIT_CONFIG)
        else:
            print("Aviso: wkhtmltopdf não encontrado no caminho padrão. Funcionalidade de PDF estará limitada.")
except Exception as e:
    print(f"Erro na configuração do PDFKit: {str(e)}")

# Configuração de locale com fallbacks
def configure_locale():
    for loc in ['pt_BR.UTF-8', 'Portuguese_Brazil.1252', '']:
        try:
            locale.setlocale(locale.LC_ALL, loc)
            break
        except locale.Error:
            continue

configure_locale()

# Função para formatar valores monetários
def format_currency(value):
    try:
        return locale.currency(value, grouping=True, symbol=True)
    except:
        # Fallback caso o locale não funcione
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

@app.route('/', methods=['GET', 'POST'])
def index():
    # Valores padrão
    valores = {
        'total_iara': '', 'luz_iara': '', 'agua_iara': '',
        'luz_rodrigo': '', 'agua_rodrigo': '', 'total_rodrigo': '',
        'error': None
    }

    if request.method == 'POST':
        try:
            # Processamento dos valores de entrada
            valor_luz = request.form.get('luz', '0').replace("R$", "").replace(".", "").replace(",", ".").strip()
            valor_agua = request.form.get('agua', '0').replace("R$", "").replace(".", "").replace(",", ".").strip()

            # Conversão para float
            valor_luz = float(valor_luz) if valor_luz else 0
            valor_agua = float(valor_agua) if valor_agua else 0

            # Cálculos das proporções
            luz_iara = valor_luz / 3
            agua_iara = valor_agua / 2
            total_iara = luz_iara + agua_iara

            luz_rodrigo = valor_luz * 2 / 3
            agua_rodrigo = valor_agua / 2
            total_rodrigo = luz_rodrigo + agua_rodrigo

            # Formatação dos valores
            valores.update({
                'total_iara': format_currency(total_iara),
                'luz_iara': format_currency(luz_iara),
                'agua_iara': format_currency(agua_iara),
                'luz_rodrigo': format_currency(luz_rodrigo),
                'agua_rodrigo': format_currency(agua_rodrigo),
                'total_rodrigo': format_currency(total_rodrigo)
            })
        
        except Exception as e:
            print(f"Erro no processamento: {str(e)}")
            valores['error'] = "Ocorreu um erro ao processar os valores. Verifique os dados e tente novamente."

    return render_template('index.html', **valores)

@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    if not PDFKIT_CONFIG:
        return "Serviço de PDF não disponível. Contate o administrador.", 503

    try:
        # Dados do formulário
        dados = {
            'luz_iara': request.form.get('luz_iara', 'R$ 0,00'),
            'agua_iara': request.form.get('agua_iara', 'R$ 0,00'),
            'total_iara': request.form.get('total_iara', 'R$ 0,00'),
            'luz_rodrigo': request.form.get('luz_rodrigo', 'R$ 0,00'),
            'agua_rodrigo': request.form.get('agua_rodrigo', 'R$ 0,00'),
            'total_rodrigo': request.form.get('total_rodrigo', 'R$ 0,00'),
            'now': datetime.now().strftime("%d/%m/%Y %H:%M")
        }

        # Renderização do template PDF
        rendered_html = render_template("iara_pdf.html", **dados)

        # Opções do PDF
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

        # Geração do PDF
        pdf = pdfkit.from_string(rendered_html, False, configuration=PDFKIT_CONFIG, options=options)
        
        # Configuração da resposta
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=Conta_de_Agua_e_Luz.pdf'
        
        return response

    except Exception as e:
        print(f"Erro ao gerar PDF: {str(e)}")
        return f"Erro ao gerar PDF: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))