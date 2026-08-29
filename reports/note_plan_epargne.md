# Votre plan d'épargne, en dix mille avenirs plutôt qu'un seul

Note préparée à partir du simulateur `pec` (dépôt 12-plan-epargne-ca). Exercice de méthode
sous hypothèses déclarées ; ceci n'est pas un conseil financier. Chiffres du 2026-08-29,
cas type : 10 000 $ d'épargne par an pendant 30 ans, 25 ans de retraite, taux marginal de
35 % pendant la vie active et de 25 % à la retraite (à remplacer par les vôtres).

## Ce que le simulateur établit

**1. Le choix REER ou CELI est un pari sur vos deux taux d'imposition, à une discipline
près : réinvestir le remboursement.** À taux égaux, les deux comptes produisent exactement
le même dollar final : c'est une identité algébrique, pas une opinion, et le simulateur la
vérifie à la douzième décimale. Votre taux baissera à la retraite ? Le REER gagne, du
facteur exact (1 - taux retraite)/(1 - taux actif) : au cas type, 15 % de plus par dollar
cotisé, et 8,0 % de richesse nette finale une fois les plafonds respectés. Votre taux
MONTERA (gros FERR, récupération de la Sécurité de la vieillesse) ? Le CELI gagne,
symétriquement. Et si le remboursement d'impôt du REER est dépensé au lieu d'être
réinvesti, le classement s'inverse entièrement (mesuré : -18,9 % au cas type). La carte
des taux du rapport donne votre case en dix secondes.

**2. Le chiffre unique d'un plan de retraite est bon en moyenne et muet sur le risque.**
Le plan « sur papier » du cas type, calé sur le rendement composé 2002-2026 du
portefeuille (7,17 %/an), promet 95 862 $ de revenu annuel net. En rejouant l'histoire
dix mille fois par blocs d'un an, la médiane tient la promesse (94 568 $), mais un avenir
sur vingt livre moins de 45 855 $ : moins de la moitié. Même épargne, même portefeuille,
même durée ; seul l'ordre des bonnes et des mauvaises années change.

**3. Au scénario prudent, l'ordre de remplissage devient une affaire de probabilité,
pas de confort.** En retirant 2 points de rendement par année (l'esprit des normes de
projection de FP Canada), la cible modeste de 30 000 $ nets par an n'est plus atteinte
que dans 91 % des avenirs en remplissant le REER d'abord, et 88 % en remplissant le CELI
d'abord. Trois points de probabilité de réussite, gagnés en changeant seulement l'ordre
des versements.

## Ce que le simulateur ne dit pas

Il ignore la RRQ, la PSV et sa récupération, les paliers d'imposition, les retraits
minimums du FERR et le crédit d'impôt sur dividendes ; il fige les plafonds de 2026 ; son
histoire des rendements (2002-2026) est courte et plutôt heureuse. Chaque simplification
est déclarée dans le code et pèse dans un sens documenté. Pour une décision réelle : vos
taux réels, vos droits de cotisation réels, et un professionnel.

---

# Your savings plan, in ten thousand futures rather than one

Prepared from the `pec` simulator (repo 12-plan-epargne-ca). A methods exercise under
declared assumptions; not financial advice. Figures as of 2026-08-29; base case: $10,000
saved yearly for 30 years, 25 years of retirement, 35 % marginal tax while working, 25 %
retired (replace with your own).

**1. RRSP vs. TFSA is a bet on your two tax rates, plus one discipline: reinvesting the
refund.** At equal rates the two accounts compound to exactly the same final dollar (an
algebraic identity, verified by the simulator to twelve decimals). If your rate falls in
retirement, the RRSP wins by exactly (1 - t_ret)/(1 - t_work): 15 % more per dollar at the
base case, 8.0 % more final after-tax wealth once contribution caps bind. If your rate
will RISE (large RRIF, OAS clawback), the TFSA wins, symmetrically: read your cell in the
tax-rate map. And if the RRSP refund is spent rather than reinvested, the ranking flips
entirely (measured: -18.9 % at the base case).

**2. A single-number retirement plan is right on average and silent about risk.** The
paper plan (7.17 %/yr, the 2002-2026 compound of the policy portfolio) promises $95,862
of sustainable net income; the simulated median delivers it ($94,568), but one future in
twenty delivers less than $45,855. Same savings, same portfolio; only the ORDER of good
and bad years differs.

**3. Under a prudent scenario (returns minus 2 points), filling order becomes a matter of
probability.** The modest $30,000 target is reached in 91 % of futures RRSP-first versus
88 % TFSA-first: three points of success probability, bought by reordering deposits.

Not modelled: QPP, OAS and its clawback, tax brackets, RRIF minimums, dividend credits;
caps frozen at 2026; a short and mostly happy return sample. Every simplification is
declared in the code. For a real decision: your real rates, your real room, and a
professional.
