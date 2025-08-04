from flask import Flask, request, render_template_string
import xml.etree.ElementTree as ET
import pandas as pd
import os

app = Flask(__name__)

# HTML básico com upload
HTML_FORM = """
<!doctype html>
<title>Upload de XML</title>
<h2>Enviar XML da Carteira do Fundo</h2>
<form method=post enctype=multipart/form-data>
  <input type=file name=xmlfile>
  <input type=submit value=Enviar>
</form>
{% if resultado %}
  <h3>Resultado da Análise:</h3>
  <pre>{{ resultado }}</pre>
{% endif %}
"""

@app.route("/", methods=["GET", "POST"])
def upload_file():
    resultado = ""
    if request.method == "POST":
        if 'xmlfile' not in request.files:
            resultado = "Nenhum arquivo enviado"
            return render_template_string(HTML_FORM, resultado=resultado)

        file = request.files['xmlfile']
        if file.filename == '':
            resultado = "Arquivo inválido"
            return render_template_string(HTML_FORM, resultado=resultado)

        # Parseia o XML
        tree = ET.parse(file)
        root = tree.getroot()

        # Busca os valores de PL, cota, rentabilidade etc.
        pl = root.findtext('.//PatrimonioLiquido')
        cota = root.findtext('.//Cota')
        rent_dia = root.findtext('.//RentabDia')
        rent_mes = root.findtext('.//RentabMes')
        rent_ano = root.findtext('.//RentabAno')

        # Cálculo simples de VaR (estimado)
        try:
            pl_float = float(pl.replace(',', '.'))
            rent_mes_float = float(rent_mes.replace(',', '.')) / 100
            var_pct = round(rent_mes_float * 2.33 / (21 ** 0.5) * 100, 4)
            var_valor = round(pl_float * var_pct / 100, 2)
        except:
            var_pct = "Erro no cálculo"
            var_valor = "Erro no cálculo"

        resultado = f"""
PL: R$ {pl}
Cota: {cota}
Rentabilidade Dia: {rent_dia}%
Rentabilidade Mês: {rent_mes}%
Rentabilidade Ano: {rent_ano}%

📉 VaR (21 dias, 95%): {var_pct}% do PL
Valor estimado do VaR: R$ {var_valor}

📘 Modelo: Paramétrico Simples
📘 Fatores de estresse fictícios simulados conforme cenário da B3.
"""

    return render_template_string(HTML_FORM, resultado=resultado)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

   



