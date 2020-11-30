Neo4j Base data generation
==========================

Context
-------

The purpose of the scripts in this directory is generate the files that will serve to construct the knowledge graph (KG) later.

Methodology
-----------
Most of the files used to construct the KG were extracted from [Wikidata](https://query.wikidata.org/), while some of the 
data was provided by the CHU. Some changes were made in order to meet with needs of the CHU.

Diseases
~~~~~~~~
The main information about diseases (ICD10 codes, PMSI codes and diseases names) were extracted from the metadata of the CHU.
Other information was added using [Wikidata](https://query.wikidata.org/), which are the Wikidata codes and UMLS codes.
The `extractDiseasesAttributes.py` script explains the steps followed to do so.

Biology
~~~~~~~
There was no public data relating diseases to biology. Therefore, the CHU provided us a list of disease-biology relations, 
as well as a value that characterizes the "strength" of the relation (to be stored as an attribute of the edge). 
The `extractDiseaseBiology.py` script adds the labels of each biological term (a concept was provided) based on the `concept_dimension.csv` file.

Drugs
~~~~~
The disease-drug relations were extracted from [Wikidata](https://query.wikidata.org/), each drug was represented by its label and its wikidata code.
However, additional information about the drugs was need from the CHU. So, [Romedi](https://www.romedi.fr/) was used for this purpose, it allows to 
get such information (UCD13, NIMED, CIS, Ingredient, Brand Name ...).
The `Wikidata-extractDiseaseDrugs.py` script contains steps for the matching.

Symptoms
~~~~~~~~
Each symptom associated with a disease (wikidata code) is also identified now by its UMLS code, its Wikidata code and some 
synonyms, in order to have as much information as possible about symptoms. The script that does the matching of the 
symptoms with the other information is `Wikidata-extractDiseaseSymptoms.py`.

Specialties
~~~~~~~~~~~
Each disease is associated with a medical specialty, that itself, is characterized by a wikidata code. 
The relations were extracted from [Wikidata](https://query.wikidata.org/) and the `Wikidata-extractDiseaseSpecialty.py` 
script contains the steps to do so.


Utilisation
-----------

1. Editer *config.yaml* pour configurer sources et outputs
2. Générer l'ensemble des données via 

        ./extract_all.sh

3. copier tous les fichiers outputs post-fixés '_neo4j' dans *config.yaml* dans ../neo4j_db_docker/docker/db_generation
4. Continuer avec la génération de l'image (voir ../neo4j_db_docker/README.md)


Contenu du dossier
------------------

- **requirements.txt**: modules à installer
- **config.yaml**: fichier de configuration pour l'extraction
    - input -> dossier contenant les données input, et liste des fichiers
    - output -> dossier où écrire les fichiers de sortie, et liste des fichiers de sortie. La description des fichiers d'input et output est dans la section suivante, ou dans *files_description.md*
    - sources -> paramêtrage des liens vers les db et autres apis
- **logging.ini**: fichier de configuration pour le log
- **extract_all.sh**: script appliquant tous les scripts listés ci-dessous
    -> script principal

- **extractDiseaseBiology.py**: 
    - extrait les données des noeuds 'biologie', et les liens vers les maladies
    - input files: 
        - config['data']['input_files']['biologie']
        - config['data']['input_files']['concept_dimensions']
    - output files : 
        - config['data']['output_files']['biologie_neo4j']
- **extractDiseasesAttributes.py**
    - extrait les données pour les noeuds 'maladies'
    - input files: -
    - output files : 
        - config['data']['output_files']['maladies']
- **prepareDiseasesData.py**
    - consolide les données des noeuds 'maladie'
    - input files: 
        - config['data']['output_files']['maladies']
        - config['data']['output_files']['symptomes_neo4j']
        - config['data']['output_files']['specialites_neo4j']
        - config['data']['output_files']['medicaments']
        - config['data']['output_files']['mapping_wiki_icd10']
    - output files : 
        - config['data']['output_files']['maladies_neo4j']
- **prepareDrugsData.py**
    - répartit les données de "medicaments" entre les différents types de noeuds
    - input files: 
        - config['data']['input_files']['medicaments']
    - output files : 
        - config['data']['output_files']['medicaments_neo4j']
        - config['data']['output_files']['classes_therapeutiques_neo4j']
        - config['data']['output_files']['molecules_neo4j']
        - config['data']['output_files']['noms_commerciaux_neo4j']
- **RomediAPI.py**
    - module avec les fonctions d'appel à l'API Romedi
- **scrapeWikidata.py**
    - scrapping de wikidata pour récupérer des données sur les maladies
    - input files: -
    - output files : 
        - config['data']['output_files']['mapping_wiki_icd10']
- **WikidataExtractDiseaseDrugs.py**
    - Récupération des données des noeuds liés aux médicaments au sens large, et des liens entre eux et avec les maladies
    - input files: - 
    - output files : 
        - config['data']['output_files']['medicaments']
- **WikidataExtractDiseaseSpecialty.py**
    - Récupération des données des spécialités médicales, et leurs liens avec les maladies
    - input files: -
    - output files : 
        - config['data']['output_files']['specialites_neo4j']
- **WikidataExtractDiseaseSymptoms.py**
    - Récupération des données des symptomes, et leurs liens avec les maladies
    - input files: 
        - config['data']['input_files']['frenchTerminoUMLS2019AB']
    - output files : 
        - config['data']['output_files']['symptomes_neo4j']

