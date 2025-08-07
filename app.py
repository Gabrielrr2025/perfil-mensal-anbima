import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import openpyxl
import plotly.express as px

# =================== CONFIG PAGE ===================
st.set_page_config(
    page_title="VaR Calculator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============== CUSTOM STYLING ===================
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# =============== SIDEBAR ===================
with st.sidebar:
    st.markdown("### ⚙️ Configurações")
    horizonte_dias = st.selectbox("Horizonte (dias)", [1, 10, 21], index=2)
    conf_label = st.selectbox("Nível de confiança", ["95%", "99%"])
    metodo = st.selectbox("Metodologia", [
        "Paramétrico (Delta-Normal)",
        "Paramétrico + Correlações"
    ])
    conf, z = (0.95, 1.65) if conf_label == "95%" else (0.99, 2.33)

# =============== HEADER ===================
st.markdown("""
<div class="main-header">
    <div class="header-title">📊 VaR Calculator</div>
    <div class="header-subtitle">Análise de risco com múltiplas metodologias</div>
</div>
""", unsafe_allow_html=True)

# =============== FUND DATA ===================
st.markdown("""
<div class="custom-card">
    <div class="card-title">🏢 Informações do Fundo</div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    cnpj = st.text_input("CNPJ *", placeholder="00.000.000/0001-00")
with col2:
    nome_fundo = st.text_input("Nome do Fundo *", placeholder="Fundo XPTO")
with col3:
    data_ref = st.date_input("Data de Referência *")
with col4:
    pl = st.number_input("Patrimônio Líquido (R$) *", min_value=0.0, format="%.2f", value=1_000_000.0)

campos_ok = bool(cnpj.strip() and nome_fundo.strip() and pl > 0)

# =============== VOLATILIDADES / CORRELAÇÕES ===================
vols = {
    "Ações (Ibovespa)": 0.25,
    "Juros-Pré": 0.08,
    "Câmbio (Dólar)": 0.15,
    "Cupom Cambial": 0.12,
    "Crédito Privado": 0.05,
    "Multimercado": 0.18,
    "Outros": 0.10
}

correlacoes = pd.DataFrame({
    k: [1 if i == j else 0.2 for j, _ in enumerate(vols)] for i, k in enumerate(vols)
}, index=list(vols.keys()))

# =============== ALOCAÇÃO ===================
st.markdown("""
<div class="custom-card">
    <div class="card-title">📊 Alocação da Carteira</div>
</div>
""", unsafe_allow_html=True)

cols = st.columns(3)
carteira = []
for i, (classe, vol) in enumerate(vols.items()):
    with cols[i % 3]:
        perc = st.number_input(
            f"{classe}", min_value=0.0, max_value=100.0, value=0.0, step=1.0,
            help=f"Volatilidade anual: {vol:.0%}"
        )
        if perc > 0:
            carteira.append({"classe": classe, "%PL": perc, "vol_anual": vol})

total = sum(i["%PL"] for i in carteira)
pode_calcular = campos_ok and total > 0 and total <= 100

if total == 100:
    st.success(f"✅ Alocação total: {total:.1f}%")
elif total > 100:
    st.error(f"❌ Excede 100% (atual: {total:.1f}%)")
elif total > 0:
    st.warning(f"⚠️ Incompleto ({total:.1f}%)")

# =============== FUNÇÃO DE CÁLCULO ===================
def calcular_var_corr(carteira, corr, dias, z, pl):
    classes = [c['classe'] for c in carteira]
    pesos = np.array([c['%PL']/100 for c in carteira])
    vols_d = np.array([c['vol_anual']/np.sqrt(252) for c in carteira])
    mat = corr.loc[classes, classes].values
    vol_portf_d = np.sqrt(pesos @ (mat * np.outer(vols_d, vols_d)) @ pesos)
    vol_periodo = vol_portf_d * np.sqrt(dias)
    var_pct = z * vol_periodo
    var_reais = pl * var_pct
    for c in carteira:
        contrib = (c['%PL']/100) * (c['vol_anual']/np.sqrt(252)) / vol_portf_d
        var_ind = var_pct * contrib
        c.update({"VaR_%": round(var_ind*100, 2), "VaR_R$": round(pl*var_ind, 2)})
    return carteira, var_pct, var_reais

# =============== RESULTADOS ===================
if st.button("🚀 Calcular", disabled=not pode_calcular):
    with st.spinner("Calculando..."):
        if metodo == "Paramétrico + Correlações":
            carteira, var_pct, var_reais = calcular_var_corr(carteira, correlacoes, horizonte_dias, z, pl)
        else:
            for c in carteira:
                vol_d = c['vol_anual'] / np.sqrt(252)
                var_p = z * vol_d * np.sqrt(horizonte_dias)
                c.update({
                    "VaR_%": round(var_p * 100, 2),
                    "VaR_R$": round(pl * (c['%PL']/100) * var_p, 2)
                })
            var_reais = sum(c['VaR_R$'] for c in carteira)
            var_pct = var_reais / pl

        df = pd.DataFrame(carteira)
        df["Exposição"] = df["%PL"] * pl / 100
        df["Contribuição %"] = (df["VaR_R$"] / var_reais * 100).round(1)

        st.markdown("### 📈 Resultados do VaR")
        col1, col2 = st.columns(2)
        col1.metric("VaR Total (R$)", f"R$ {var_reais:,.0f}")
        col2.metric("VaR % do PL", f"{var_pct*100:.2f}%")

        st.dataframe(df, use_container_width=True)

        fig = px.bar(df, x="classe", y="VaR_R$", title="VaR por Classe")
        st.plotly_chart(fig, use_container_width=True)

        # Excel de respostas para CVM
        perguntas = [
            "CNPJ do fundo", "Portfolio",
            "Qual é o VAR (Valor de risco) de um dia como percentual do PL calculado para 21 dias úteis e 95% de confiança?",
            "Qual classe de modelos foi utilizada para o cálculo do VAR reportado na questão anterior?",
            "Qual a variação diária percentual esperada para o valor da cota?"
        ]
        respostas = [
            cnpj, nome_fundo,
            f"{var_pct*100:.2f}%",
            metodo,
            f"{(var_pct/np.sqrt(horizonte_dias)) * 100:.2f}%"
        ]
        df_resp = pd.DataFrame({"Pergunta": perguntas, "Resposta": respostas})
        output = BytesIO()
        df_resp.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)

        st.download_button(
            label="📥 Baixar Respostas CVM",
            data=output,
            file_name="respostas_cvm.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

if not campos_ok:
    st.info("⚠️ Preencha todos os campos obrigatórios acima para prosseguir.")

          
