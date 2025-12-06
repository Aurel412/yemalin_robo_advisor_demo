import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from demo_model import get_universe, optimize_portfolio, compute_efficient_frontier


st.set_page_config(page_title="YEMALIN Robo-Advisor - Demo", layout="wide")

st.title("YEMALIN Robo-Advisor - Demo Investisseur")
st.write(
    "Cette démo permet de tester le fonctionnement général du robo-advisor "
    "sans exposer les détails complets du modèle propriétaire."
)

# -------------------------------------------------------------------
# Profil investisseur
# -------------------------------------------------------------------
st.sidebar.header("Profil investisseur")
horizon = st.sidebar.selectbox("Horizon d'investissement", ["Court terme", "Moyen terme", "Long terme"])
risque = st.sidebar.slider("Tolérance au risque (1 = prudent, 5 = agressif)", 1, 5, 3)
montant = st.sidebar.number_input("Montant à investir (€)", min_value=1000.0, value=10000.0, step=500.0)

st.sidebar.header("Contraintes simples")
liquidite_min = st.sidebar.slider("Pourcentage minimum en liquidités", 0, 50, 10)
nb_max_actifs = st.sidebar.slider("Nombre maximum d'actifs en portefeuille", 3, 10, 6)

# -------------------------------------------------------------------
# Univers
# -------------------------------------------------------------------
st.header("Univers d'investissement (exemple)")
universe = get_universe()
st.dataframe(universe)

# -------------------------------------------------------------------
# Optimisation
# -------------------------------------------------------------------
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

    # ---------------- Allocation ----------------
    st.subheader("Allocation proposée (démo)")
    st.dataframe(alloc.style.format({"Poids": "{:.1%}", "Montant (€)": "{:,.0f}"}))

    mu = stats["expected_return"]
    sigma = stats["volatility"]
    score = stats["score"]
    cash_amount = stats["cash_amount"]

    # mapping horizon (pour le gain espéré)
    if horizon == "Court terme":
        horizon_years = 3
    elif horizon == "Moyen terme":
        horizon_years = 5
    else:
        horizon_years = 10

    valeur_future = montant * (1 + mu) ** horizon_years
    gain_espere = valeur_future - montant

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Rendement annualisé (démo)", f"{mu:.1%}")
        st.metric("Volatilité annualisée (démo)", f"{sigma:.1%}")
    with col2:
        st.metric("Ratio rendement/risque (score interne)", f"{score:.2f}")
        st.metric("Cash alloué", f"{cash_amount:,.0f} €")
    with col3:
        st.metric(f"Gain espéré sur {horizon_years} ans (démo)", f"{gain_espere:,.0f} €")
        st.metric("Valeur future estimée", f"{valeur_future:,.0f} €")

    # -------------------------------------------------------------------
    # Projection de la valeur future (démo)
    # -------------------------------------------------------------------
    st.subheader("Projection de la valeur future (démo)")

    horizon_annees = st.slider(
        "Horizon de projection (en années)",
        min_value=1,
        max_value=30,
        value=horizon_years,
        help="Projection indicative basée sur le rendement et la volatilité du portefeuille."
    )

    annees = np.arange(0, horizon_annees + 1)

    mu_pess = max(mu - sigma, -0.99)  # éviter les puissances négatives folles
    valeur_centrale = montant * (1 + mu) ** annees
    valeur_pessimiste = montant * (1 + mu_pess) ** annees
    valeur_optimiste = montant * (1 + (mu + sigma)) ** annees

    df_proj = pd.DataFrame({
        "Année": annees,
        "Scénario pessimiste": valeur_pessimiste,
        "Scénario central": valeur_centrale,
        "Scénario optimiste": valeur_optimiste,
    })

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(f"Valeur pessimiste à {horizon_annees} ans", f"{valeur_pessimiste[-1]:,.0f} €")
    with c2:
        st.metric(f"Valeur centrale à {horizon_annees} ans", f"{valeur_centrale[-1]:,.0f} €")
    with c3:
        st.metric(f"Valeur optimiste à {horizon_annees} ans", f"{valeur_optimiste[-1]:,.0f} €")

    df_proj_melt = df_proj.melt(id_vars="Année", var_name="Scénario", value_name="Valeur")

    fig_proj = px.line(
        df_proj_melt,
        x="Année",
        y="Valeur",
        color="Scénario",
        title="Projection de la valeur du portefeuille (démo)",
        labels={"Valeur": "Valeur du portefeuille (€)"}
    )
    st.plotly_chart(fig_proj, use_container_width=True)

    st.caption(
        "Cette projection est purement indicative et basée sur une version simplifiée du modèle "
        "(rendement et volatilité constants). Elle ne constitue pas une garantie de performance."
    )

    # -------------------------------------------------------------------
    # Frontière efficiente (démo)
    # -------------------------------------------------------------------
    st.subheader("Frontière efficiente (démo)")

    frontier = compute_efficient_frontier(universe)

    fig_front = go.Figure()

    fig_front.add_trace(
        go.Scatter(
            x=frontier["Volatilite_portefeuille"],
            y=frontier["Rendement_portefeuille"],
            mode="lines",
            name="Frontière efficiente",
            line=dict(color="#4CAF50", width=3),
            hovertemplate="Volatilité : %{x:.2%}<br>Rendement espéré : %{y:.2%}<extra></extra>",
        )
    )

    fig_front.add_trace(
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

    fig_front.add_trace(
        go.Scatter(
            x=[sigma],
            y=[mu],
            mode="markers+text",
            name="Portefeuille proposé",
            marker=dict(size=14, color="#1E88E5"),
            text=["Portefeuille YEMALIN"],
            textposition="top center",
            hovertemplate="<b>Portefeuille YEMALIN</b><br>Volatilité : %{x:.2%}<br>Rendement espéré : %{y:.2%}<extra></extra>",
        )
    )

    fig_front.update_layout(
        template="plotly_white",
        title="Frontière efficiente (rendement vs risque)",
        title_font=dict(size=20),
        xaxis=dict(
            title="Volatilité du portefeuille (σ)",
            showgrid=True,
            gridcolor="lightgray",
            tickformat=".1%",
        ),
        yaxis=dict(
            title="Rendement espéré du portefeuille (µ)",
            showgrid=True,
            gridcolor="lightgray",
            tickformat=".1%",
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

    st.plotly_chart(fig_front, use_container_width=True)

    st.info(
        "⚠️ La frontière et la projection sont basées sur une approximation simplifiée "
        "pour la démonstration. Le moteur complet d'optimisation (covariances détaillées, "
        "scénarios de marché, stress tests, etc.) reste propriétaire."
    )

else:
    st.warning("Clique sur **Optimiser le portefeuille** pour générer une proposition d'allocation.")
