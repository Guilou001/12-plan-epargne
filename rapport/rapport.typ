#set document(title: "REER, CELI, ou les deux : le plan d'épargne simulé plutôt que promis", author: "Guillaume Vaudescal")
#set page(
  paper: "a4",
  margin: (x: 2.2cm, y: 2.4cm),
  numbering: "1 / 1",
  footer: context [
    #set text(size: 8pt, fill: luma(90))
    #grid(columns: (1fr, auto), align: (left, right),
      [plan-epargne-ca], [#counter(page).display("1 / 1", both: true)])
  ],
)
#set text(font: ("Helvetica", "Arial", "DejaVu Sans"), size: 10pt, lang: "fr")
#set par(justify: true, leading: 0.68em, spacing: 1.1em)
#set heading(numbering: none)
#show heading.where(level: 2): it => block(above: 1.6em, below: 0.8em, text(size: 13pt, it))
#show heading.where(level: 3): it => block(above: 1.2em, below: 0.6em, text(size: 11pt, it))
#show raw.where(block: true): it => block(
  fill: luma(246), inset: 8pt, radius: 3pt, width: 100%, text(size: 8.5pt, it))
#show raw.where(block: false): it => text(size: 9pt, fill: rgb("#1a3f66"), it)
#show quote.where(block: true): it => block(
  inset: (left: 10pt), stroke: (left: 1.5pt + luma(180)),
  text(style: "italic", fill: luma(45), it.body))
#show table: it => block(above: 1.1em, below: 1.1em,
  par(justify: false, text(size: 8.8pt, it)))
#show figure: it => block(above: 1.4em, below: 1.4em, it)
#show figure.caption: it => text(size: 8.5pt, fill: luma(70), it)
#show link: it => text(fill: rgb("#0072B2"), it)

#align(center)[
  #block(width: 100%)[
    #text(size: 18pt, weight: "bold")[REER, CELI, ou les deux : le plan d'épargne simulé plutôt que promis]
    #v(0.6em)
    #text(size: 10pt, fill: luma(70))[Guillaume Vaudescal · 2026-08-29 · #link("https://github.com/Guilou001/12-plan-epargne")[Guilou001/12-plan-epargne]]
  ]
]
#v(1.2em)
#line(length: 100%, stroke: 0.6pt + luma(190))
#v(0.8em)

Un simulateur Monte Carlo des trois comptes d'épargne canadiens, alimenté par les rendements du portefeuille de politique du dépôt 03, avec les équivalences fiscales prouvées par des tests analytiques exacts. Le seul dépôt du portfolio écrit pour un client final. _English summary below._

Le même contenu en PDF : #link("rapport/rapport.pdf")[rapport/rapport.pdf].

== En bref

+ *À taux d'imposition égaux, REER et CELI sont EXACTEMENT équivalents.* Ce n'est pas une opinion, c'est une identité algébrique, et le simulateur la retrouve à 1e-12 près (testé). Tout l'avantage du REER tient dans l'écart entre le taux marginal d'aujourd'hui et celui de la retraite, POURVU que le remboursement d'impôt soit réinvesti : au cas type (35 % actif, 25 % retraité), REER d'abord bat CELI d'abord de 8,0 % de richesse nette médiane (1 193 538 \$ contre 1 105 368 \$, mesuré) ; le remboursement dépensé, le classement s'inverse (-18,9 %, mesuré, testé). La carte des taux donne le verdict pour tous les autres profils.
+ *Ce que la moyenne promet, un avenir sur vingt n'en livre pas la moitié.* Le plan « sur papier » à rendement constant (7,17 %/an, le composé 2002-2026 du portefeuille) promet un revenu de retraite net de 95 862 \$/an ; la médiane simulée le tient (94 568 \$), mais le 5e percentile tombe à 45 855 \$. La moyenne cache le risque de séquence. (Mesuré.)
+ *Au scénario prudent (rendements amputés de 2 points, déclaré), même la cible de base vacille.* À 5,06 %/an, la cible de 30 000 \$ nets n'est atteinte que dans 91,2 % des avenirs en REER d'abord, 88,0 % en CELI d'abord : l'ordre de remplissage vaut 3 points de probabilité de réussite, pas seulement des dollars. (Mesuré.)

Ceci est un exercice de méthode, pas un conseil financier : toutes les règles fiscales sont des simplifications déclarées et les taux marginaux sont des paramètres à remplacer par les vôtres.

== La question

Pour un épargnant québécois type, dans quel ordre remplir REER, CELI et compte imposable, et que devient la probabilité d'atteindre un revenu de retraite cible quand on simule les rendements au lieu de les supposer constants ? La tension : le REER domine le CELI dans les comparatifs usuels, or l'identité algébrique dit qu'à taux égaux ils sont indiscernables ; et le plan déterministe promet un chiffre unique, or dix mille rejeux de l'histoire en font une distribution.

== Le moteur fiscal, en conventions déclarées

Trois comptes, trois traitements. Le REER, cotisé en dollars AVANT impôt : la chaîne complète des remboursements d'impôt est réinvestie (le remboursement, puis le remboursement du remboursement, et ainsi de suite), ce qui équivaut à cotiser b/(1 - t) pour un budget après impôt b (convention du « grossing up », déclarée ; l'option #raw("remboursement_reinvesti") du moteur permet de la couper, et la limite 1 dit ce que cela renverse) ; le retrait est imposé au taux de la retraite. Le CELI, cotisé après impôt, croît et se retire sans impôt. Le compte non enregistré, cotisé après impôt, subit chaque année un impôt sur ses gains à l'inclusion de 50 % au taux de la vie active, décumulation comprise (gains réputés réalisés annuellement, pertes créditées immédiatement : simplifications déclarées).

La vérité connue qui verrouille le moteur : à taux égaux et sans plafond,

#raw("b/(1 - t) x (1 + r)^N x (1 - t)  =  b x (1 + r)^N", block: true)

le REER et le CELI produisent le même dollar final, exactement. Le test #raw("test_reer_egale_celi_quand_les_taux_sont_egaux") l'exige à 1e-12 ; le facteur exact (1 - t\_retraite)/(1 - t\_actif) quand les taux diffèrent est testé de même. Le moteur vectoriel (10 000 trajectoires d'un coup) est contraint d'égaler le moteur scalaire à 1e-8 (testé aussi) : la vitesse n'a pas le droit de changer les chiffres.

Plafonds : 7 000 \$ de droits CELI annuels (2026, rapporté) et 12 960 \$ de droits REER (18 % d'un revenu de 72 000 \$, cas type, précepte). Ce sont les plafonds, et eux seuls, qui séparent les trois ordres de remplissage quand les taux sont égaux.

== Le cas type (précepte déclaré, à remplacer par vos chiffres)

10 000 \$ d'épargne annuelle après impôt pendant 30 ans ; 25 ans de retraite ; cible de 30 000 \$ nets par an HORS RRQ et pension de la Sécurité de la vieillesse ; taux marginal de 35 % pendant la vie active, 25 % à la retraite (chiffres ronds, pas un barème). Les rendements viennent du portefeuille de politique du dépôt 03 (XIU 25 %, XSP 20 %, XIN 15 %, XRE 5 %, XBB 25 %, XSB 10 %, mêmes poids, déclaré) : 286 rendements mensuels, 2002-11 à 2026-08, via yfinance (usage personnel, jamais commité ; le dernier mois est tronqué au jour du téléchargement, effet de 0,04 point sur le composé, déclaré).

Le Monte Carlo tire des blocs de 12 mois CONSÉCUTIFS à départ aléatoire : les enchaînements d'une année de crise (2008, 2020, 2022) restent intacts, les années sont indépendantes entre elles (convention déclarée). Les mêmes tirages servent aux trois ordres : la comparaison est appariée, l'écart entre ordres ne doit rien au hasard des tirages.

== Verdict 1 : l'ordre de remplissage (mesuré, #raw("results/tables/resume_ordres.csv"))

#table(
  columns: 5,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Ordre*],
    [*P(cible atteinte)*],
    [*Richesse nette médiane*],
    [*Revenu soutenable médian*],
    [*p5*],
    [REER d'abord],
    [99,5 %],
    [1 193 538 \$],
    [94 568 \$],
    [45 855 \$],
    [Moitié-moitié],
    [99,4 %],
    [1 137 879 \$],
    [90 158 \$],
    [43 717 \$],
    [CELI d'abord],
    [99,2 %],
    [1 105 368 \$],
    [87 582 \$],
    [42 468 \$],
)

*Lecture guidée.* Au cas type, le taux tombe de 10 points à la retraite : chaque dollar passé par le REER se multiplie par (1 - 0,25)/(1 - 0,35) = 1,154 par rapport au même dollar en CELI. L'avantage mesuré (8,0 % de richesse nette) est plus petit que 15,4 %, car les plafonds forcent une partie de l'épargne hors du REER. Le revenu soutenable, le montant net constant qui épuise exactement le patrimoine sur 25 ans (calculé par bissection sur chaque trajectoire), ordonne les trois stratégies dans le même sens.

#figure(image("../results/figures/carte_des_ordres.png", width: 100%), caption: [Carte des ordres])

*Comment lire cette figure.* L'avantage du REER d'abord sur le CELI d'abord, en % de richesse nette, pour chaque couple de taux (vie active en abscisse, retraite en ordonnée). Sur la diagonale, zéro : c'est l'équivalence algébrique, retrouvée par le simulateur. Sous la diagonale (le taux baisse à la retraite, le cas usuel), le REER gagne, jusqu'à +20 %. Au-dessus (taux plus HAUT à la retraite : récupération de la PSV, revenus de retraite élevés), le CELI gagne, jusqu'à -19 %. L'étoile marque le cas type. Placez vos deux taux, lisez votre case.

== Verdict 2 : la promesse contre la distribution (mesuré)

#figure(image("../results/figures/eventail_richesse.png", width: 100%), caption: [Éventail de richesse])

*Comment lire cette figure.* Dix mille rejeux du même plan d'épargne. La bande foncée contient la moitié centrale des avenirs, la bande pâle en contient 90 %. La ligne pointillée est le plan à rendement constant : il suit la médiane presque exactement (1 517 321 \$ contre 1 535 877 \$ à l'an 30), et c'est le piège : le chiffre unique du planificateur est BON en espérance et muet sur l'éventail, qui fait plus que tripler entre p5 et p95 (x3,2 à l'an 30, mesuré).

#figure(image("../results/figures/revenu_soutenable.png", width: 100%), caption: [Revenu soutenable])

*Comment lire cette figure.* Pour chaque revenu en abscisse, la part des trajectoires capables de le servir pendant 25 ans. La ligne verticale grise est la promesse du plan constant (95 862 \$) : 48,7 % des avenirs la tiennent en REER d'abord (mesuré, lisible à l'intersection). La cible de 30 000 \$ (pointillé) est quasi sûre sur l'historique brut ; le tableau prudent ci-dessous la met à l'épreuve.

== Verdict 3 : le scénario prudent (mesuré, #raw("results/tables/resume_ordres_prudent.csv"))

L'échantillon 2002-2026 compose à 7,17 %/an, porté par quinze années de marché haussier ; le futur n'y a droit à rien. Le scénario prudent retire 2/12 de point à chaque rendement mensuel des mêmes tirages, soit 2,1 points de composé annuel (7,17 % à 5,06 % ; convention déclarée, dans l'esprit des normes de projection de FP Canada) :

#table(
  columns: 5,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Ordre*],
    [*Rendement*],
    [*P(30 000 \$ atteints)*],
    [*Revenu soutenable médian*],
    [*p5*],
    [REER d'abord],
    [5,06 %],
    [91,2 %],
    [53 434 \$],
    [26 234 \$],
    [Moitié-moitié],
    [5,06 %],
    [89,3 %],
    [50 942 \$],
    [25 011 \$],
    [CELI d'abord],
    [5,06 %],
    [88,0 %],
    [49 486 \$],
    [24 296 \$],
)

*Lecture guidée.* Deux points de rendement en moins retranchent 43 % du revenu médian (94 568 \$ à 53 434 \$) : la capitalisation amplifie tout, dans les deux sens. Et à ce niveau, l'ordre de remplissage cesse d'être cosmétique : 3,2 points de probabilité de réussite séparent REER d'abord de CELI d'abord, et l'échec devient courant : 8,8 % des avenirs ne financent pas 30 000 \$/an en REER d'abord, 12,0 % en CELI d'abord, environ un sur dix.

== Reproduire

#raw("uv sync --locked --all-extras\nuv run pytest          # 11 tests analytiques, sans réseau\nuv run pec fetch       # six FNB, yfinance (usage personnel)\nuv run pec simulate    # 3 ordres x 10 000 trajectoires + prudent + carte (~40 s)", block: true, lang: "bash")

Les tests sont des vérités fermées : équivalence REER/CELI exacte à taux égaux, facteur (1 - t\_r)/(1 - t\_a) exact à taux différents, plafonds respectés au dollar, décumulation à rendement nul contre la forme fermée (750 000 \$ financent exactement 25 ans à 30 000 \$ depuis un CELI, 1 000 000 \$ depuis un REER à 25 %), bissection retrouvant l'annuité due à rendement nul ET constant, renversement du classement quand le remboursement est dépensé, bootstrap reproductible à graine fixée, moteur vectoriel contraint d'égaler le scalaire, carte neutre sur la diagonale.

== Limites, avec statut

Les trois premières sont chiffrées dans #raw("results/tables/sensibilites.csv"), rejouées par #raw("pec simulate") : aucune n'est discutée sans être mesurée.

+ *Tout est en dollars COURANTS.* Les 10 000 \$ cotisés chaque année et les 30 000 \$ visés à la retraite ne sont jamais revalorisés sur cinquante-cinq ans, et les rendements sont nominaux. La probabilité d'atteinte de 99,5 % mesure donc la couverture d'une cible dont le pouvoir d'achat s'érode. Le plan indexé à 2 % par an, cotisations ET cible, tombe à *90,5 %*, et l'avantage du REER d'abord passe de +8,0 % à +3,8 % de richesse nette (mesuré, option #raw("inflation") de #raw("run_monte_carlo")). C'est la limite qui déplace le plus le verdict de tête.
+ *Le verdict REER dépend de la convention de réinvestissement.* Le moteur réinvestit la chaîne complète des remboursements d'impôt ; si le remboursement est DÉPENSÉ, le classement s'inverse au cas type (CELI d'abord gagne de 18,9 % de richesse nette, mesuré, option #raw("remboursement_reinvesti=False") et test dédié). L'avantage du REER est un pari sur les deux taux À CONVENTION DONNÉE, et la discipline de réinvestir le remboursement en fait partie. La convention porte aussi sur la DATE : le remboursement est réinvesti l'année même de la cotisation, ce qui suppose une réduction de la retenue à la source (formulaire T1213 au fédéral) ou une avance de trésorerie. (Mesuré et déclaré.)
+ *La fiscalité est une maquette.* Taux marginaux constants par période, pas de paliers, pas de PSV ni de RRQ, pas de récupération de la PSV, pas de FERR à retraits minimums, pas de crédit d'impôt sur dividendes ; le non enregistré impose tout à l'inclusion de 50 % chaque année, au taux de la vie active même pendant la décumulation (sans effet ici, le compte restant vide au cas type, déclaré). Chaque règle est déclarée dans #raw("fiscal.py") ; la récupération de la PSV se lit dans la carte comme un taux de retraite effectif plus élevé. (Précepte.)
+ *L'échantillon de rendements est court et heureux.* 286 mois dont un seul grand krach ; le bootstrap ne crée pas de crises qu'il n'a pas vues ; le scénario prudent est la réponse déclarée, pas une prévision. (Mesuré pour l'échantillon, précepte pour le prudent.)
+ *Les années simulées sont indépendantes.* Les blocs de 12 mois préservent les enchaînements intra-année, pas les cycles pluriannuels (un marché baissier de trois ans est sous-représenté). (Déclaré.)
+ *Les plafonds sont figés* au niveau 2026 pendant 30 ans, sans indexation ni droits inutilisés reportés. (Déclaré ; l'indexation des deux plafonds jouerait dans le même sens pour les trois ordres.)

5 bis. *Le plafond REER de 12 960 \$ est ACTIF dans chaque case de la carte des taux*, alors que le plafond et le taux marginal sont deux fonctions du même revenu : la carte suppose partout les droits d'un revenu de 72 000 \$. Avec les droits d'un revenu de 150 000 \$ (27 000 \$), l'avantage du REER d'abord au cas type passe de +8,0 % à +10,3 % de richesse nette (mesuré). Lire une case suppose donc ce plafond-là, pas le vôtre. (Déclaré.)

+ *Aucun conseil.* Ce dépôt compare des mécaniques sous hypothèses déclarées ; il ne connaît ni votre revenu, ni vos taux réels, ni votre tolérance au risque.

== Références

- Normes de projection de FP Canada et de l'IQPF (hypothèses de rendement pour la

planification, publiées annuellement) : l'esprit du scénario prudent.

- Milevsky, M. A., _The Calculus of Retirement Income_, Cambridge University Press, 2006 :

le revenu soutenable et la ruine stochastique.

- Bengen, W. (1994), « Determining withdrawal rates using historical data », \*Journal of

Financial Planning\* : l'ancêtre du retrait soutenable simulé.

- Agence du revenu du Canada et Revenu Québec : mécanique REER/CELI (les règles simplifiées

du moteur s'y réfèrent, sans en reproduire les barèmes).

== English summary

A Monte Carlo simulator of Canada's three savings vehicles (RRSP, TFSA, taxable), driven by one-year block bootstrap of the repo-03 policy portfolio (286 monthly returns, 2002-2026), with the tax mechanics locked by exact analytic tests: with equal marginal tax rates and no caps, RRSP and TFSA compound to the SAME final dollar (tested to 1e-12), and the entire RRSP advantage is the factor (1 - t\_ret)/(1 - t\_work). Base case (35 % working, 25 % retired): RRSP-first beats TFSA-first by 8.0 % of median after-tax wealth; a tax-rate map gives the verdict for every other profile, exactly zero on the diagonal. The verdict assumes the tax refund is fully reinvested: spent instead, the ranking flips (TFSA-first wins by 18.9 %, measured and tested). The deterministic plan (7.17 %/yr, the 2002-2026 compound) promises a \$95,862 sustainable retirement income; the simulated median delivers it, but the 5th percentile is \$45,855. Under a declared prudent scenario (returns minus 2 points), the basic \$30,000 target is only reached in 91.2 % of futures (RRSP-first) versus 88.0 % (TFSA-first): filling order buys 3 points of success probability. Simplified declared tax conventions, no OAS/QPP, no advice; 11 closed-form tests, no network.

== Licence et citation

Code sous licence MIT ; rapport et figures CC BY 4.0. Données : Yahoo Finance (usage personnel, jamais commitées). Citer via #raw("CITATION.cff").
