"""
Méthode utilisée en substitution à l’annotation :

La solution d’annotation de Starclay n’a pas été utilisée par manque de temps de la part du personnel du CHU.

La solution que nous avons mis en place pour pallier ce problème est la suivante :

- Nous avons récupéré des listes de termes médicaux sur wikipédia pour créer des relations entre les maladies, symptômes et traitements.
  Il nous est compliqué de récupérer la biologie et bactériologie car ces éléments se trouvent dans des textes libres et ne sont pas listés.
- Une fois ces termes récupérés et les relations créées, elles sont intégrées dans une base Neo4j pour y être stockées et utilisées.


Leur utilisation sera la suivante :

- Appliquer les termes médicaux sur les DPI anonymisés :
  Les DPI seront divisés en mots et une colonne sera créée où les termes médicaux seront annotés.
  Cela nous permettra de créer une base d’entrainement pour un modèle.
- Ce modèle visera à classer les termes médicaux en fonction de la probabilité d’appartenance de ces termes à telle ou telle relation.

"""


