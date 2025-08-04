from flask import Flask, request, render_template_string
import xml.etree.ElementTree as ET

app = Flask(__name__)

FORM_HTML = """
<!doctype html>
<title>Upload XML</title>
<h2>Enviar XML da Carteira</h2>
<form method=post enctype=multipart/form-data>
  <input type=file name=xmlfile>
  <input type=submit value=Analisar>
</form>
{% if resultado %}
  <h3>Resultado:</h3>
  <pre>{{ resultado }}</pre>
{% endif %}
"""

@app.route("/", methods=["GET", "POST"])
def index():
    resultado = ""
    if request.method == "POST":
        file = request.files.get("xmlfile")
        if not file:
            resultado = "Nenhum arquivo enviado."
        else:
            try:
                tree = ET.parse(file)
                root = tree.getroot()
                pl = root.findtext(".//PatrimonioLiquido")
                cota = root.findtext(".//Cota")
                rent_mes = root.findtext(".//RentabMes")

                # Cálculo simples de VaR
                pl_float = float(pl.replace(',', '.'))
                rent_mes_float = float(rent_mes.replace(',', '.')) / 100
                var_pct = round(rent_mes_float * 2.33 / (21**0.5) * 100, 2)
                var_valor = round(pl_float * var_pct / 100, 2)

                resultado = f"""
PL: R$ {pl}
Cota: {cota}
Rentab Mês: {rent_mes}%

📉 VaR estimado (21d, 95%): {var_pct}%
Valor estimado do VaR: R$ {var_valor}
"""
            except Exception as e:
                resultado = f"Erro ao ler XML: {str(e)}"
    return render_template_string(FORM_HTML, resultado=resultado)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

          
