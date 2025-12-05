import streamlit as st
import pandas as pd
from demo_model import get_universe, optimize_portfolio, compute_efficient_frontier
import plotly.express as px

st.set_page_config(page_title="YEMALIN Robo-Advisor - Demo", layout="wide")

st.title("YEMALIN Robo-Advisor - Démo Investisseur")
st.write(
    "Cette démo permet de tester le fonctionnement général du robo-advisor "
    "sans exposer les détails complets du modèle propriétaire."
)

# -------------------------
# Barre latérale : profil
# -------------------------
st.sidebar.header("Profil investisseur")
horizon = st.sidebar.selectbox("Horizon d'investissement", ["Court terme", "Moyen terme", "Long terme"])
risque = st.sidebar.slider("Tolérance au risque (1 = prudent, 5 = agressif)", 1, 5, 3)
montant = st.sidebar.number_input("Montant à investir (€)", min_value=1000.0, value=10000.0, step=500.0)

st.sidebar.header("Contraintes simples")
liquidite_min = st.sidebar.slider("Pourcentage minimum en liquidités", 0, 50, 10)
nb_max_actifs = st.sidebar.slider("Nombre maximum d'actifs en portefeuille", 3, 10, 6)

# -------------------------
# Univers
# -------------------------
st.header("Univers d'investissement (exemple)")
universe = get_universe()
st.dataframe(universe)

# -------------------------
# Optimisation + affichage
# -------------------------
if st.button("Optimiser le portefeuille (version démo)"):
    with st.spinner("Calcul en cours..."):
        alloc, stats = optimize_portfolio(
            universe,
            montant=montant,
            risque=risque,
            liquidite_min=liquidite_min / 100.0,
            nb_max_actifs=nb_max_actifs,
            horizon=horizon,
        )

    st.subheader("Allocation proposée (démo)")
    st.dataframe(alloc.style.format({"Poids": "{:.1%}", "Montant (€)": "{:,.0f}"}))

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Rendement annualisé (démo)", f"{stats['expected_return']:.1%}")
        st.metric("Volatilité annualisée (démo)", f"{stats['volatility']:.1%}")
    with col2:
        st.metric("Ratio rendement/risque (score interne)", f"{stats['score']:.2f}")
        st.metric("Cash alloué", f"{stats['cash_amount']:,.0f} €")

    # -------------------------
    # Frontière efficiente
    # -------------------------
    st.subheader("Frontière efficiente (démo)")

    frontier = compute_efficient_frontier(universe)

    fig = px.line(
        frontier,
        x="Volatilite_portefeuille",
        y="Rendement_portefeuille",
        title="Frontière efficiente (démo)",
        labels={
            "Volatilite_portefeuille": "Volatilité du portefeuille",
            "Rendement_portefeuille": "Rendement espéré du portefeuille",
        },
    )

    # Point du portefeuille proposé
    fig.add_scatter(
        x=[stats["volatility"]],
        y=[stats["expected_return"]],
        mode="markers",
        name="Portefeuille proposé",
    )

    st.plotly_chart(fig, use_container_width=True)

    st.info(
        "⚠️ Cette version est une approximation simplifiée à des fins de démonstration. "
        "Le moteur complet d'optimisation reste propriétaire."
    )
else:
    st.warning("Clique sur **Optimiser le portefeuille** pour générer une proposition d'allocation.")
