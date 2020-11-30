import pandas as pd
from pathlib import Path
import yaml
import os
import logging.config
import json


def main():
    """
    Ce script:
        - récupère les données qui ont été scrappées / récupérées auparavant

            - diseases.csv
            - symptoms.csv
            - specialties.csv
            - drugs.csv
            - mapping_wiki_icd10.csv

        - enrichit les diseases avec des codes wikidata scrappés dans mapping_wiki_icd10 (merge sur ICD10)
    """

    log_config_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'logging.ini')
    logging.config.fileConfig(log_config_file)
    logger = logging.getLogger(os.path.basename(__file__))
    logger.info('Starting')

    with open('config.yaml') as f:
        config = yaml.safe_load(f)

    diseases_file = os.path.abspath(os.path.join(config['data']['output_dir'],
                                                 config['data']['output_files']['maladies']))
    symptoms_file = os.path.abspath(os.path.join(config['data']['output_dir'],
                                                 config['data']['output_files']['symptomes_neo4j']))
    specialties_file = os.path.abspath(os.path.join(config['data']['output_dir'],
                                                    config['data']['output_files']['specialites_neo4j']))
    drugs_file = os.path.abspath(os.path.join(config['data']['output_dir'],
                                              config['data']['output_files']['medicaments']))
    mapping_file = os.path.abspath(os.path.join(config['data']['output_dir'],
                                                config['data']['output_files']['mapping_wiki_icd10']))
    abbreviation_file = os.path.abspath(os.path.join(config['data']['output_dir'],
                                                     config['data']['output_files']['abbreviations']))

    diseases_output_file = os.path.abspath(os.path.join(config['data']['output_dir'],
                                                        config['data']['output_files']['maladies_neo4j']))

    if os.path.exists(diseases_output_file):
        logger.error(f"output file {diseases_output_file} exists, stopping")
        exit(-1)

    try:

        # read csv files
        logger.debug(f'Loading files')
        diseases = pd.read_csv(diseases_file, sep='\t')
        symptoms = pd.read_csv(symptoms_file, sep='\t')
        specialties = pd.read_csv(specialties_file, sep='\t')
        drugs = pd.read_csv(drugs_file, sep='\t')
        mapping_wikicode_ICD10_1_n = pd.read_csv(mapping_file, sep='\t')
        with open(Path(abbreviation_file)) as json_file:
            abbreviations = json.load(json_file)

        logger.debug(f'Formatting data')
        # since the icd10 column is stored as a list and pandas can not read it as list, we have to change the type manually
        mapping_wikicode_ICD10_1_n['icd10'] = mapping_wikicode_ICD10_1_n['icd10'].apply(lambda x: x.strip("][").replace("'", "").split(', '))

        # A lot of rows do not contain values for an ICD10 code, so drop those rows
        mapping_wikicode_ICD10_1_n = mapping_wikicode_ICD10_1_n[mapping_wikicode_ICD10_1_n.astype(str)['icd10'] != '[]']
        mapping_wikicode_ICD10_1_n.reset_index(drop=True, inplace=True)

        # delete duplicates from the icd10 column
        mapping_wikicode_ICD10_1_n['icd10'] = mapping_wikicode_ICD10_1_n['icd10'].apply(lambda x: list(set(x)))

        # put each icd10 code on a separate row
        s = mapping_wikicode_ICD10_1_n.apply(lambda x: pd.Series(x['icd10']), axis=1).stack().reset_index(level=1, drop=True)
        s.name = 'icd10'
        mapping_wikicode_ICD10_1_1 = mapping_wikicode_ICD10_1_n.drop('icd10', axis=1).join(s)
        mapping_wikicode_ICD10_1_1['icd10'] = pd.Series(mapping_wikicode_ICD10_1_1['icd10'], dtype=object)
        mapping_wikicode_ICD10_1_1.reset_index(inplace=True, drop=True)

        # Now, each row of the mapping dataframe contains a wikidata code and an ICD10 code
        # However, there is still somme changes too make

        # drop rows where the value in the column 'icd10' contains ('-')
        idx = mapping_wikicode_ICD10_1_1[mapping_wikicode_ICD10_1_1['icd10'].str.contains('-')].index
        mapping_wikicode_ICD10_1_1.drop(idx, inplace=True)
        mapping_wikicode_ICD10_1_1.reset_index(inplace=True, drop=True)

        # drop rows where the column 'icd10' is in the wrong format (all numbers)
        idx = mapping_wikicode_ICD10_1_1[mapping_wikicode_ICD10_1_1['icd10'].str.isnumeric()].index
        mapping_wikicode_ICD10_1_1.drop(idx, inplace=True)
        mapping_wikicode_ICD10_1_1.reset_index(inplace=True, drop=True)

        # use the code only, not the entire URI
        mapping_wikicode_ICD10_1_1['wikidata'] = mapping_wikicode_ICD10_1_1['wikidata'].apply(lambda x: x.split('/')[-1])

        # one more step : drop the rows if the wikidata data code is not in all_wiki
        # THIS IS DONE TO FACILITATE FOLLOWING MATCHING BY REMOVING ALL WIKI CODES THAT ARE NOT IN THE REST OF THE DATA
        all_wiki = set(list(drugs['diseaseUri'].unique()) + list(specialties['diseaseWikidata'].unique()) + list(symptoms['diseaseWikidata'].unique()))
        mapping_wikicode_ICD10_1_1 = mapping_wikicode_ICD10_1_1[mapping_wikicode_ICD10_1_1['wikidata'].isin(all_wiki)]

        # create a dict that has ICD10 codes as keys and wikidata codes as values
        map_dict = pd.Series(mapping_wikicode_ICD10_1_1.wikidata.values, index=mapping_wikicode_ICD10_1_1.icd10).to_dict()

        logger.debug(f'Merging diseases')
        # separate the diseases dataframe into 2, according to the value of the 'wikidata' column
        diseases_pos = diseases[diseases.Wikidata.notnull()].copy()
        diseases_neg = diseases[diseases.Wikidata.isnull()].copy()

        diseases_neg['Wikidata'] = diseases_neg['ICD10'].map(map_dict)
        final_diseases = pd.concat([diseases_neg, diseases_pos], ignore_index=True)

        logger.debug(f"Adding abbreviations")
        # add abbreviations
        final_diseases['abbreviation'] = final_diseases['ICD10'].map(abbreviations)

        # replace nan values with n/a
        final_diseases.fillna('n/a', inplace=True)

        # save to csv file
        logger.debug(f'Saving to {diseases_output_file}')
        final_diseases.to_csv(Path(diseases_output_file), sep="\t", index=False)

        logging.info(f"Done!")
        exit(0)

    except Exception as e:
        logger.error(f'Something happened : {str(e)}')
        exit(-1)


if __name__ == "__main__":
    main()

