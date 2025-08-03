from flask import Flask, request, render_template, send_file
import pandas as pd
import xml.etree.ElementTree as ET
import os

app = Flask(__name__)

def analisar_xml_gerar_excel(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Simulação de respostas (substituir com a lógica real)
    respostas = {
        "Qual é o VAR (Valor de risco)...": "2,48%",
        "Classe de modelo utilizada": "Paramétrico – Variância-Covariância",
        "Cenário estresse IBOVESPA": "Queda de 15%",
        "Cenário estresse Dólar": "Alta de 10%",
    }

    df_respostas = pd.DataFrame(respostas.items(), columns=["Pergunta", "Resposta"])
    output_path = "respostas_geradas.xlsx"
    df_respostas.to_excel(output_path, index=False)
    return output_path

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "xmlfile" not in request.files:
            return "Nenhum arquivo enviado."
        file = request.files["xmlfile"]
        if file.filename == "":
            return "Nome de arquivo vazio."
        if file:
            filepath = os.path.join("uploads", file.filename)
            os.makedirs("uploads", exist_ok=True)
            file.save(filepath)

            output_excel = analisar_xml_gerar_excel(filepath)
            return send_file(output_excel, as_attachment=True)
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)


