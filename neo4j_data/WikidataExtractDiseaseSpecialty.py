import pymantic.sparql as sparql
from pathlib import Path
import pandas as pd
import yaml
import os
import logging.config


def main():
    """
    Script qui :
        - va récupérer dans wikidata les spécialités associées au maladies (par code wikidata des maladies)

          (pas de croisement avec les PMSI connus)
        - sauvegarde vers *specialties.csv*
    """

    log_config_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'logging.ini')
    logging.config.fileConfig(log_config_file)
    logger = logging.getLogger(os.path.basename(__file__))
    logger.info('Starting')


    with open('config.yaml') as f:
        config = yaml.safe_load(f)

    specialties_output_file = os.path.abspath(os.path.join(config['data']['output_dir'],
                                                           config['data']['output_files']['specialites_neo4j']))
    os.makedirs(config['data']['output_dir'], exist_ok=True)

    wikidata_sparql_endpoint = config['sources']['wikidata']['sparql']


    if os.path.exists(specialties_output_file):
        logger.error(f"output file {specialties_output_file} exists, stopping")
        exit(-1)

    try:
        logger.debug(f'Querying wikidata to get specialties')
        server = sparql.SPARQLServer(wikidata_sparql_endpoint)

        # Query to retrieve links between diseases and specialties from Wikidata
        sparql_query_disease_specialties = """
                                            SELECT DISTINCT ?disease ?label ?spe WHERE {
                                            ?disease wdt:P31 wd:Q12136;
                                                     wdt:P1995 ?spe.
                                            ?spe rdfs:label ?label;
                                            FILTER (lang(?label) = 'fr')
                                            }
                                        """

        endpoint_results = server.query(sparql_query_disease_specialties)
        endpoint_data = endpoint_results["results"]["bindings"]

        # stock the results to a data frame
        specialties = pd.DataFrame(columns=['diseaseWikidata', 'label', 'wikidata'])

        for elt in endpoint_data:
            specialties = specialties.append({'diseaseWikidata': elt['disease']['value'].split('/')[-1],
                                              'label': elt['label']['value'],
                                              'wikidata': elt['spe']['value'].split('/')[-1]},
                                             ignore_index=True)

        # save to csv file
        logger.debug(f'saving to {specialties_output_file}')
        specialties.to_csv(Path(specialties_output_file), sep="\t", index=False)

        logging.info(f"Done!")
        exit(0)

    except Exception as e:
        logger.error(f'Something happened : {str(e)}')
        exit(-1)


if __name__ == "__main__":
    main()