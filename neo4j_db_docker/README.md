NEO4J Database docker
=====================

Build de l'image
----------------

L'image est basée sur l'image neo4j:3.5.17, à laquelle on ajoute des données, des scripts d'import, 
et un script de démarrage permettant une commande pour créer la database à partir des données dans l'image

- Data en csv et scripts cypher sont dans le sous dossier neo4j/db_generation.
- scripts de démarrage et de création de la base sont dans neo4j:
    - start_script.sh intercept l'argument 'generate_db' s'il existe, et lance db_generation.sh
    - db_generation.sh crée la DB à partir des fichier cypher et csv

Le dossier neo4j est copié dans le dossier /var/lib/neo4j/import dans l'image produite

Le script neo4j/build_docker.sh génère l'image.

**NB** : Ne pas lancer les scripts avec un *sudo*, cela résulterait à une erreur lors de la génération du graphe.


Utilisation de l'image
----------------------

L'image crée est nommée starclay/chub_neo4j:1.0.0 (ou latest). Pour le changer, re-tagger l'image ou modifier le 
fichier neo4j/build_docker.sh

Pour la démarrer, voir le fichier start_neo4j_docker.sh

<h4> Configuration </h4>
Voir fichier exemple pour les variables possibles. 

**IMPORTANT** : ne pas mapper de volume sur neo4j/import : c'est là où sont les données, ce qui empècherait la génération de la base

**Process**:

script de lancement : *start_neo4j_docker.sh*

- 1er lancement:
    - mapper un volume sur neo4j/data dans *start_neo4j_docker.sh*: c'est là que la base sera stockée sur disque
    - démarrer le docker avec './start_neo4j_docker.sh --generate', pour créer la db
        - les logs de création se voient en vert dans les logs de l'instance
        - si erreur, le message apparaitra en rouge et le process de création s'arretera
        - la création peut être un peu longue (en particulier, "add_biology" peut approcher les 30min selon la puissance disponible)
        
- lancements suivants:
    - laisser le volume de data mappé
    - lancer le docker avec './start_neo4j_docker.sh'
    - la base est accessible
    
    
Contenu du dossier
------------------

- **start_neo4j_docker.sh** : script de lancement de l'image docker (voir section précédente)
- **docker**:
    - **dockerfile**: description de l'image
    - **build_docker.sh**: appel de la commande docker pour générer l'image
    - **db_generation.sh** : script de génération de la db utilisant les scripts dans *db_generation*.
                             copié dans l'image
    - **start_script.sh**: script de démarrage de l'image. Copié dans l'image
    - **db_generation**: dossier contenant les données en csv et les scripts cypher pour les charger dans la base
        - **add_XXX.cypher**: chargement du fichier XXX.csv
        - **finalize_db.cypher**: finalisation de la base
        
