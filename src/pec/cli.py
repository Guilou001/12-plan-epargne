"""Ligne de commande : télécharger les FNB, simuler le plan, produire tables et figures.

Le cas type est un précepte déclaré, pas un barème réel : 10 000 $ d'épargne annuelle après
impôt pendant 30 ans, 25 ans de retraite, cible de 30 000 $ nets par an HORS RRQ et PSV,
taux marginal de 35 % pendant la vie active et de 25 % à la retraite (chiffres ronds à
remplacer par les vôtres ; la carte des taux couvre les autres cas).
"""

from __future__ import annotations

from pathlib import Path

import typer

app = typer.Typer(help="Plan d'épargne REER/CELI/non enregistré : Monte Carlo par bootstrap "
                       "sur le portefeuille de politique du dépôt 03, trois ordres de "
                       "remplissage, verdict en probabilité d'atteinte.")

BUDGET = 10_000.0
ANNEES_ACC = 30
ANNEES_RET = 25
CIBLE = 30_000.0
TAU_ACTIF = 0.35
TAU_RETRAITE = 0.25


@app.callback()
def main() -> None:
    """Sous-commandes nommées."""


@app.command()
def fetch() -> None:
    """Les cours ajustés des six FNB de la politique du dépôt 03 (yfinance, usage personnel)."""
    from pec import data

    data.fetch()
    port = data.load_portfolio_returns()
    typer.echo(f"portefeuille de politique : {len(port)} mois, "
               f"{port.index[0]:%Y-%m} -> {port.index[-1]:%Y-%m}")


@app.command()
def simulate(out: Path = Path("results"), n_traj: int = 10_000, seed: int = 0) -> None:
    """Le Monte Carlo complet : trois ordres, plan déterministe, éventail, carte des taux."""
    import numpy as np
    import pandas as pd

    from pec import data, figures, simulate
    from pec.fiscal import Fiscalite

    mensuels = data.load_portfolio_returns().to_numpy()
    f = Fiscalite(tau_actif=TAU_ACTIF, tau_retraite=TAU_RETRAITE)
    tables, figs = out / "tables", out / "figures"
    tables.mkdir(parents=True, exist_ok=True)
    figs.mkdir(parents=True, exist_ok=True)

    mc = simulate.run_monte_carlo(mensuels, f, BUDGET, ANNEES_ACC, ANNEES_RET, CIBLE,
                                  n_traj=n_traj, seed=seed)
    resume = (mc.groupby("ordre")
              .agg(p_succes=("succes", "mean"),
                   richesse_nette_mediane=("richesse_nette", "median"),
                   revenu_soutenable_med=("revenu_soutenable", "median"),
                   revenu_soutenable_p5=("revenu_soutenable", lambda s: float(np.percentile(s, 5))),
                   legs_median=("legs", "median"))
              .reset_index())
    det = simulate.plan_deterministe(mensuels, f, BUDGET, ANNEES_ACC, ANNEES_RET, "reer_d_abord")
    resume.round(4).to_csv(tables / "resume_ordres.csv", index=False)
    pd.DataFrame([det]).round(4).to_csv(tables / "plan_deterministe.csv", index=False)
    mc.drop(columns="traj").round(2).to_csv(tables / "monte_carlo.csv", index=False)

    fan = simulate.fan_richesse(mensuels, f, BUDGET, ANNEES_ACC, "reer_d_abord",
                                n_traj=n_traj, seed=seed)
    fan.round(0).to_csv(tables / "eventail_richesse.csv", index=False)
    # la trajectoire « sur papier » : le même plan à rendement constant, année par année
    from pec.fiscal import cotiser, taux_net_ni

    r = simulate.rendement_deterministe(mensuels)
    d_reer, d_celi, d_ni = cotiser(BUDGET, "reer_d_abord", f)
    reer = celi = ni = 0.0
    promesse = []
    for _ in range(ANNEES_ACC):
        reer = (reer + d_reer) * (1.0 + r)
        celi = (celi + d_celi) * (1.0 + r)
        ni = (ni + d_ni) * (1.0 + float(taux_net_ni(r, f)))
        promesse.append(reer + celi + ni)
    promesse = pd.Series(promesse, index=fan["annee"])

    grille_a = np.arange(0.25, 0.51, 0.05)
    grille_r = np.arange(0.15, 0.46, 0.05)
    carte = simulate.carte_des_ordres(mensuels, BUDGET, ANNEES_ACC, grille_a, grille_r)
    carte.round(3).to_csv(tables / "carte_des_ordres.csv", index=False)

    # le scénario prudent déclaré : les mêmes tirages, amputés de 2 points par année
    prudent = mensuels - 0.02 / 12.0
    mc_p = simulate.run_monte_carlo(prudent, f, BUDGET, ANNEES_ACC, ANNEES_RET, CIBLE,
                                    n_traj=n_traj, seed=seed)
    det_p = simulate.plan_deterministe(prudent, f, BUDGET, ANNEES_ACC, ANNEES_RET, "reer_d_abord")
    resume_p = (mc_p.groupby("ordre")
                .agg(p_succes=("succes", "mean"),
                     revenu_soutenable_med=("revenu_soutenable", "median"),
                     revenu_soutenable_p5=("revenu_soutenable", lambda s: float(np.percentile(s, 5))))
                .reset_index())
    resume_p.round(4).to_csv(tables / "resume_ordres_prudent.csv", index=False)
    pd.DataFrame([det_p]).round(4).to_csv(tables / "plan_deterministe_prudent.csv", index=False)

    # ce que coûtent les trois conventions les plus lourdes, chacune REJOUÉE ici plutôt que
    # discutée : l'absence d'indexation, la date du remboursement d'impôt, le plafond REER
    from pec.fiscal import Fiscalite

    sens = []
    for nom, kwargs, f_var in [
        ("référence (dollars courants, remboursement réinvesti la même année)", {}, f),
        ("cible et cotisations indexées à 2 % par an", {"inflation": 0.02}, f),
        ("remboursement d'impôt dépensé au lieu d'être réinvesti", {},
         Fiscalite(tau_actif=TAU_ACTIF, tau_retraite=TAU_RETRAITE, remboursement_reinvesti=False)),
        ("droits REER d'un revenu de 150 000 $ (27 000 $ au lieu de 12 960 $)", {},
         Fiscalite(tau_actif=TAU_ACTIF, tau_retraite=TAU_RETRAITE, plafond_reer=27_000.0)),
    ]:
        m = simulate.run_monte_carlo(mensuels, f_var, BUDGET, ANNEES_ACC, ANNEES_RET, CIBLE,
                                     n_traj=n_traj, seed=seed, **kwargs)
        r_ = m[m["ordre"] == "reer_d_abord"]
        c_ = m[m["ordre"] == "celi_d_abord"]
        sens.append({"variante": nom,
                     "p_succes_reer_d_abord": float(r_["succes"].mean()),
                     "richesse_nette_mediane_reer": float(r_["richesse_nette"].median()),
                     "avantage_reer_sur_celi_pct": 100.0 * (float(r_["richesse_nette"].median())
                                                            / float(c_["richesse_nette"].median()) - 1.0)})
    pd.DataFrame(sens).round(4).to_csv(tables / "sensibilites.csv", index=False)

    figures.fig_fan(fan, promesse, figs / "eventail_richesse.png")
    figures.fig_revenu(mc, det["revenu_promis"], CIBLE, figs / "revenu_soutenable.png")
    figures.fig_carte(carte, (TAU_ACTIF, TAU_RETRAITE), figs / "carte_des_ordres.png")

    typer.echo(f"rendement constant du plan sur papier : {100 * det['rendement_constant']:.2f} %/an ; "
               f"revenu promis {det['revenu_promis']:,.0f} $".replace(",", " "))
    typer.echo(resume.round(3).to_string(index=False))
    typer.echo("sensibilité aux conventions :")
    typer.echo(pd.DataFrame(sens).round(3).to_string(index=False))


if __name__ == "__main__":
    app()
