"""Les rendements mensuels du portefeuille de politique du dépôt 03 (six FNB canadiens, yfinance).

Mêmes FNB et mêmes poids que 03-portfolio-ops-ca (déclaré) : XIU 25 %, XSP 20 %, XIN 15 %,
XRE 5 %, XBB 25 %, XSB 10 %, rééquilibrage mensuel. Yahoo Finance est en usage personnel ;
les données ne sont jamais commitées ; le biais de survie ne joue pas (FNB toujours cotés).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

RAW = Path("data/raw")

POLITIQUE = {"XIU.TO": 0.25, "XSP.TO": 0.20, "XIN.TO": 0.15,
             "XRE.TO": 0.05, "XBB.TO": 0.25, "XSB.TO": 0.10}


def fetch() -> None:
    """Télécharge les cours ajustés (dividendes réinvestis) des six FNB, tout l'historique."""
    import yfinance as yf

    RAW.mkdir(parents=True, exist_ok=True)
    px = yf.download(list(POLITIQUE), period="max", auto_adjust=True, progress=False)["Close"]
    px.to_csv(RAW / "prix_fnb.csv")


def load_portfolio_returns() -> pd.Series:
    """Les rendements mensuels du portefeuille de politique, sur l'échantillon commun des six FNB.

    Le dernier mois est retenu tel que téléchargé, même s'il est incomplet au jour du fetch
    (convention déclarée ; l'effet mesuré sur le composé 2002-2026 est de 0,04 point).
    """
    px = pd.read_csv(RAW / "prix_fnb.csv", index_col=0, parse_dates=True)
    monthly = px.resample("ME").last()
    rets = monthly.pct_change()
    rets = rets.dropna(how="any")                    # échantillon commun : le plus jeune FNB borne le début
    w = pd.Series(POLITIQUE)
    port = (rets[w.index] * w).sum(axis=1)
    port.name = "rendement_politique"
    return port
