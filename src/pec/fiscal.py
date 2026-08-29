"""Le moteur fiscal simplifié des trois comptes : REER, CELI, non enregistré.

Toutes les règles sont des conventions déclarées, pas un barème réel :
- REER : la cotisation est déductible ; le remboursement d'impôt est réinvesti immédiatement
  dans le REER (convention du « grossing up » : un budget après impôt b achète b/(1 - tau_actif)
  de cotisation brute) ; le retrait est imposé au taux marginal de retraite.
- CELI : cotisé après impôt, croissance et retraits libres d'impôt.
- Non enregistré : cotisé après impôt ; les gains sont réputés réalisés chaque année et imposés
  à l'inclusion de 50 %, les pertes créditées immédiatement (simplification déclarée, prudente
  pour les gains, généreuse pour les pertes).

La vérité analytique qui sert de test : à taux marginaux égaux et sans plafond, REER et CELI
produisent EXACTEMENT la même richesse finale ; le REER ne gagne que si le taux de retraite est
plus bas que le taux de la vie active, d'un facteur (1 - tau_ret)/(1 - tau_actif).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Fiscalite:
    tau_actif: float                  # taux marginal pendant la vie active (précepte, à choisir)
    tau_retraite: float               # taux marginal à la retraite
    inclusion_gain: float = 0.5       # inclusion des gains en capital (rapporté, règle générale)
    plafond_celi: float = 7_000.0     # droits annuels 2026 (rapporté)
    plafond_reer: float = 12_960.0    # 18 % d'un revenu de 72 000 $ (cas type, précepte)


ORDRES = ("reer_d_abord", "celi_d_abord", "moitie_moitie")


def taux_net_ni(r: float | np.ndarray, f: Fiscalite) -> float | np.ndarray:
    """Le rendement après l'impôt annuel du compte non enregistré."""
    return r * (1.0 - f.tau_actif * f.inclusion_gain)


def cotiser(budget: float, ordre: str, f: Fiscalite) -> tuple[float, float, float]:
    """Répartit un budget APRÈS IMPÔT d'une année entre REER (brut), CELI et non enregistré."""
    if ordre not in ORDRES:
        raise ValueError(f"ordre inconnu : {ordre}")
    cout_reer_plein = f.plafond_reer * (1.0 - f.tau_actif)   # coût après impôt du REER plafonné
    reer_brut = celi = ni = 0.0
    if ordre == "reer_d_abord":
        b = min(budget, cout_reer_plein)
        reer_brut = b / (1.0 - f.tau_actif)
        reste = budget - b
        celi = min(reste, f.plafond_celi)
        ni = reste - celi
    elif ordre == "celi_d_abord":
        celi = min(budget, f.plafond_celi)
        reste = budget - celi
        b = min(reste, cout_reer_plein)
        reer_brut = b / (1.0 - f.tau_actif)
        ni = reste - b
    else:                                                   # moitie_moitie
        b = min(budget / 2.0, cout_reer_plein)
        reer_brut = b / (1.0 - f.tau_actif)
        celi = min(budget / 2.0, f.plafond_celi)
        ni = budget - b - celi
    return reer_brut, celi, ni


def accumuler(rendements_annuels: np.ndarray, budget: float, ordre: str,
              f: Fiscalite) -> tuple[float, float, float]:
    """Cotise en début d'année puis capitalise ; retourne (reer brut, celi, non enregistré)."""
    reer = celi = ni = 0.0
    for r in rendements_annuels:
        d_reer, d_celi, d_ni = cotiser(budget, ordre, f)
        reer = (reer + d_reer) * (1.0 + r)
        celi = (celi + d_celi) * (1.0 + r)
        ni = (ni + d_ni) * (1.0 + float(taux_net_ni(r, f)))
    return reer, celi, ni


def decumuler(reer: float, celi: float, ni: float, rendements_annuels: np.ndarray,
              cible_nette: float, f: Fiscalite) -> tuple[int, float]:
    """Retire `cible_nette` après impôt en début de chaque année, dans l'ordre déclaré
    non enregistré -> REER -> CELI ; retourne (années financées, legs final après impôt)."""
    for k, r in enumerate(rendements_annuels):
        besoin = cible_nette
        pris = min(ni, besoin)
        ni -= pris
        besoin -= pris
        if besoin > 0:
            brut = besoin / (1.0 - f.tau_retraite)
            pris_brut = min(reer, brut)
            reer -= pris_brut
            besoin -= pris_brut * (1.0 - f.tau_retraite)
        if besoin > 0:
            pris = min(celi, besoin)
            celi -= pris
            besoin -= pris
        if besoin > 1e-9:
            return k, 0.0
        reer *= 1.0 + r
        celi *= 1.0 + r
        ni *= 1.0 + float(taux_net_ni(r, f))
    legs = celi + ni + reer * (1.0 - f.tau_retraite)
    return len(rendements_annuels), legs


def richesse_nette(reer: float, celi: float, ni: float, f: Fiscalite) -> float:
    """La valeur après impôt du patrimoine : le REER vaut sa part nette du taux de retraite."""
    return celi + ni + reer * (1.0 - f.tau_retraite)


def revenu_soutenable(reer: float, celi: float, ni: float, rendements_annuels: np.ndarray,
                      f: Fiscalite, tol: float = 1.0) -> float:
    """Le revenu net constant qui épuise exactement le patrimoine sur l'horizon, par bissection."""
    bas, haut = 0.0, richesse_nette(reer, celi, ni, f) * 2.0 / max(len(rendements_annuels), 1) + 1e5
    while haut - bas > tol:
        mid = (bas + haut) / 2.0
        annees, _ = decumuler(reer, celi, ni, rendements_annuels, mid, f)
        if annees == len(rendements_annuels):
            bas = mid
        else:
            haut = mid
    return bas
