import pandas as pd
import numpy as np


def get_universe() -> pd.DataFrame:
    data = [
        {"Ticker": "EUROSTOXX50", "Classe": "Actions", "Rendement_attendu": 0.07, "Volatilite": 0.15},
        {"Ticker": "MSCI_WORLD", "Classe": "Actions", "Rendement_attendu": 0.08, "Volatilite": 0.16},
        {"Ticker": "CORP_BBB", "Classe": "Obligations", "Rendement_attendu": 0.04, "Volatilite": 0.06},
        {"Ticker": "GOV_CORE", "Classe": "Obligations", "Rendement_attendu": 0.02, "Volatilite": 0.03},
        {"Ticker": "GOLD", "Classe": "Matières premières", "Rendement_attendu": 0.05, "Volatilite": 0.20},
        {"Ticker": "REIT_EU", "Classe": "Immobilier coté", "Rendement_attendu": 0.06, "Volatilite": 0.18},
        {"Ticker": "MONEY_MKT", "Classe": "Monétaire", "Rendement_attendu": 0.015, "Volatilite": 0.01},
    ]
    return pd.DataFrame(data)


def _risk_aversion_from_profile(risque: int, horizon: str) -> float:
    base = {1: 8.0, 2: 4.0, 3: 2.5, 4: 1.7, 5: 1.2}[risque]
    if horizon == "Court terme":
        base *= 1.2
    elif horizon == "Long terme":
        base *= 0.8
    return base


def optimize_portfolio(universe: pd.DataFrame,
                       montant: float,
                       risque: int,
                       liquidite_min: float,
                       nb_max_actifs: int,
                       horizon: str):
    lam = _risk_aversion_from_profile(risque, horizon)

    risky = universe[universe["Classe"] != "Monétaire"].copy()

    risky["score"] = risky["Rendement_attendu"] - lam * risky["Volatilite"] ** 2
    risky = risky.sort_values("score", ascending=False).head(nb_max_actifs)

    risky_weights = np.maximum(risky["score"], 0)
    if risky_weights.sum() == 0:
        risky_weights = np.ones(len(risky))
    risky_weights = risky_weights / risky_weights.sum()

    total_risky_weight = 1.0 - liquidite_min
    risky["Poids"] = risky_weights * total_risky_weight

    money_row = universe[universe["Classe"] == "Monétaire"].iloc[0].copy()
    money_weight = liquidite_min

    alloc_risky = risky[["Ticker", "Classe", "Poids"]].copy()
    alloc_cash = pd.DataFrame([{
        "Ticker": money_row["Ticker"],
        "Classe": money_row["Classe"],
        "Poids": money_weight,
    }])

    alloc = pd.concat([alloc_risky, alloc_cash], ignore_index=True)
    alloc["Montant (€)"] = alloc["Poids"] * montant

    merged = alloc.merge(universe, on=["Ticker", "Classe"])
    expected_return = float((merged["Poids"] * merged["Rendement_attendu"]).sum())
    volatility = float((merged["Poids"] * merged["Volatilite"]).sum())

    score = expected_return / (volatility + 1e-6)

    stats = {
        "expected_return": expected_return,
        "volatility": volatility,
        "score": score,
        "cash_amount": float(alloc[alloc["Classe"] == "Monétaire"]["Montant (€)"].sum()),
    }
    return alloc, stats


def compute_efficient_frontier(universe: pd.DataFrame, n_points: int = 30) -> pd.DataFrame:
    """
    Calcule une frontière efficiente DÉMO à partir des rendements/volatilités des actifs.
    On suppose une corrélation moyenne entre les actifs risqués.
    Résultat : DataFrame avec (Volatilite_portefeuille, Rendement_portefeuille).
    """
    risky = universe.copy().reset_index(drop=True)

    mu = risky["Rendement_attendu"].values  # rendements attendus
    sigma = risky["Volatilite"].values      # volatilités
    n = len(mu)

    # Matrice de corrélation simplifiée (démo) :
    rho = 0.2  # corrélation moyenne entre les actifs
    corr = np.full((n, n), rho)
    np.fill_diagonal(corr, 1.0)

    # Matrice de covariance : Σ = D * Corr * D
    cov = np.outer(sigma, sigma) * corr

    lam_values = np.linspace(0.5, 8.0, n_points)
    results = []

    for lam in lam_values:
        # Solution analytique démo : w ∝ Σ^{-1} μ / λ
        try:
            w_raw = np.linalg.solve(cov, mu / lam)
        except np.linalg.LinAlgError:
            continue

        # Pas de ventes à découvert dans la démo
        w_raw = np.maximum(w_raw, 0.0)

        if w_raw.sum() == 0:
            w = np.ones(n) / n
        else:
            w = w_raw / w_raw.sum()

        ret = float(np.dot(w, mu))
        vol = float(np.sqrt(w @ cov @ w))

        results.append({
            "Rendement_portefeuille": ret,
            "Volatilite_portefeuille": vol,
        })

    frontier = pd.DataFrame(results).sort_values("Volatilite_portefeuille")
    return frontier
