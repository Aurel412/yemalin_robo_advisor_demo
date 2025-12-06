import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

from demo_model import get_universe, optimize_portfolio

st.set_page_config(page_title="YEMALIN Robo-Advisor - Demo", layout="wide")

st.title("YEMALIN Robo-Advisor - Demo Investisseur")
st.write(
    "Cette démo permet de tester le fonctionnement général du robo-advisor "
    "sans exposer les détails complets du modèle propriétaire."
)

# ------------------ PROFIL INVESTISSEUR (SIDEBAR) ------------------
st.sidebar.header("Profil investisseur")
horizon = st.sidebar.selectbox(
    "Horizon d'investissement",
    ["Court terme", "Moyen terme", "Long terme"],
)
risque = st.sidebar.slider(
    "Tolérance au risque (1 = prudent, 5 = agressif)",
    min_value=1,
    max_value=5,
    value=3,
)
montant = st.sidebar.number_input(
    "Montant à investir (€)",
    min_value=1000.0,
    value=10000.0,
    step=500.0,
    format="%.2f",
)

st.sidebar.header("Contraintes simples")
liquidite_min = st.sidebar.slider(
    "Pourcentage minimum en liquidités",
    min_value=0,
    max_value=50,
    value=10,
)
nb_max_actifs = st.sidebar.slider(
    "Nombre maximum d'actifs en portefeuille",
    min_value=3,
    max_value=10,
    value=6,
)

# ------------------ UNIVERS D'INVESTISSEMENT ------------------
st.header("Univers d'investissement (exemple)")
universe = get_universe()
st.dataframe(universe)

if st.button("Optimiser le portefeuille (version démo)"):
    with st.spinner("Calcul en cours..."):
        alloc, stats = optimize_portfolio(
            universe=universe,
            montant=montant,
            risque=risque,
            liquidite_min=liquidite_min / 100.0,
            nb_max_actifs=nb_max_actifs,
            horizon=horizon,
        )

    # ------------------ ALLOCATION PROPOSÉE ------------------
    st.subheader("Allocation proposée (démo)")
    st.dataframe(
        alloc.style.format({"Poids": "{:.1%}", "Montant (€)": "{:,.0f}"})
    )

    # ------------------ INDICATEURS PRINCIPAUX ------------------
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Rendement annualisé (démo)", f"{stats['expected_return']:.1%}")
        st.metric("Volatilité annualisée (démo)", f"{stats['volatility']:.1%}")
    with col2:
        st.metric("Ratio rendement/risque (score interne)", f"{stats['score']:.2f}")
        st.metric("Cash alloué", f"{stats['cash_amount']:,.0f} €")

    # ==========================================================
    #   PROJECTION DE LA VALEUR FUTURE - 3 SCÉNARIOS
    # ==========================================================
    st.subheader("Projection de la valeur future (démo)")

    horizon_proj = st.slider(
        "Horizon de projection (en années)",
        min_value=1,
        max_value=30,
        value=10,
    )

    r_central = stats["expected_return"]
    vol = stats["volatility"]

    # Scénarios simplifiés : pessimiste / central / optimiste
    r_pess = r_central - vol
    r_opt = r_central + vol

    years = np.arange(0, horizon_proj + 1)

    valeurs_pess = montant * (1 + r_pess) ** years
    valeurs_centr = montant * (1 + r_central) ** years
    valeurs_opt = montant * (1 + r_opt) ** years

    val_pess_T = valeurs_pess[-1]
    val_centr_T = valeurs_centr[-1]
    val_opt_T = valeurs_opt[-1]

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(f"Valeur pessimiste à {horizon_proj} ans", f"{val_pess_T:,.0f} €")
    with c2:
        st.metric(f"Valeur centrale à {horizon_proj} ans", f"{val_centr_T:,.0f} €")
    with c3:
        st.metric(f"Valeur optimiste à {horizon_proj} ans", f"{val_opt_T:,.0f} €")

    st.markdown("**Projection de la valeur du portefeuille (démo)**")

    df_proj = pd.DataFrame(
        {
            "Année": years,
            "Scénario pessimiste": valeurs_pess,
            "Scénario central": valeurs_centr,
            "Scénario optimiste": valeurs_opt,
        }
    )

    df_proj_long = df_proj.melt(
        id_vars="Année",
        var_name="Scénario",
        value_name="Valeur",
    )

    chart_proj = (
        alt.Chart(df_proj_long)
        .mark_line(point=True)
        .encode(
            x=alt.X("Année:Q", title="Année"),
            y=alt.Y("Valeur:Q", title="Valeur du portefeuille (€)"),
            color=alt.Color("Scénario:N", title="Scénario"),
            tooltip=[
                alt.Tooltip("Année:Q", title="Année"),
                alt.Tooltip("Scénario:N", title="Scénario"),
                alt.Tooltip("Valeur:Q", title="Valeur", format=",.0f"),
            ],
        )
        .properties(height=350)
    )
    st.altair_chart(chart_proj, use_container_width=True)

    # ==========================================================
    #   FRONTIÈRE EFFICIENTE (VERSION DÉMO COLORÉE)
    # ==========================================================
    st.subheader("Frontière efficiente (version démo simplifiée)")

    points = []
    for r_level in range(1, 6):
        _, s_tmp = optimize_portfolio(
            universe=universe,
            montant=montant,
            risque=r_level,
            liquidite_min=liquidite_min / 100.0,
            nb_max_actifs=nb_max_actifs,
            horizon=horizon,
        )
        points.append(
            {
                "Profil_risque": r_level,
                "Volatilité": s_tmp["volatility"],
                "Rendement": s_tmp["expected_return"],
                "Actuel": "Profil sélectionné" if r_level == risque else "Autre niveau",
            }
        )

    df_frontier = pd.DataFrame(points)

    chart_points = (
        alt.Chart(df_frontier)
        .mark_circle()
        .encode(
            x=alt.X("Volatilité:Q", title="Volatilité annualisée"),
            y=alt.Y("Rendement:Q", title="Rendement annualisé"),
            color=alt.Color("Profil_risque:O", title="Niveau de risque"),
            size=alt.Size(
                "Actuel:N",
                title="Portefeuille",
                scale=alt.Scale(range=[80, 200]),
            ),
            tooltip=[
                alt.Tooltip("Profil_risque:O", title="Profil de risque"),
                alt.Tooltip("Rendement:Q", title="Rendement", format=".1%"),
                alt.Tooltip("Volatilité:Q", title="Volatilité", format=".1%"),
                "Actuel",
            ],
        )
    )

    chart_line = (
        alt.Chart(df_frontier.sort_values("Volatilité"))
        .mark_line(strokeWidth=2)
        .encode(
            x="Volatilité:Q",
            y="Rendement:Q",
            color=alt.value("#999999"),
        )
    )

    st.altair_chart(chart_line + chart_points, use_container_width=True)

    st.info(
        "⚠️ Cette version est une approximation simplifiée à des fins de démonstration. "
        "Le moteur complet d'optimisation reste propriétaire."
    )
else:
    st.warning("Clique sur **Optimiser le portefeuille** pour générer une proposition d'allocation.")
