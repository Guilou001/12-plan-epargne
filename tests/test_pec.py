"""Les vérités analytiques du plan d'épargne : équivalences fiscales exactes, moteurs concordants."""

import numpy as np
import pytest

from pec.fiscal import (
    Fiscalite,
    accumuler,
    cotiser,
    decumuler,
    revenu_soutenable,
    richesse_nette,
    taux_net_ni,
)
from pec.simulate import (
    _verifie_scalaire_vectoriel,
    annees_bootstrap,
    carte_des_ordres,
    rendement_deterministe,
)

SANS_PLAFOND = dict(plafond_celi=1e12, plafond_reer=1e12)


def test_reer_egale_celi_quand_les_taux_sont_egaux():
    # LA vérité analytique : b/(1-t) * (1+r)^N * (1-t) = b * (1+r)^N, exactement
    f = Fiscalite(tau_actif=0.40, tau_retraite=0.40, **SANS_PLAFOND)
    r = np.full(30, 0.05)
    reer, _, _ = accumuler(r, 10_000.0, "reer_d_abord", f)
    _, celi, _ = accumuler(r, 10_000.0, "celi_d_abord", f)
    assert richesse_nette(reer, 0.0, 0.0, f) == pytest.approx(celi, rel=1e-12)


def test_avantage_reer_egale_le_rapport_des_taux():
    # à taux différents, le facteur exact est (1 - tau_ret)/(1 - tau_actif)
    f = Fiscalite(tau_actif=0.40, tau_retraite=0.25, **SANS_PLAFOND)
    r = np.full(20, 0.06)
    reer, _, _ = accumuler(r, 8_000.0, "reer_d_abord", f)
    _, celi, _ = accumuler(r, 8_000.0, "celi_d_abord", f)
    assert richesse_nette(reer, 0.0, 0.0, f) / celi == pytest.approx((1 - 0.25) / (1 - 0.40), rel=1e-12)


def test_non_enregistre_perd_toujours_contre_celi():
    f = Fiscalite(tau_actif=0.35, tau_retraite=0.35, plafond_celi=0.0, plafond_reer=0.0)
    r = np.full(25, 0.05)
    _, _, ni = accumuler(r, 5_000.0, "celi_d_abord", f)      # tout déborde en non enregistré
    f2 = Fiscalite(tau_actif=0.35, tau_retraite=0.35, **SANS_PLAFOND)
    _, celi, _ = accumuler(r, 5_000.0, "celi_d_abord", f2)
    assert ni < celi                                          # le frottement fiscal annuel coûte


def test_cotiser_respecte_les_plafonds():
    f = Fiscalite(tau_actif=0.40, tau_retraite=0.25)          # plafonds par défaut : 7 000 et 12 960
    reer_brut, celi, ni = cotiser(30_000.0, "celi_d_abord", f)
    assert celi == pytest.approx(7_000.0)
    assert reer_brut == pytest.approx(12_960.0)               # plafonné en brut
    assert ni == pytest.approx(30_000.0 - 7_000.0 - 12_960.0 * 0.60)
    assert reer_brut * (1 - f.tau_actif) + celi + ni == pytest.approx(30_000.0)


def test_decumulation_a_rendement_nul_forme_fermee():
    # 25 ans à 30 000 $ nets depuis un CELI : il faut exactement 750 000 $
    f = Fiscalite(tau_actif=0.35, tau_retraite=0.25)
    zeros = np.zeros(25)
    annees, legs = decumuler(0.0, 750_000.0, 0.0, zeros, 30_000.0, f)
    assert annees == 25 and legs == pytest.approx(0.0, abs=1e-6)
    annees, _ = decumuler(0.0, 749_999.0, 0.0, zeros, 30_000.0, f)
    assert annees == 24
    # depuis un REER, il faut le brut : 750 000 / (1 - 0,25) = 1 000 000
    annees, legs = decumuler(1_000_000.0, 0.0, 0.0, zeros, 30_000.0, f)
    assert annees == 25 and legs == pytest.approx(0.0, abs=1e-6)


def test_revenu_soutenable_retrouve_la_forme_fermee():
    f = Fiscalite(tau_actif=0.35, tau_retraite=0.25)
    rev = revenu_soutenable(0.0, 750_000.0, 0.0, np.zeros(25), f)
    assert rev == pytest.approx(30_000.0, abs=2.0)
    # rendement constant non nul : annuité due, C = W (1 - v) / (1 - v^M), v = 1/(1+r)
    r, w, m = 0.12, 5_000_000.0, 25
    v = 1.0 / (1.0 + r)
    attendu = w * (1.0 - v) / (1.0 - v**m)
    assert revenu_soutenable(0.0, w, 0.0, np.full(m, r), f) == pytest.approx(attendu, abs=2.0)


def test_remboursement_depense_renverse_le_classement():
    # la convention porte le verdict : remboursement dépensé, le REER perd son avantage
    from pec.fiscal import richesse_nette

    r = np.full(30, 0.05)
    f = Fiscalite(tau_actif=0.35, tau_retraite=0.25, remboursement_reinvesti=False)
    w = {}
    for ordre in ("reer_d_abord", "celi_d_abord"):
        reer, celi, ni = accumuler(r, 10_000.0, ordre, f)
        w[ordre] = richesse_nette(reer, celi, ni, f)
    assert w["celi_d_abord"] > w["reer_d_abord"]


def test_bootstrap_reproductible_et_calibre():
    rng = np.random.default_rng(3)
    mensuels = rng.normal(0.005, 0.03, 240)
    a1 = annees_bootstrap(mensuels, 10, 500, np.random.default_rng(1))
    a2 = annees_bootstrap(mensuels, 10, 500, np.random.default_rng(1))
    assert np.array_equal(a1, a2)                             # même graine, mêmes tirages
    r_det = rendement_deterministe(mensuels)
    assert a1.mean() == pytest.approx(r_det, abs=0.02)        # le bootstrap recentre l'échantillon


def test_moteur_vectoriel_egale_le_scalaire():
    rng = np.random.default_rng(3)
    mensuels = rng.normal(0.005, 0.03, 240)
    f = Fiscalite(tau_actif=0.35, tau_retraite=0.25)
    assert _verifie_scalaire_vectoriel(mensuels, f, 10_000.0) < 1e-8


def test_carte_neutre_sur_la_diagonale():
    rng = np.random.default_rng(3)
    mensuels = rng.normal(0.005, 0.03, 240)
    carte = carte_des_ordres(mensuels, 10_000.0, 20,
                             np.array([0.30, 0.40]), np.array([0.30, 0.40]))
    diag = carte[(carte["tau_actif"] == carte["tau_retraite"])]["avantage_reer_pct"]
    hors = carte[(carte["tau_actif"] == 0.40) & (carte["tau_retraite"] == 0.30)]["avantage_reer_pct"]
    assert diag.abs().max() < 0.7        # quasi nul : seuls les plafonds cassent l'équivalence exacte
    assert float(hors.iloc[0]) > 2.0     # taux qui baisse à la retraite : le REER gagne nettement


def test_taux_net_ni_symetrique():
    f = Fiscalite(tau_actif=0.40, tau_retraite=0.25)
    assert taux_net_ni(0.10, f) == pytest.approx(0.08)        # gain imposé à 40 % x 50 %
    assert taux_net_ni(-0.10, f) == pytest.approx(-0.08)      # perte créditée (déclaré)
