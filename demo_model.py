
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

    expected_return = float(
        (alloc.merge(universe, on=["Ticker", "Classe"])[["Poids", "Rendement_attendu"]]
         .prod(axis=1)
         .sum())
    )
    volatility = float(
        (alloc.merge(universe, on=["Ticker", "Classe"])[["Poids", "Volatilite"]]
         .prod(axis=1)
         .sum())
    )

    score = expected_return / (volatility + 1e-6)

    stats = {
        "expected_return": expected_return,
        "volatility": volatility,
        "score": score,
        "cash_amount": float(alloc[alloc["Classe"] == "Monétaire"]["Montant (€)"].sum()),
    }
    return alloc, stats
