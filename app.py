import streamlit as st
import pandas as pd
import numpy as np

from demo_model import get_universe, optimize_portfolio, compute_efficient_frontier

import plotly.graph_objects as go
import plotly.express as px


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
    "profil investisseur, allocation d’actifs, mesure du risque, visualisation "
    "de la frontière efficiente et projection de la valeur future du portefeuille. "
    "Le moteur complet d’optimisation reste propriétaire."
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
    # Projection de la valeur future (démo)
    # --------------------------------------------------
    st.subheader("Projection de la valeur future (démo)")

    horizon_annees = st.slider(
        "Horizon de projection (en années)",
        min_value=1,
        max_value=30,
        value=10,
        help="Projection indicative basée sur le rendement et la volatilité du portefeuille."
    )

    mu = stats["expected_return"]
    sigma = stats["volatility"]

    annees = np.arange(0, horizon_annees + 1)

    # On évite des taux trop négatifs
    mu_pess = max(mu - sigma, -0.99)

    valeur_centrale = montant * (1 + mu) ** annees
    valeur_pessimiste = montant * (1 + mu_pess) ** annees
    valeur_optimiste = montant * (1 + (mu + sigma)) ** annees

    df_proj = pd.DataFrame({
        "Année": annees,
        "Scénario pessimiste": valeur_pessimiste,
        "Scénario central": valeur_centrale,
        "Scénario optimiste": valeur_optimiste,
    })

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric(
            f"Valeur pessimiste à {horizon_annees} ans",
            f"{valeur_pessimiste[-1]:,.0f} €"
        )
    with col_b:
        st.metric(
            f"Valeur centrale à {horizon_annees} ans",
            f"{valeur_centrale[-1]:,.0f} €"
        )
    with col_c:
        st.metric(
            f"Valeur optimiste à {horizon_annees} ans",
            f"{valeur_optimiste[-1]:,.0f} €"
        )

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
            hovertemplate="Volatilité : %{x:.2%}<br>Rendement espéré : %{y:.2%}<extra></extra>",
        )
    )

    # Zone ombrée sous la frontière
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
            hovertemplate="<b>Portefeuille YEMALIN</b><br>Volatilité : %{x:.2%}<br>Rendement espéré : %{y:.2%}<extra></extra>",
        )
    )

    fig.update_layout(
        template="plotly_white",
        title="Frontière efficiente (rendement vs risque)",
        title_font=dict(size=20),
        xaxis=dict(
            title="Volatilité du portefeuille (σ)",
            showgrid=True,
            gridcolor="lightgray",
            tickformat=".1%",
            range=[0, 0.25],
        ),
        yaxis=dict(
            title="Rendement espéré du portefeuille (µ)",
            showgrid=True,
            gridcolor="lightgray",
            tickformat=".1%",
            range=[0, 0.10],
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
        "⚠️ La frontière et la projection sont basées sur une approximation simplifiée "
        "pour la démonstration. Le moteur complet d’optimisation (covariances détaillées, "
        "scénarios de marché, stress tests, etc.) reste propriétaire et peut être présenté "
        "séparément sous NDA."
    )

else:
    st.warning(
        "Clique sur **Optimiser le portefeuille (version démo)** pour générer une allocation, "
        "voir la projection de la valeur future et positionner le portefeuille sur la "
        "frontière efficiente."
    )
