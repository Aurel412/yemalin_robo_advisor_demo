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

# Mapping horizon -> nombre d'années pour la projection
YEARS_MAP = {
    "Court terme": 1,
    "Moyen terme": 3,
    "Long terme": 8,
}

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

    # ------------------ PROJECTION VALEUR FUTURE ------------------
    st.subheader("Projection de la valeur future du portefeuille (démonstration)")

    r = stats["expected_return"]
    n_years = YEARS_MAP[horizon]

    # Valeur future avec hypothèse de rendement constant
    valeur_future = montant * (1 + r) ** n_years
    gain_total = valeur_future - montant

    st.write(
        f"- Horizon considéré : **{horizon}** (≈ {n_years} ans)\n"
        f"- Rendement annuel estimé du portefeuille : **{r:.1%}**\n"
        f"- Valeur future projetée : **{valeur_future:,.0f} €**\n"
        f"- Gain cumulé estimé sur la période : **{gain_total:,.0f} €**\n\n"
        "_Ces chiffres sont purement illustratifs et ne constituent pas une garantie de performance._"
    )

    # Petite courbe de croissance dans le temps
    annees = np.arange(0, n_years + 1)
    valeurs = montant * (1 + r) ** annees
    df_proj = pd.DataFrame({"Année": annees, "Valeur_portefeuille": valeurs})

    chart_proj = (
        alt.Chart(df_proj)
        .mark_line(point=True)
        .encode(
            x=alt.X("Année:Q", title="Année"),
            y=alt.Y("Valeur_portefeuille:Q", title="Valeur du portefeuille (€)"),
            tooltip=["Année", alt.Tooltip("Valeur_portefeuille:Q", format=",.0f")],
            color=alt.value("#1f77b4"),
        )
        .properties(height=300)
    )
    st.altair_chart(chart_proj, use_container_width=True)

    # ------------------ FRONTIÈRE EFFICIENTE (DÉMO) ------------------
    st.subheader("Frontière efficiente (version démo simplifiée)")

    # On fait tourner le modèle pour différents niveaux de risque (1 à 5)
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
                "Actuel": "Profil sélectionné" if r_level == risque else "Autres profils",
            }
        )

    df_frontier = pd.DataFrame(points)

    # Graphique en couleurs – chaque point correspond à un profil de risque
    chart_frontier = (
        alt.Chart(df_frontier)
        .mark_circle(size=120)
        .encode(
            x=alt.X("Volatilité:Q", title="Volatilité annualisée"),
            y=alt.Y("Rendement:Q", title="Rendement annualisé"),
            color=alt.Color(
                "Profil_risque:O",
                title="Niveau de risque",
                scale=alt.Scale(scheme="category10"),
            ),
            shape=alt.Shape("Actuel:N", title="Statut"),
            tooltip=[
                alt.Tooltip("Profil_risque:O", title="Profil de risque"),
                alt.Tooltip("Rendement:Q", title="Rendement", format=".1%"),
                alt.Tooltip("Volatilité:Q", title="Volatilité", format=".1%"),
                "Actuel",
            ],
        )
        .properties(height=350)
    )

    # On relie les points pour visualiser la "frontière" (courbe)
    line_frontier = (
        alt.Chart(df_frontier)
        .mark_line(strokeWidth=2)
        .encode(
            x="Volatilité:Q",
            y="Rendement:Q",
            color=alt.value("lightgray"),
        )
    )

    st.altair_chart(line_frontier + chart_frontier, use_container_width=True)

    st.info(
        "⚠️ Cette version est une approximation simplifiée à des fins de démonstration. "
        "Le moteur complet d'optimisation reste propriétaire."
    )

else:
    st.warning("Clique sur **Optimiser le portefeuille** pour générer une proposition d'allocation.")
