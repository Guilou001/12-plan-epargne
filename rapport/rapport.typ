#set document(title: "Épargner pour la retraite sans supposer que chaque année sera bonne", author: "Guillaume Vaudescal")
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
// la table NE DOIT PAS être enfermée dans un par() : Typst 0.15 la supprime alors
// entièrement, sans erreur. Le réglage se pose donc dans la portée du bloc.
#show table: it => block(above: 1.1em, below: 1.1em,
  [#set par(justify: false); #text(size: 8.8pt, it)])
#show figure: it => block(above: 1.4em, below: 1.4em, it)
#show figure.caption: it => text(size: 8.5pt, fill: luma(70), it)
#show link: it => text(fill: rgb("#0072B2"), it)

#align(center)[
  #block(width: 100%)[
    #text(size: 18pt, weight: "bold")[Épargner pour la retraite sans supposer que chaque année sera bonne]
    #v(0.6em)
    #text(size: 10pt, fill: luma(70))[Guillaume Vaudescal · 2026-09-08 · #link("https://github.com/Guilou001/12-plan-epargne")[Guilou001/12-plan-epargne]]
  ]
]
#v(1.2em)
#line(length: 100%, stroke: 0.6pt + luma(190))
#v(0.8em)

Mettre de l'argent de côté ne suffit pas à connaître son revenu futur. Le compte utilisé, les impôts et l'ordre des bonnes et mauvaises années changent le résultat.

Ce projet compare le REER, où l'impôt est reporté au retrait, et le CELI, où l'argent déjà imposé peut ensuite croître sans impôt. Il rejoue des blocs de douze mois de rendements historiques pour construire 10 000 parcours possibles.

*Le remboursement d'impôt et l'inflation peuvent changer la conclusion d'un plan qui paraît rassurant.*

== Un même effort d'épargne, plusieurs résultats

Le cas étudié prévoit 10 000 dollars canadiens d'épargne annuelle après impôt pendant 30 ans, puis 25 ans de retraite. Le taux d'imposition passe de 35 % à 25 %. Ce sont des hypothèses d'exercice.

#figure(image("../results/figures/presentation.png", width: 100%), caption: [Effet du remboursement d'impôt et de l'indexation sur le classement des comptes])

Une barre à droite de zéro favorise le REER d'abord. À gauche, le CELI d'abord finit devant. Dépenser le remboursement inverse le classement, même si le taux d'imposition baisse à la retraite.

#table(
  columns: 2,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Hypothèse*],
    [*Avantage de richesse médiane du REER d'abord sur le CELI d'abord*],
    [Remboursement réinvesti, montants non indexés],
    [+8,0 %],
    [Cotisations et revenu cible augmentés de 2 % par an],
    [+3,8 %],
    [Remboursement dépensé],
    [−18,9 %],
)

La richesse médiane est celle du parcours situé au milieu des simulations. Le signe négatif signifie que le CELI d'abord finit devant. #link("results/tables/sensibilites.csv")[Calculs des trois variantes].

== Pourquoi les deux comptes peuvent être équivalents

Avec le même taux d'imposition au dépôt et au retrait, sans plafonds et avec le remboursement entièrement réinvesti, les deux comptes donnent exactement la même somme nette. Le programme vérifie cette égalité avant de simuler les cas plus complexes.

Les rendements proviennent de six fonds canadiens entre novembre 2002 et août 2026. Les mêmes tirages servent à comparer les comptes, afin qu'un ordre ne bénéficie pas par hasard de meilleures années.

== La limite à lire avant les montants

Le cas de référence utilise des dollars courants. Sa cible de 30 000 dollars perd donc du pouvoir d'achat au fil du temps. Lorsque cotisations et cible augmentent de 2 % par an, le taux de réussite du REER d'abord passe de 99,5 % à 90,5 %.

La fiscalité est simplifiée et les droits de cotisation sont figés. Les simulations ne créent pas de crises absentes de l'historique. Ce dépôt explique ces mécanismes et ne remplace pas un plan financier personnel.

== Refaire les calculs

#raw("uv sync --locked --all-extras\nuv run pytest\nuv run pec fetch\nuv run pec simulate", block: true, lang: "bash")

Les commandes de téléchargement accèdent aux sources externes. Les résultats publiés restent consultables sans lancer les calculs. Le graphique de présentation se régénère hors réseau avec #raw("uv run python scripts/figure_presentation.py"), depuis les tableaux publiés.

== Pour aller plus loin

#link("docs/ETUDE_DETAILLEE.md")[Méthodes, résultats complets et références] · #link("rapport/rapport.pdf")[Présentation en PDF] · #link("CITATION.cff")[Citer le projet] · #link("LICENSE")[Licence].

== English summary

An RRSP–TFSA simulator compares identical savings budgets under historical return resampling. Reinvesting tax refunds and indexing the savings target materially change the results. Tax rules are simplified.
