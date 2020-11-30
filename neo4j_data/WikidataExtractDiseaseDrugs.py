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

    - va récupérer dans wikidata les liens entre maladies et molécules (par codes wikidata + drugLabel)
      (pas de croisement avec les PMSI connus)

    - sauvegarde dans *wiki-DiseaseDrugs-21072020.tsv*

    - récupération via Romedi de RomediUri:
      -> on teste (et donc potentiellement on récupère) Ingrédients, Brand Names, Drug Classes

    - on sauvegarde dans *wiki-DrugsLabelsMapping.tsv*

    - on récupère via Romedi (romediURL:

        - ucd (uri Romedi),
        - cis
        - IN, inlabel
        - bn, bnlabel, ucd13, nimed,
        - drugclass, drugclasslabel

    - sauvegarde dans *drugs.csv*

    """

    log_config_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'logging.ini')
    logging.config.fileConfig(log_config_file)
    logger = logging.getLogger(os.path.basename(__file__))
    logger.info('Starting')

    with open('config.yaml') as f:
        config = yaml.safe_load(f)

    wiki_disease_drugs_output_file = os.path.abspath(os.path.join(config['data']['output_dir'],
                                                                  'wiki-DiseaseDrugs-21072020.tsv'))
    wiki_DrugsLabelsMapping_output_file = os.path.abspath(os.path.join(config['data']['output_dir'],
                                                                       'wiki-DrugsLabelsMapping-21072020.tsv'))
    drugs_output_file = os.path.abspath(os.path.join(config['data']['output_dir'],
                                                     config['data']['output_files']['medicaments']))
    os.makedirs(config['data']['output_dir'], exist_ok=True)

    wikidata_sparql_endpoint = config['sources']['wikidata']['sparql']
    romedi_sparql_endpoint = config['sources']['romedi']['sparql']
    romedi_api_url = config['sources']['romedi']['api']


    if os.path.exists(drugs_output_file):
        logger.error(f"output file {drugs_output_file} exists, stopping")
        exit(-1)

    try:


        ########################
        # Récupération des liens maladies / molécules (par codes wikidata + drugLabel)
        ########################
        logger.debug(f'Querying wikidata to get diseases <-> molecules links')
        server = sparql.SPARQLServer(wikidata_sparql_endpoint)

        # Query to retrieve links between disease and drugs from Wikidata
        # with the French labels of each drug
        sparql_query_disease_drug = """SELECT ?disease ?drug ?drugLabel
            WHERE 
            {
              ?disease wdt:P31 wd:Q12136 ;  # disease est une maladie
              wdt:P2176 ?drug . # disease a pour medicament
              ?drug rdfs:label ?drugLabel # medicament a pour label
              FILTER (lang(?drugLabel) = 'fr') # filtre langue FR label
        }"""

        endpoint_results = server.query(sparql_query_disease_drug)
        endpoint_data = endpoint_results["results"]["bindings"]

        # extract the 3 columns:
        diseases_wiki_uri = [x["disease"]["value"] for x in endpoint_data]
        drugs_wiki_uri = [x["drug"]["value"] for x in endpoint_data]
        drugs_wiki_label = [x["drugLabel"]["value"] for x in endpoint_data]
        diseaseDrugsRel = zip(diseases_wiki_uri, drugs_wiki_uri, drugs_wiki_label)

        # write results to file
        logger.debug(f'saving to {wiki_disease_drugs_output_file}')
        with open(Path(wiki_disease_drugs_output_file), 'w') as outFile:
            outFile.write(f'diseaseUri\tdrugUri\tdrugLabel\n')
            for row in diseaseDrugsRel:
                (diseaseUri, drugUri, drugLabel) = row
                outFile.write(f'{diseaseUri}\t{drugUri}\t{drugLabel}\n')

        # test load
        test = pd.read_csv(wiki_disease_drugs_output_file, sep="\t")
        test.shape == (4303, 3)


        ########################### Mappings to Romedi ######################
        ## add Romedi URI to each drug label to link it to the metadata
        #####################################################################

        from neo4j_data.RomediAPI import RomediAPI  # local import

        logger.debug(f'Querying Romedi to get RomediURI by resource type')
        # romedi website API
        url_detection = romedi_api_url + "GetJSONdrugsDetected"
        url_detection_by_type = romedi_api_url + "GetJSONdrugDetectedByType"
        romediAPI = RomediAPI(url_detection=url_detection,
                              url_detection_by_type=url_detection_by_type)
        romediAPI.detect_drug_by_type("ethambutol", "IN")  ## test API

        # unique drugs labels :
        drugsLabels = list(set(drugs_wiki_label))
        len(drugsLabels)  # number of labels to map to Romedi URI (1099)
        drugLabel = drugsLabels[0]
        mappings = dict()

        # map on ingredients
        logger.debug(f'testing ingredients')
        for drugLabel in drugsLabels:
            try:
                detection = romediAPI.detect_drug_by_type(drugLabel, "IN")
                if len(detection.keys()) == 0:
                    continue
                code = detection["0"]["code"]
                terminoLabel = detection["0"]["terminoLabel"]
                mappings[drugLabel] = (code, terminoLabel)
            except :
                continue
        len(mappings)  # number of labels successfully mapped by IN (765)

        # map on brand name
        logger.debug(f'testing brand names')
        for drugLabel in drugsLabels:
            try:
                if drugLabel in mappings.keys():  # if already mapped
                    continue
                detection = romediAPI.detect_drug_by_type(drugLabel, "BN")
                if len(detection.keys()) == 0:
                    continue
                code = detection["0"]["code"]
                terminoLabel = detection["0"]["terminoLabel"]
                mappings[drugLabel] = (code, terminoLabel)
            except :
                continue
        len(mappings)  # number of labels successfully mapped by IN, BN (775)

        # map on DrugClass
        logger.debug(f'testing drug classes')
        for drugLabel in drugsLabels:
            try:
                if drugLabel in mappings.keys():  # if already mapped
                    continue
                detection = romediAPI.detect_drug_by_type(drugLabel, "DrugClass")
                if len(detection.keys()) == 0:
                    continue
                code = detection["0"]["code"]
                terminoLabel = detection["0"]["terminoLabel"]
                mappings[drugLabel] = (code, terminoLabel)
            except:
                continue
        len(mappings)  # number of labels successfully mapped by IN, BN (776)

        # all terms not mapped:
        """
        for drugLabel in drugsLabels:
            if drugLabel not in mappings.keys():  # if already mapped
                print(drugLabel)
        """

        # write results to file
        logger.debug(f'saving to {wiki_DrugsLabelsMapping_output_file}')
        with open(Path(wiki_DrugsLabelsMapping_output_file), 'w') as outFile:
            outFile.write(f'DrugsLabels\tRomediURI\n')
            for drugLabel in mappings.keys():
                (RomediURI, RomediLabel) = mappings[drugLabel]
                outFile.write(f'{drugLabel}\t{RomediURI}\n')


        # add properties to the drugs found
        logger.debug(f'Querying Romedi to get resource characteristics')
        drugs = test.copy()
        romediURI = pd.read_csv(wiki_DrugsLabelsMapping_output_file, sep='\t')

        # merge the 2 data frames
        drugs_romedi = pd.merge(drugs, romediURI, left_on='drugLabel', right_on='DrugsLabels', how='left')

        # drop the 'DrugsLabels' column
        drugs_romedi.drop(columns=['DrugsLabels'], inplace=True)

        # keep only the wikidata code (not the entire URI)
        drugs_romedi['diseaseUri'] = drugs_romedi['diseaseUri'].apply(lambda x: x.split("/")[-1])
        drugs_romedi['drugUri'] = drugs_romedi['drugUri'].apply(lambda x: x.split("/")[-1])

        # extract the drugs characteristics (cis, in, bn ...)
        romedi_server = sparql.SPARQLServer(romedi_sparql_endpoint)

        # the query to extract the data from the romedi server
        query = """
                PREFIX romedi:<http://www.romedi.fr/romedi/>
                select ?UCD ?UCD13 ?NIMED ?CIS ?CISlabel ?IN ?INlabel ?BN ?BNlabel ?drugClass ?drugClassLabel where {
                ?UCD a romedi:UCD13 .
                ?UCD romedi:hasUCD13 ?UCD13 .
                ?CIS romedi:CIShasUCD13 ?UCD . 
                ?CIS rdfs:label ?CISlabel .
                ?CIS romedi:CIShasBNdosage ?BNdosage .
                ?BNdosage romedi:BNdosagehasBN ?BN .
                ?BN rdfs:label ?BNlabel .
                ?CIS romedi:CIShasPINdosage ?PINdosage .
                ?PINdosage romedi:PINdosagehasINdosage ?INdosage .
                ?INdosage romedi:INdosagehasIN ?IN .
                ?IN rdfs:label ?INlabel.
                ?UCD romedi:hasNIMED ?NIMED.
                ?CIS romedi:CIShasDrugClass ?drugClass . ?drugClass rdfs:label ?drugClassLabel
                }
                """

        endpoint_results = romedi_server.query(query)
        endpoint_data = endpoint_results["results"]["bindings"]

        # put the results into lists to facilitate their transformation to a data frame
        ucd = [x["UCD"]["value"] for x in endpoint_data]
        ucd13 = [x["UCD13"]["value"] for x in endpoint_data]
        nimed = [x["NIMED"]["value"] for x in endpoint_data]
        cis = [x["CIS"]["value"] for x in endpoint_data]
        cisLabel = [x["CISlabel"]["value"] for x in endpoint_data]
        IN = [x["IN"]["value"] for x in endpoint_data]
        inlabel = [x["INlabel"]["value"] for x in endpoint_data]
        bn = [x["BN"]["value"] for x in endpoint_data]
        bnlabel = [x["BNlabel"]["value"] for x in endpoint_data]
        drugclass = [x["drugClass"]["value"] for x in endpoint_data]
        drugclasslabel = [x["drugClassLabel"]["value"] for x in endpoint_data]

        zippedList = list(zip(ucd, ucd13, nimed, cis, cisLabel, IN, inlabel, bn, bnlabel, drugclass, drugclasslabel))

        # create a data frame with all the drugs' characteristics
        drugsCarac = pd.DataFrame(zippedList, columns=['UCD', 'UCD13', 'NIMED', 'CIS', 'CISLabel', 'IN', 'INlabel', 'BN',
                                                       'BNlabel', 'drugClass', 'drugClassLabel'])

        # merge the characteristics with the first table (containing the diseases and their associated drugs)
        final_df = pd.merge(drugs_romedi, drugsCarac, left_on='RomediURI', right_on='IN', how='left')

        # drop duplicates and rows with nan values
        final_df.drop_duplicates(inplace=True)
        final_df.dropna(inplace=True)

        # save to csv file
        logger.debug(f'saving to {drugs_output_file}')
        final_df.to_csv(Path(drugs_output_file), sep="\t", index=False)

        logging.info(f"Done!")
        exit(0)

    except Exception as e:
        logger.error(f'Something happened : {str(e)}')
        exit(-1)


if __name__ == "__main__":
    main()