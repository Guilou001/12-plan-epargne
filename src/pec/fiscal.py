"""Le moteur fiscal simplifié des trois comptes : REER, CELI, non enregistré.

Toutes les règles sont des conventions déclarées, pas un barème réel :
- REER : la cotisation est déductible et se fait en dollars AVANT impôt ; la chaîne complète
  des remboursements d'impôt est réinvestie (le remboursement, puis le remboursement du
  remboursement, etc.), ce qui équivaut à cotiser b/(1 - tau_actif) pour un budget après
  impôt b (convention du « grossing up ») ; le retrait est imposé au taux marginal de
  retraite. Si le remboursement était DÉPENSÉ plutôt que réinvesti, le classement des ordres
  s'inverserait : la convention porte le verdict, et c'est déclaré dans le README.
- CELI : cotisé après impôt, croissance et retraits libres d'impôt.
- Non enregistré : cotisé après impôt ; les gains sont réputés réalisés chaque année et imposés
  à l'inclusion de 50 % AU TAUX DE LA VIE ACTIVE, y compris pendant la décumulation
  (convention déclarée ; sans effet sur les chiffres publiés, le compte restant vide au cas
  type), les pertes créditées immédiatement (simplification déclarée, prudente pour les
  gains, généreuse pour les pertes).

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
    remboursement_reinvesti: bool = True   # False : le remboursement d'impôt REER est dépensé


ORDRES = ("reer_d_abord", "celi_d_abord", "moitie_moitie")


def taux_net_ni(r: float | np.ndarray, f: Fiscalite) -> float | np.ndarray:
    """Le rendement après l'impôt annuel du compte non enregistré."""
    return r * (1.0 - f.tau_actif * f.inclusion_gain)


def cotiser(budget: float, ordre: str, f: Fiscalite) -> tuple[float, float, float]:
    """Répartit un budget APRÈS IMPÔT d'une année entre REER (brut), CELI et non enregistré."""
    if ordre not in ORDRES:
        raise ValueError(f"ordre inconnu : {ordre}")
    # remboursement réinvesti : un budget après impôt b achète b/(1-t) de cotisation brute ;
    # remboursement dépensé : il n'achète que b, et le REER perd l'essentiel de son avantage
    gross = 1.0 / (1.0 - f.tau_actif) if f.remboursement_reinvesti else 1.0
    cout_reer_plein = f.plafond_reer / gross                 # coût après impôt du REER plafonné
    reer_brut = celi = ni = 0.0
    if ordre == "reer_d_abord":
        b = min(budget, cout_reer_plein)
        reer_brut = b * gross
        reste = budget - b
        celi = min(reste, f.plafond_celi)
        ni = reste - celi
    elif ordre == "celi_d_abord":
        celi = min(budget, f.plafond_celi)
        reste = budget - celi
        b = min(reste, cout_reer_plein)
        reer_brut = b * gross
        ni = reste - b
    else:                                                   # moitie_moitie
        b = min(budget / 2.0, cout_reer_plein)
        reer_brut = b * gross
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
    """Le revenu net constant qui épuise exactement le patrimoine sur l'horizon, par bissection.

    Le premier retrait précède toute croissance : le revenu constant ne peut donc jamais
    dépasser la richesse nette initiale, qui sert de borne haute prouvée.
    """
    bas, haut = 0.0, richesse_nette(reer, celi, ni, f) + 1.0
    while haut - bas > tol:
        mid = (bas + haut) / 2.0
        annees, _ = decumuler(reer, celi, ni, rendements_annuels, mid, f)
        if annees == len(rendements_annuels):
            bas = mid
        else:
            haut = mid
    return bas
