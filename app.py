import streamlit as st
import pandas as pd
from demo_model import get_universe, optimize_portfolio, compute_efficient_frontier
import plotly.graph_objects as go

# --------------------------------------------------
# Configuration générale de la page
# --------------------------------------------------
st.set_page_config(
    page_title="YEMALIN Robo-Advisor - Démo Investisseur",
    layout="wide"
)

st.title("YEMALIN Robo-Advisor - Démo Investisseur")
st.write(
    "Cette démo illustre le fonctionnement général du robo-advisor YEMALIN : "
    "profil investisseur, allocation d’actifs, mesure du risque et visualisation "
    "de la frontière efficiente. Le moteur complet d’optimisation reste propriétaire."
)

# --------------------------------------------------
# Barre latérale : profil investisseur + contraintes
# --------------------------------------------------
st.sidebar.header("Profil de l'investisseur")
horizon = st.sidebar.selectbox(
    "Horizon d'investissement",
    ["Court terme", "Moyen terme", "Long terme"]
)
risque = st.sidebar.slider(
    "Tolérance au risque (1 = prudent, 5 = agressif)",
    min_value=1,
    max_value=5,
    value=3
)
montant = st.sidebar.number_input(
    "Montant à investir (€)",
    min_value=1000.0,
    value=10000.0,
    step=500.0
)

st.sidebar.header("Contraintes simples")
liquidite_min = st.sidebar.slider(
    "Pourcentage minimum en liquidités",
    min_value=0,
    max_value=50,
    value=10
)
nb_max_actifs = st.sidebar.slider(
    "Nombre maximum d'actifs en portefeuille",
    min_value=3,
    max_value=10,
    value=6
)

# --------------------------------------------------
# Univers d’investissement
# --------------------------------------------------
st.header("Univers d'investissement (exemple)")
universe = get_universe()
st.dataframe(universe)

# --------------------------------------------------
# Optimisation + affichage des résultats
# --------------------------------------------------
if st.button("Optimiser le portefeuille (version démo)"):
    with st.spinner("Calcul de l'allocation en cours..."):
        alloc, stats = optimize_portfolio(
            universe,
            montant=montant,
            risque=risque,
            liquidite_min=liquidite_min / 100.0,
            nb_max_actifs=nb_max_actifs,
            horizon=horizon,
        )

    # ------------------ Allocation ------------------
    st.subheader("Allocation proposée (démo)")
    st.dataframe(
        alloc.style.format(
            {
                "Poids": "{:.1%}",
                "Montant (€)": "{:,.0f}",
            }
        )
    )

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Rendement annualisé (démo)", f"{stats['expected_return']:.1%}")
        st.metric("Volatilité annualisée (démo)", f"{stats['volatility']:.1%}")
    with col2:
        st.metric("Ratio rendement/risque (score interne)", f"{stats['score']:.2f}")
        st.metric("Cash alloué", f"{stats['cash_amount']:,.0f} €")

    # --------------------------------------------------
    # Frontière efficiente (version démo, visualisation pro)
    # --------------------------------------------------
    st.subheader("Frontière efficiente (démo)")

    frontier = compute_efficient_frontier(universe)

    fig = go.Figure()

    # Courbe de frontière efficiente
    fig.add_trace(
        go.Scatter(
            x=frontier["Volatilite_portefeuille"],
            y=frontier["Rendement_portefeuille"],
            mode="lines",
            name="Frontière efficiente",
            line=dict(color="#4CAF50", width=3),
            hovertemplate=(
                "Volatilité : %{x:.2%}<br>"
                "Rendement espéré : %{y:.2%}<extra></extra>"
            ),
        )
    )

    # Zone ombrée sous la frontière (effet premium)
    fig.add_trace(
        go.Scatter(
            x=frontier["Volatilite_portefeuille"],
            y=frontier["Rendement_portefeuille"],
            mode="lines",
            line=dict(color="rgba(76, 175, 80, 0.0)"),
            fill="tozeroy",
            fillcolor="rgba(76, 175, 80, 0.10)",
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # Point du portefeuille proposé par YEMALIN
    fig.add_trace(
        go.Scatter(
            x=[stats["volatility"]],
            y=[stats["expected_return"]],
            mode="markers+text",
            name="Portefeuille proposé",
            marker=dict(size=14, color="#1E88E5"),
            text=["Portefeuille YEMALIN"],
            textposition="top center",
            hovertemplate=(
                "<b>Portefeuille YEMALIN</b><br>"
                "Volatilité : %{x:.2%}<br>"
                "Rendement espéré : %{y:.2%}<extra></extra>"
            ),
        )
    )

    # Mise en forme du graphique
    fig.update_layout(
        template="plotly_white",
        title="Frontière efficiente (rendement vs risque)",
        title_font=dict(size=20),
        xaxis=dict(
            title="Volatilité du portefeuille (σ)",
            showgrid=True,
            gridcolor="lightgray",
            tickformat=".0%",
        ),
        yaxis=dict(
            title="Rendement espéré du portefeuille (µ)",
            showgrid=True,
            gridcolor="lightgray",
            tickformat=".0%",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0.0,
        ),
        margin=dict(l=40, r=40, t=60, b=40),
        hovermode="closest",
    )

    st.plotly_chart(fig, use_container_width=True)

    st.info(
        "⚠️ Cette visualisation est basée sur une approximation simplifiée de la frontière "
        "efficiente pour la démo. Le moteur complet d’optimisation (matrices de covariance, "
        "scénarios de marché, stress tests, etc.) reste propriétaire et peut être présenté "
        "séparément sous NDA."
    )

else:
    st.warning(
        "Clique sur **Optimiser le portefeuille (version démo)** pour générer une allocation "
        "et la positionner sur la frontière efficiente."
    )
