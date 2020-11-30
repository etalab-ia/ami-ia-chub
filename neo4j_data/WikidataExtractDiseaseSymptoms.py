#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 21 16:06:53 2020

@author: cossin
"""

import pymantic.sparql as sparql
from pathlib import Path
import pandas as pd
import os
import yaml
import logging.config


def main():
    """
    Script qui :
        - va récupérer dans wikidata les symptomes associées au maladies (par code wikidata des maladies)

          (pas de croisement avec les PMSI connus)

        - récupération dans wikidata des codes CUI par code wikidata des symptomes)
        - lecture du fichier *frenchTerminoUMLS2019AB.csv* qui liste des synonymes pour tous types de concepts, par code CUI
        - on ne garde que les synonymes des symptômes
        - sauvegarde dans *symptoms.csv*
    """

    log_config_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'logging.ini')
    logging.config.fileConfig(log_config_file)
    logger = logging.getLogger(os.path.basename(__file__))
    logger.info('Starting')


    with open('config.yaml') as f:
        config = yaml.safe_load(f)

    frenchTerminoUMLS2019AB_input_file = os.path.abspath(os.path.join(config['data']['input_dir'],
                                                                      config['data']['input_files']['frenchTerminoUMLS2019AB']))
    symptoms_output_file = os.path.abspath(os.path.join(config['data']['output_dir'],
                                                        config['data']['output_files']['symptomes_neo4j']))
    os.makedirs(config['data']['output_dir'], exist_ok=True)

    wikidata_sparql_endpoint = config['sources']['wikidata']['sparql']


    if os.path.exists(symptoms_output_file):
        logger.error(f"output file {symptoms_output_file} exists, stopping")
        exit(-1)

    try:

        #########################
        # récupération de couples PMSI - symptomes
        #########################
        logger.debug(f'Querying wikidata to get diseases <-> symptoms links')
        server = sparql.SPARQLServer(wikidata_sparql_endpoint)

        # Query to retrieve links between disease and symptoms from Wikidata
        # keep Wikidata URIs
        sparql_query_disease_symptoms = """ SELECT ?disease ?wikidata ?prefLabel
                                            WHERE 
                                            {
                                              ?disease wdt:P31 wd:Q12136 ;  # disease est une maladie
                                                    wdt:P780 ?wikidata . # disease a pour symptome (code wikidata)
                                              ?wikidata rdfs:label ?prefLabel; # symptome a pour label
                                              FILTER (lang(?prefLabel) = 'fr') # filtre langue symptome
                                            }"""

        endpoint_results = server.query(sparql_query_disease_symptoms)
        endpoint_data = endpoint_results["results"]["bindings"]

        # stock the results to a data frame
        symptoms = pd.DataFrame(columns=['diseaseWikidata', 'prefLabel', 'wikidata'])

        for elt in endpoint_data:
            symptoms = symptoms.append({'diseaseWikidata': elt['disease']['value'].split('/')[-1],
                                        'prefLabel': elt['prefLabel']['value'],
                                        'wikidata': elt['wikidata']['value'].split('/')[-1]},
                                       ignore_index=True)

        #######################
        # récupération dans wikidata des codes CUI par code wikidata des symptomes)
        #######################
        logger.debug(f'Querying wikidata to get CUI codes for symptoms')
        # Symptoms and their CUIs:
        sparql_query_symptoms_cui = """ SELECT distinct ?symptom ?CUI
                                        WHERE 
                                        {
                                          ?disease wdt:P31 wd:Q12136 ;  # disease est une maladie
                                                   wdt:P780 ?symptom . # disease a pour symptome
                                          ?symptom wdt:P2892 ?CUI # symptome a un ou plusieurs CUIs
                                        }"""

        endpoint_results = server.query(sparql_query_symptoms_cui)
        endpoint_data = endpoint_results["results"]["bindings"]

        # create a dict to map every wikidata code for a symptom to its CUI
        symptoms_cui_dict = dict()
        for elt in endpoint_data:
            wiki = elt['symptom']['value'].split('/')[-1]
            if wiki in symptoms_cui_dict.keys():
                symptoms_cui_dict[wiki].append(elt['CUI']['value'])
            else:
                symptoms_cui_dict[wiki] = [elt['CUI']['value']]

        # add the CUIs to the data frame
        symptoms['CUI'] = symptoms['wikidata'].map(symptoms_cui_dict)


        ############################
        # lecture du fichier *frenchTerminoUMLS2019AB.csv* qui liste des synonymes pour tous types de concepts, par code CUI
        # on ne garde que les synonymes des symptômes
        ############################

        logger.debug(f'adding symptom synonyms using file {frenchTerminoUMLS2019AB_input_file}')
        # Symptoms and their synonyms:

        # use the 'frenchTerminoUMLS2019AB.csv' file to match the symptoms with their synonyms
        umls = pd.read_csv(frenchTerminoUMLS2019AB_input_file, sep='\t')

        # create a dictionary with the CUI as key and the libelles as value
        synonyms_dict = umls.groupby('CUI')['libelle'].apply(list).to_dict()

        # to lowercase and delete duplicates
        for k in synonyms_dict.keys():
            synonyms_dict[k] = [v.lower() for v in synonyms_dict[k]]
            synonyms_dict[k] = list(set(synonyms_dict[k]))

        # create a column for the synonyms in the df
        symptoms['synonyms'] = '[]'

        # fill the column with the synonyms
        for idx, row in symptoms.iterrows():
            # do not consider nan values
            if type(row['CUI']) == list:
                synonyms = []
                for cui in row['CUI']:
                    if cui in synonyms_dict.keys():
                        synonyms += synonyms_dict[cui]
                symptoms.at[idx, 'synonyms'] = synonyms

        # add weights according to the number of appearances of a symptom in the links
        # a symptom that appears in many diseases has a low weight, a symptom that appears once or twice has a higher weight
        symptoms_counts = symptoms['wikidata'].value_counts().to_dict()
        symptoms_weights = {k: float("{:.3f}".format(1 / v)) for k, v in symptoms_counts.items()}
        symptoms['weight'] = symptoms['wikidata'].map(symptoms_weights)

        # replace empty lists with n/a
        symptoms['synonyms'] = symptoms['synonyms'].replace('[]', 'n/a')

        # replace nan values with empty strings
        symptoms.fillna('n/a', inplace=True)

        # save to csv file
        logger.debug(f'saving to {symptoms_output_file}')
        symptoms.to_csv(Path(symptoms_output_file), sep="\t", index=False)

        logging.info(f"Done!")
        exit(0)

    except Exception as e:
        logger.error(f'Something happened : {str(e)}')
        exit(-1)


if __name__ == "__main__":
    main()