import pymantic.sparql as sparql
from bs4 import BeautifulSoup
import requests
import pandas as pd
import yaml
import os
import logging.config


def main():
    """
    Since some of the medical entities (drugs, symptoms, specialties) are linked to diseases via the wikidata codes,
    and since not all of the diseases nodes have a wikidata code attribute, we are going to scrape wikidata in order to
    enrich the disease nodes (represented by an ICD10 code) with wikidata codes.

    PS: The script takes several hours to complete running, so an output file is available in data/graph/output to facilitate
    the reuse of the results obtained.

    generates:
        - mapping_wiki_icd10.csv  -> mappinc code wikidata <-> UCD10
    """

    log_config_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'logging.ini')
    logging.config.fileConfig(log_config_file)
    logger = logging.getLogger(os.path.basename(__file__))
    logger.info('Starting')


    with open('config.yaml') as f:
        config = yaml.safe_load(f)

    mapping_wiki_icd10_output_file = os.path.abspath(os.path.join(config['data']['output_dir'],
                                                                  config['data']['output_files']['mapping_wiki_icd10']))
    os.makedirs(config['data']['output_dir'], exist_ok=True)

    wikidata_sparql_endpoint = config['sources']['wikidata']['sparql']


    # if os.path.exists(mapping_wiki_icd10_output_file):
    #     logger.error(f"output file {mapping_wiki_icd10_output_file} exists, stopping")
    #     exit(-1)

    try:


        ##########
        #
        ##########

        # first, query wikidata to get all diseases entities (represented by a wikidata code)
        logger.debug(f'Querying wikidata to get all diseases')
        server = sparql.SPARQLServer(wikidata_sparql_endpoint)
        query = """SELECT distinct ?disease
                    WHERE
                    {
                      ?disease wdt:P31 wd:Q12136 ;
                    }"""
        endpoint_results = server.query(query)
        endpoint_data = endpoint_results["results"]["bindings"]

        # create dict that will contain the mapping icd10-wikidata codes
        logger.info(f'starting to scrape wikidata')

        def _save():
            logger.debug(f'saving to {mapping_wiki_icd10_output_file}')
            df = pd.DataFrame(wiki_icd.items(), columns=['wikidata', 'icd10'])
            df.to_csv(mapping_wiki_icd10_output_file, sep='\t', index=False)

        def _load():
            current_dict = {}
            if os.path.exists(mapping_wiki_icd10_output_file):
                wiki_icd_data = pd.read_csv(mapping_wiki_icd10_output_file, sep='\t')
                current_dict = {k: v for k, v in zip(wiki_icd_data['wikidata'].values, wiki_icd_data['icd10'].values)}
                logger.info(f'Starting from : {len(current_dict)}')
            else:
                logger.info(f'Starting from 0')
            return current_dict

        wiki_icd = _load()

        logger.info(f'Total iterations : {len(endpoint_data)}')
        for counter, d in enumerate(endpoint_data):
            try:
                wikidataURL = d['disease']['value']
                if wikidataURL in wiki_icd:
                    continue
                page = requests.get(wikidataURL.replace('entity', 'wiki'))
                soup = BeautifulSoup(page.content, 'html.parser')
                wiki_icd[wikidataURL] = []
                for elt in soup.find_all('a', class_='wb-external-id external'):
                    if 'icd.who' in elt['href']:
                        wiki_icd[wikidataURL].append(elt['href'].split('/')[-1])
                    if 'icdcodelookup' in elt['href']:
                        wiki_icd[wikidataURL].append(elt['href'].split('/')[-1])
                if (counter + 1) % 100 == 0:
                    logger.info(f'{counter} iterations done')
                    _save()
            except :
                continue

        # save the dict as a df and then as csv file
        _save()

        logging.info(f"Done!")
        exit(0)

    except Exception as e:
        logger.error(f'Something happened : {str(e)}')
        exit(-1)


if __name__ == "__main__":
    main()