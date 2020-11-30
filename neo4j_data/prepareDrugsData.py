from pathlib import Path
import pandas as pd
import os
import yaml
import logging.config


def main():
    """
    This script will process the 'drugs.csv' in order to extract several files for integration into neo4j.
    The reason for not using 'drugs.csv' directly is that neo4j is not able to distinguish if the node already exists or not
    And we have multiple duplicates in our case.

    Generates :
        - medoc.csv
        - drugclass.csv
        - ingredient.csv
        - brand_name.csv
    """

    log_config_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'logging.ini')
    logging.config.fileConfig(log_config_file)
    logger = logging.getLogger(os.path.basename(__file__))
    logger.info('Starting')

    with open('config.yaml') as f:
        config = yaml.safe_load(f)

    drugs_file = os.path.abspath(os.path.join(config['data']['output_dir'],
                                              config['data']['output_files']['medicaments']))

    medoc_output_file = os.path.abspath(os.path.join(config['data']['output_dir'],
                                                     config['data']['output_files']['medicaments_neo4j']))
    drugclass_output_file = os.path.abspath(os.path.join(config['data']['output_dir'],
                                                         config['data']['output_files']['classes_therapeutiques_neo4j']))
    ingredient_output_file = os.path.abspath(os.path.join(config['data']['output_dir'],
                                                          config['data']['output_files']['molecules_neo4j']))
    brand_name_output_file = os.path.abspath(os.path.join(config['data']['output_dir'],
                                                          config['data']['output_files']['noms_commerciaux_neo4j']))

    if any(os.path.exists(f) for f in [medoc_output_file, drugclass_output_file, ingredient_output_file, brand_name_output_file]):
        logger.error(f"at least one output file exists, stopping")
        exit(-1)

    try:

        # read the drugs csv file
        logger.debug(f'loading {drugs_file}')
        drugs = pd.read_csv(drugs_file, sep='\t')

        # shorten the CIS for better visualization
        drugs['CIS'] = drugs['CIS'].apply(lambda x: x.split('/')[-1])

        # the 'Medicament' nodes
        logger.debug(f'processing Medoc')
        # the attributes that we are keeping for the 'Medicament' node are : diseaseUri, CIS and CISLabel
        medoc = drugs[['diseaseUri', 'CIS', 'CISLabel']].copy()

        # drop the duplicates
        medoc.drop_duplicates(inplace=True)


        # save to csv file
        logger.debug(f'saving to {medoc_output_file}')
        medoc.to_csv(Path(medoc_output_file), sep="\t", index=False)


        # the 'Classe thérapeutique' nodes (drug class)
        logger.debug(f'processing drug classes')
        # the attributes that we are keeping are : drugUri, drugLabel, RomediURI, CIS, drugClass and drugClassLabel
        drugclass = drugs[['CIS', 'CISLabel', 'drugClass', 'drugClassLabel']].copy()

        # drop the duplicates
        drugclass.drop_duplicates(inplace=True)

        # save to csv file
        logger.debug(f'saving to {drugclass_output_file}')
        drugclass.to_csv(Path(drugclass_output_file), sep="\t", index=False)


        # the 'Ingredient' nodes (IN)
        logger.debug(f'processing ingredients')
        # the attributes that we are keeping are : drugUri, drugLabel, RomediURI, CIS, IN and INlabel
        ingredient = drugs[['CIS', 'CISLabel', 'IN', 'INlabel', 'drugUri']].copy()

        # drop the duplicates
        ingredient.drop_duplicates(inplace=True)

        # save to csv file
        logger.debug(f'saving to {ingredient_output_file}')
        ingredient.to_csv(Path(ingredient_output_file), sep="\t", index=False)


        # the 'Nom commercial' nodes (BN : Brand Name)
        logger.debug(f'processing brand names')
        # the attributes that we are keeping are : drugUri, drugLabel, RomediURI, CIS, BN, BNlabel, NIMED and UCD13
        brand_name = drugs[['CIS', 'CISLabel', 'BN', 'BNlabel', 'NIMED', 'UCD13']].copy()

        # drop the duplicates
        brand_name.drop_duplicates(inplace=True)

        # save to csv file
        logger.debug(f'saving to {brand_name_output_file}')
        brand_name.to_csv(Path(brand_name_output_file), sep="\t", index=False)

        logging.info(f"Done!")
        exit(0)

    except Exception as e:
        logger.error(f'Something happened : {str(e)}')
        exit(-1)


if __name__ == "__main__":
    main()