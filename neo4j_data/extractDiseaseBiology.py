import pandas as pd
from pathlib import Path
import pymantic.sparql as sparql
import os
import yaml
import logging.config


def main():
    """
    Script qui :
        - lit *disease_biology23072020.tsv* qui contient les liens Biologie <-> Maladie :

            - bio : CONCEPT_CD_DXCARENUM
            - maladie : CONCEPT_CD_PMSI
            - value : poids du lien

        - lit le fichier *concept_dimension.csv* qui contient toutes les entités des métadonnées
        - merge les 2 pour garder, pour chaque lien, le nom de l'examen biologique
        - récupère le type d'examen bio depuis les métadonnées via CONCEPT_CD_DXCARENUM
        - sauvegarde dans *biology.csv*
    """

    log_config_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'logging.ini')
    logging.config.fileConfig(log_config_file)
    logger = logging.getLogger(os.path.basename(__file__))
    logger.info('Starting')

    logger.debug('Loading config')
    with open('config.yaml') as f:
        config = yaml.safe_load(f)

    biology_input_file = os.path.abspath(os.path.join(config['data']['input_dir'],
                                                      config['data']['input_files']['biologie']))
    concept_dim_input_file = os.path.abspath(os.path.join(config['data']['input_dir'],
                                                          config['data']['input_files']['concept_dimensions']))

    biology_output_file = os.path.abspath(os.path.join(config['data']['output_dir'],
                                                       config['data']['output_files']['biologie_neo4j']))
    os.makedirs(config['data']['output_dir'], exist_ok=True)

    blazegraph_endpoint = config['sources']['chu']['blazegraph']

    if os.path.exists(biology_output_file):
        logger.error(f"output file {biology_output_file} exists, stopping")
        exit(-1)

    try:
        #####################
        # Chargement des données, merge sur CONCEPT_CD_DXCARENUM  (on ne garde que la bio pour laquelle on a un lien
        #####################

        # Read the csv files

        # the disease_biology table contains links between a disease (PSMI code) and a biology term, as well as a value
        # this value is to be stored as an attribute of the edge between the 2 entities
        logging.debug(f"reading {biology_input_file}")
        disease_bio = pd.read_csv(biology_input_file, sep='\t')

        # the concept_dimension table contains all the concepts (including the biology)
        # the file is not in the git repo due to its large size
        logging.debug(f"reading {concept_dim_input_file}")
        concept_dim = pd.read_csv(concept_dim_input_file, sep='\t', encoding = "ISO-8859-1" )

        # we need only 2 columns from this data frame : CONCEPT_CD and NAME_CHAR
        concept_dim_sub = concept_dim[['CONCEPT_CD', 'NAME_CHAR']]
        concept_dim_sub.drop_duplicates(inplace=True)

        # merge the 2 data frames to have the name each biology concept
        logging.debug(f"merging on CONCEPT_CD_DXCARENUM")
        disease_bio_res = pd.merge(disease_bio, concept_dim_sub, left_on='CONCEPT_CD_DXCARENUM', right_on='CONCEPT_CD', how='left')

        # drop the CONCEPT_CD column as it is the same as the CONCEPT_CD_DXCARENUM column
        disease_bio_res.drop(columns=['CONCEPT_CD'], inplace=True)

        # the next step is to add the type of each biology exam
        # to do so, we need to extract the information from the metadata based on the CONCEPT_CD_DXCARENUM of the exams

        ###########################
        # On récupère le type d'examen bio depuis les métadonnées via CONCEPT_CD_DXCARENUM
        ###########################

        logging.debug(f"querying blazegraph to get exam type")
        # connect to the server where the metadata are
        server = sparql.SPARQLServer(blazegraph_endpoint)

        # query to retrieve the types of biological results
        query = """SELECT * WHERE {
                                    ?bio_exam rdf:type <http://chu-bordeaux.fr/biologie-dxcare-num#biologicalResult>.
                                    ?bio_exam <http://chu-bordeaux.fr/biologie-dxcare-num#resultInCategory> ?cat.
                                    ?cat <http://chu-bordeaux.fr/biologie-dxcare-num#categoryInCategory> ?cat2.
                                    ?cat2 <http://chu-bordeaux.fr/biologie-dxcare-num#categoryInDomain> ?domain.
                                    ?domain rdfs:label ?domainLabel
                                }"""
        res = server.query(query)

        # create a dictionary to map the biological result (CONCEPT_CD_DXCARENUM) to its type
        bio_type_dict = dict()
        for r in res['results']['bindings']:
            bio_id = r['bio_exam']['value'].split('-')[-1]
            bio_type_dict[bio_id] = r['domainLabel']['value']

        # add to the data frame, a column that contains the id of the biological result
        disease_bio_res['bio_id'] = disease_bio_res['CONCEPT_CD_DXCARENUM'].apply(lambda x: x.split(':')[-1])

        # create the column for the type
        disease_bio_res['type'] = disease_bio_res['bio_id'].map(bio_type_dict)

        # drop the newly added column "bio_id" as it is no loner needed
        disease_bio_res.drop(columns=['bio_id'], inplace=True)

        # replace nan values with empty strings
        disease_bio_res.fillna('n/a', inplace=True)

        # save to csv file
        logging.debug(f"saving to {biology_output_file}")
        disease_bio_res.to_csv(Path(biology_output_file), sep="\t", index=False)

        logging.info(f"Done!")
        exit(0)

    except Exception as e:
        logger.error(f'Something happened : {str(e)}')
        exit(-1)


if __name__ == "__main__":
    main()