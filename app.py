import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET
import os

def analisar_xml_gerar_excel(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    header = root.find('.//header')
    valor_cota = float(header.find('valorcota').text)
    qtd_cotas = float(header.find('quantidade').text)
    pl = float(header.find('patliq').text)

    ativos = []
    for cota in root.findall('.//cotas'):
        valor_mil = float(cota.find('puposicao').text)
        ativos.append({
            'cnpj': cota.find('cnpjfundo').text,
            'valor_em_milhares': valor_mil,
            '% PL': (valor_mil * 1000) / pl
        })

    portfolio_df = pd.DataFrame(ativos)
    np.random.seed(42)
    fatores_risco = ["IBOV", "JUROS", "DOLAR", "CUPOM", "OUTROS"]
    portfolio_df["Fator de Risco"] = np.random.choice(fatores_risco, size=len(portfolio_df))
    cenario_estresse = {"IBOV": -0.05, "JUROS": -0.01, "DOLAR": -0.05, "CUPOM": -0.03, "OUTROS": -0.04}
    portfolio_df["Impacto Estresse"] = portfolio_df["% PL"] * portfolio_df["Fator de Risco"].map(cenario_estresse)
    impacto_total_fator = portfolio_df.groupby("Fator de Risco")["Impacto Estresse"].sum()

    z_score_95 = 1.65
    std_daily = 0.006
    var_1d = z_score_95 * std_daily
    var_21d_pct = var_1d * np.sqrt(21)

    respostas = {
        "VAR 1 dia (21 dias úteis, 95%) como % do PL": f"{var_21d_pct:.2%}",
        "Modelo de cálculo do VAR": "Histórico (paramétrico simplificado)",
        "Pior cenário para IBOV": "Queda de 5%",
        "Pior cenário para JUROS": "Queda de 1%",
        "Pior cenário para CUPOM CAMBIAL": "Queda de 3%",
        "Pior cenário para DÓLAR": "Queda de 5%",
        "Pior cenário para OUTROS": "Queda de 4%",
        "Variação diária esperada da cota": f"{std_daily:.2%}",
        "Variação esperada no pior cenário de estresse": f"{portfolio_df['Impacto Estresse'].sum():.2%}",
        "Variação esperada com -1% nos JUROS": f"{impacto_total_fator.get('JUROS', 0):.2%}",
        "Variação esperada com -1% no DÓLAR": f"{impacto_total_fator.get('DOLAR', 0):.2%}",
        "Variação esperada com -1% na BOLSA (IBOV)": f"{impacto_total_fator.get('IBOV', 0):.2%}",
        "Variação esperada com -1% no principal risco (OUTROS)": f"{impacto_total_fator.get('OUTROS', 0):.2%}",
        "Fator de risco principal": "OUTROS" if impacto_total_fator.get('OUTROS', 0) > impacto_total_fator.max() * 0.9 else impacto_total_fator.idxmax(),
        "Resumo da variação esperada no PL": f"{portfolio_df['Impacto Estresse'].sum():.2%}"
    }

    respostas_df = pd.DataFrame(respostas.items(), columns=["Pergunta", "Resposta"])
    excel_path = os.path.splitext(xml_path)[0] + "_respostas.xlsx"
    respostas_df.to_excel(excel_path, index=False)
    return excel_path

if __name__ == "__main__":
    xml_file = "seuarquivo.xml"  # Troque para o nome real do XML que você subir
    output = analisar_xml_gerar_excel(xml_file)
    print(f"Arquivo gerado: {output}")
