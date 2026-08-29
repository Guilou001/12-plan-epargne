"""Le Monte Carlo : bootstrap de blocs d'un an sur les rendements mensuels du portefeuille.

Chaque année simulée est le produit de 12 rendements mensuels CONSÉCUTIFS tirés à une date de
départ aléatoire de l'échantillon : les enchaînements intra-année (2008, 2020, 2022) sont
préservés, les années sont indépendantes entre elles (convention déclarée). Les 10 000
trajectoires sont traitées en vectoriel ; le moteur scalaire de fiscal.py, testé contre les
équivalences analytiques, sert de référence (le test d'accord vectoriel/scalaire est dans pytest).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from pec.fiscal import ORDRES, Fiscalite, accumuler, cotiser, decumuler, richesse_nette, taux_net_ni


def annees_bootstrap(mensuels: np.ndarray, n_annees: int, n_traj: int,
                     rng: np.random.Generator) -> np.ndarray:
    """Une matrice (n_traj, n_annees) de rendements annuels par blocs de 12 mois consécutifs."""
    n = len(mensuels)
    if n < 24:
        raise ValueError("échantillon mensuel trop court pour un bootstrap de blocs d'un an")
    starts = rng.integers(0, n - 12 + 1, size=(n_traj, n_annees))
    idx = starts[..., None] + np.arange(12)
    return np.prod(1.0 + mensuels[idx], axis=-1) - 1.0


def rendement_deterministe(mensuels: np.ndarray) -> float:
    """Le rendement annuel composé moyen de l'échantillon : l'hypothèse du plan « sur papier »."""
    return float((1.0 + mensuels).prod() ** (12.0 / len(mensuels)) - 1.0)


def accumuler_vec(acc: np.ndarray, budget: float, ordre: str, f: Fiscalite) -> tuple[np.ndarray, ...]:
    """L'accumulation sur toutes les trajectoires à la fois ; mêmes conventions que fiscal.accumuler."""
    n_traj, n_annees = acc.shape
    reer = np.zeros(n_traj)
    celi = np.zeros(n_traj)
    ni = np.zeros(n_traj)
    d_reer, d_celi, d_ni = cotiser(budget, ordre, f)      # budget constant : mêmes dépôts chaque année
    for a in range(n_annees):
        r = acc[:, a]
        reer = (reer + d_reer) * (1.0 + r)
        celi = (celi + d_celi) * (1.0 + r)
        ni = (ni + d_ni) * (1.0 + taux_net_ni(r, f))
    return reer, celi, ni


def decumuler_vec(reer0: np.ndarray, celi0: np.ndarray, ni0: np.ndarray, ret: np.ndarray,
                  cible: np.ndarray | float, f: Fiscalite) -> tuple[np.ndarray, np.ndarray]:
    """La décumulation vectorisée (retrait début d'année, ordre NI -> REER -> CELI) ;
    retourne (années financées, legs net, 0 si ruine)."""
    n_traj, n_annees = ret.shape
    reer, celi, ni = reer0.copy(), celi0.copy(), ni0.copy()
    cible = np.broadcast_to(np.asarray(cible, dtype=float), (n_traj,)).copy()
    annees = np.zeros(n_traj, dtype=int)
    vivant = np.ones(n_traj, dtype=bool)
    for a in range(n_annees):
        besoin = np.where(vivant, cible, 0.0)
        pris = np.minimum(ni, besoin)
        ni -= pris
        besoin -= pris
        brut = np.minimum(reer, besoin / (1.0 - f.tau_retraite))
        reer -= brut
        besoin -= brut * (1.0 - f.tau_retraite)
        pris = np.minimum(celi, besoin)
        celi -= pris
        besoin -= pris
        rate = vivant & (besoin > 1e-9)
        vivant = vivant & ~rate
        annees += vivant.astype(int)                       # l'année n'est comptée que si financée
        r = ret[:, a]
        reer *= 1.0 + r
        celi *= 1.0 + r
        ni *= 1.0 + taux_net_ni(r, f)
    legs = np.where(vivant, celi + ni + reer * (1.0 - f.tau_retraite), 0.0)
    return annees, legs


def revenu_soutenable_vec(reer: np.ndarray, celi: np.ndarray, ni: np.ndarray, ret: np.ndarray,
                          f: Fiscalite, n_iter: int = 40) -> np.ndarray:
    """Le revenu net constant qui épuise exactement chaque trajectoire, par bissection vectorielle.

    Borne haute prouvée : la richesse nette initiale, car le premier retrait précède toute
    croissance (l'ancienne borne en richesse/horizon plafonnait quelques trajectoires extrêmes).
    """
    n_annees = ret.shape[1]
    bas = np.zeros(len(reer))
    haut = richesse_nette(reer, celi, ni, f) + 1.0
    for _ in range(n_iter):
        mid = (bas + haut) / 2.0
        annees, _ = decumuler_vec(reer, celi, ni, ret, mid, f)
        ok = annees == n_annees
        bas = np.where(ok, mid, bas)
        haut = np.where(ok, haut, mid)
    return bas


def run_monte_carlo(mensuels: np.ndarray, f: Fiscalite, budget: float,
                    annees_acc: int, annees_ret: int, cible_nette: float,
                    n_traj: int = 10_000, seed: int = 0) -> pd.DataFrame:
    """Toutes les trajectoires pour les trois ordres de remplissage ; une ligne par trajectoire.

    Les mêmes tirages de rendements servent aux trois ordres : la comparaison est appariée.
    """
    rng = np.random.default_rng(seed)
    acc = annees_bootstrap(mensuels, annees_acc, n_traj, rng)
    ret = annees_bootstrap(mensuels, annees_ret, n_traj, rng)
    frames = []
    for ordre in ORDRES:
        reer, celi, ni = accumuler_vec(acc, budget, ordre, f)
        annees, legs = decumuler_vec(reer, celi, ni, ret, cible_nette, f)
        frames.append(pd.DataFrame({
            "ordre": ordre, "traj": np.arange(n_traj),
            "richesse_brute": reer + celi + ni,
            "richesse_nette": richesse_nette(reer, celi, ni, f),
            "annees_financees": annees, "succes": annees == annees_ret,
            "legs": legs,
            "revenu_soutenable": revenu_soutenable_vec(reer, celi, ni, ret, f),
        }))
    return pd.concat(frames, ignore_index=True)


def plan_deterministe(mensuels: np.ndarray, f: Fiscalite, budget: float,
                      annees_acc: int, annees_ret: int, ordre: str) -> dict[str, float]:
    """Le même plan à rendement constant : ce que promet la moyenne quand on oublie le hasard."""
    from pec.fiscal import revenu_soutenable

    r = rendement_deterministe(mensuels)
    reer, celi, ni = accumuler(np.full(annees_acc, r), budget, ordre, f)
    return {"rendement_constant": r,
            "richesse_brute": reer + celi + ni,
            "richesse_nette": richesse_nette(reer, celi, ni, f),
            "revenu_promis": revenu_soutenable(reer, celi, ni, np.full(annees_ret, r), f)}


def fan_richesse(mensuels: np.ndarray, f: Fiscalite, budget: float, annees_acc: int,
                 ordre: str, n_traj: int = 10_000, seed: int = 0) -> pd.DataFrame:
    """Les percentiles 5/25/50/75/95 de la richesse brute année par année (pour l'éventail)."""
    rng = np.random.default_rng(seed)
    annees = annees_bootstrap(mensuels, annees_acc, n_traj, rng)
    reer = np.zeros(n_traj)
    celi = np.zeros(n_traj)
    ni = np.zeros(n_traj)
    d_reer, d_celi, d_ni = cotiser(budget, ordre, f)
    out = []
    for a in range(annees_acc):
        r = annees[:, a]
        reer = (reer + d_reer) * (1.0 + r)
        celi = (celi + d_celi) * (1.0 + r)
        ni = (ni + d_ni) * (1.0 + taux_net_ni(r, f))
        total = reer + celi + ni
        out.append({"annee": a + 1,
                    **{f"p{p}": float(np.percentile(total, p)) for p in (5, 25, 50, 75, 95)}})
    return pd.DataFrame(out)


def carte_des_ordres(mensuels: np.ndarray, budget: float, annees_acc: int,
                     taux_actifs: np.ndarray, taux_retraites: np.ndarray) -> pd.DataFrame:
    """À rendement constant, l'avantage du REER d'abord sur le CELI d'abord (en % de richesse
    nette), pour une grille de taux : la carte qui dit à qui le REER profite."""
    r = rendement_deterministe(mensuels)
    acc = np.full(annees_acc, r)
    rows = []
    for ta in taux_actifs:
        for tr in taux_retraites:
            f = Fiscalite(tau_actif=float(ta), tau_retraite=float(tr))
            w = {}
            for ordre in ("reer_d_abord", "celi_d_abord"):
                reer, celi, ni = accumuler(acc, budget, ordre, f)
                w[ordre] = richesse_nette(reer, celi, ni, f)
            rows.append({"tau_actif": float(ta), "tau_retraite": float(tr),
                         "avantage_reer_pct": 100.0 * (w["reer_d_abord"] / w["celi_d_abord"] - 1.0)})
    return pd.DataFrame(rows)


def _verifie_scalaire_vectoriel(mensuels: np.ndarray, f: Fiscalite, budget: float) -> float:
    """L'écart max entre les moteurs scalaire et vectoriel sur 50 trajectoires (utilisé par pytest)."""
    rng = np.random.default_rng(7)
    acc = annees_bootstrap(mensuels, 10, 50, rng)
    ret = annees_bootstrap(mensuels, 8, 50, rng)
    reer_v, celi_v, ni_v = accumuler_vec(acc, budget, "celi_d_abord", f)
    annees_v, legs_v = decumuler_vec(reer_v, celi_v, ni_v, ret, 30_000.0, f)
    worst = 0.0
    for i in range(50):
        reer_s, celi_s, ni_s = accumuler(acc[i], budget, "celi_d_abord", f)
        annees_s, legs_s = decumuler(reer_s, celi_s, ni_s, ret[i], 30_000.0, f)
        worst = max(worst, abs(reer_s - reer_v[i]), abs(celi_s - celi_v[i]), abs(ni_s - ni_v[i]),
                    abs(legs_s - legs_v[i]), float(annees_s != annees_v[i]))
    return worst
