"""Trois figures : l'éventail de la richesse, le revenu soutenable par ordre, la carte des taux."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

OKABE_ITO = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#56B4E9", "#F0E442", "#000000"]

LABELS = {"reer_d_abord": "REER d'abord", "celi_d_abord": "CELI d'abord", "moitie_moitie": "Moitié-moitié"}


def use_style():
    import matplotlib as mpl
    from cycler import cycler
    from matplotlib.ticker import FuncFormatter

    mpl.rcParams.update({
        "figure.dpi": 200, "savefig.dpi": 200, "figure.constrained_layout.use": True,
        "font.size": 11, "axes.titlesize": 12, "axes.prop_cycle": cycler(color=OKABE_ITO),
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.alpha": 0.3, "grid.linewidth": 0.5,
        "legend.frameon": False, "lines.linewidth": 1.8,
    })
    return FuncFormatter(lambda v, _: f"{v:g}".replace(".", ","))


def _milliers(v: float) -> str:
    return f"{v:,.0f}".replace(",", " ")


def fig_fan(fan: pd.DataFrame, promesse: pd.Series | None, dest: Path) -> None:
    """L'éventail de la richesse accumulée : la moitié des avenirs vit entre p25 et p75."""
    use_style()
    from matplotlib.ticker import FuncFormatter

    fig, ax = plt.subplots(figsize=(8.8, 4.6))
    x = fan["annee"]
    ax.fill_between(x, fan["p5"], fan["p95"], color=OKABE_ITO[0], alpha=0.15,
                    label="90 % des trajectoires (p5 à p95)")
    ax.fill_between(x, fan["p25"], fan["p75"], color=OKABE_ITO[0], alpha=0.35,
                    label="La moitié centrale (p25 à p75)")
    ax.plot(x, fan["p50"], color=OKABE_ITO[0], label=f"Médiane ({_milliers(fan['p50'].iloc[-1])} $)")
    if promesse is not None:
        ax.plot(promesse.index, promesse.to_numpy(), color=OKABE_ITO[3], linestyle="--",
                label=f"Plan à rendement constant ({_milliers(float(promesse.iloc[-1]))} $)")
    ax.set_xlabel("Années d'épargne")
    ax.set_ylabel("Richesse accumulée ($, brute : REER avant impôt)")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: _milliers(v)))
    ax.legend(fontsize=9, loc="upper left")
    ax.set_title("Le même plan, dix mille avenirs : l'éventail s'ouvre avec les années")
    fig.savefig(dest)
    plt.close(fig)


def fig_revenu(mc: pd.DataFrame, promis: float, cible: float, dest: Path) -> None:
    """Le revenu net soutenable : sa distribution par ordre, contre la promesse déterministe."""
    fr = use_style()
    from matplotlib.ticker import FuncFormatter

    fig, ax = plt.subplots(figsize=(8.8, 4.6))
    for ordre, color in zip(mc["ordre"].unique(), OKABE_ITO, strict=False):
        rev = np.sort(mc.loc[mc["ordre"] == ordre, "revenu_soutenable"].to_numpy())
        surv = 1.0 - np.arange(len(rev)) / len(rev)
        med = float(np.median(rev))
        ax.plot(rev, surv, color=color, label=f"{LABELS.get(ordre, ordre)} (médiane {_milliers(med)} $)")
    ax.axvline(promis, color="0.3", linestyle="--", linewidth=1.2)
    ax.text(promis + 2000, 1.02, f"promesse du plan constant ({_milliers(promis)} $)",
            fontsize=8.5, ha="left", color="0.3")
    ax.axvline(cible, color=OKABE_ITO[4], linestyle=":", linewidth=1.2)
    ax.text(cible - 2000, 1.02, f"cible ({_milliers(cible)} $)", fontsize=8.5, ha="right",
            color=OKABE_ITO[4])
    ax.set_xlabel("Revenu net soutenable pendant la retraite ($/an)")
    ax.set_ylabel("Part des trajectoires qui atteignent au moins ce revenu")
    ax.yaxis.set_major_formatter(fr)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: _milliers(v)))
    ax.set_ylim(0, 1.08)
    ax.legend(fontsize=9, loc="lower left")
    ax.set_title("Ce que la moyenne promet, la moitié des avenirs ne le livre pas")
    fig.savefig(dest)
    plt.close(fig)


def fig_carte(carte: pd.DataFrame, cas_type: tuple[float, float], dest: Path) -> None:
    """La carte des taux : le REER d'abord gagne sous la diagonale, perd au-dessus."""
    fr = use_style()
    fig, ax = plt.subplots(figsize=(7.6, 5.2))
    piv = carte.pivot(index="tau_retraite", columns="tau_actif", values="avantage_reer_pct")
    vmax = float(np.abs(piv.to_numpy()).max())
    im = ax.pcolormesh(piv.columns * 100, piv.index * 100, piv.to_numpy(),
                       cmap="RdBu_r", vmin=-vmax, vmax=vmax, shading="nearest")
    for (tr, ta), v in piv.stack().items():
        ax.text(ta * 100, tr * 100, f"{v:+.0f}".replace(".", ","), ha="center", va="center",
                fontsize=8.5, color="black")
    ax.plot([piv.columns.min() * 100, piv.columns.max() * 100],
            [piv.columns.min() * 100, piv.columns.max() * 100], color="0.2", linewidth=1.0,
            linestyle="--")
    ax.scatter([cas_type[0] * 100 - 1.4], [cas_type[1] * 100 + 1.4], marker="*", s=180,
               color=OKABE_ITO[2], zorder=5, label="cas type")
    ax.set_xlabel("Taux marginal pendant la vie active (%)")
    ax.set_ylabel("Taux marginal à la retraite (%)")
    ax.xaxis.set_major_formatter(fr)
    ax.yaxis.set_major_formatter(fr)
    cb = fig.colorbar(im, ax=ax)
    cb.set_label("Avantage du REER d'abord (% de richesse nette)")
    ax.legend(fontsize=9, loc="upper left")
    ax.set_title("Le REER gagne quand le taux baisse à la retraite, à l'égalité il est neutre")
    fig.savefig(dest)
    plt.close(fig)
