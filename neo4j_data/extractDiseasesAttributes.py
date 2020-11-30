import pymantic.sparql as sparql
import pandas as pd
from pathlib import Path
import os
import yaml
import logging.config


def main():
    """
    Script qui :
        - va récupérer dans les métadonnées les codes (ICD10, PMSI)
        - va récupérer dans les métadonnées les noms des maladies par le code ICD10
        - va récupérer les codes wikidata et UMLS à partir du code ICD10
        - sauvegarde dans *diseases.csv*
    """

    log_config_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'logging.ini')
    logging.config.fileConfig(log_config_file)
    logger = logging.getLogger(os.path.basename(__file__))
    logger.info('Starting')


    with open('config.yaml') as f:
        config = yaml.safe_load(f)

    frenchTerminoUMLS2019AB_input_file = os.path.abspath(os.path.join(config['data']['input_dir'],
                                                                      config['data']['input_files']['frenchTerminoUMLS2019AB']))

    diseases_output_file = os.path.abspath(os.path.join(config['data']['output_dir'],
                                                        config['data']['output_files']['maladies']))
    os.makedirs(config['data']['output_dir'], exist_ok=True)

    blazegraph_endpoint = config['sources']['chu']['blazegraph']
    wikidata_sparql_endpoint = config['sources']['wikidata']['sparql']


    if os.path.exists(diseases_output_file):
        logger.error(f"output file {diseases_output_file} exists, stopping")
        exit(-1)

    try:

        ###############
        # Récupération ICD10/PMSI
        ###############

        # use the metadata to extract the diseases, their ICD10 codes and their PMSI codes
        logger.debug(f"Querying blazegraph to get couples PMSI <-> ICD10")
        metadata_server = sparql.SPARQLServer(blazegraph_endpoint)

        # query to retrieve links between ICD10 codes and PMSI codes from the blazegraph
        icd_pmsi_query = "SELECT * WHERE {  ?s rdf:type <http://chu-bordeaux.fr/pmsi#diagnosticCode>. \
                                            ?s rdfs:label ?o. \
                                            ?s <http://chu-bordeaux.fr/m2sitis/iso11179-3/mdr.owl#isComponentOf> ?x .\
                                            ?x <http://chu-bordeaux.fr/m2sitis/iso11179-3/mdr.owl#hasTarget> ?y .\
                                            ?y rdfs:label ?l}"
        pmsi_results = metadata_server.query(icd_pmsi_query)

        # stock the results in a data frame
        mapping = pd.DataFrame(columns=['ICD10', 'PMSI'])
        for b in pmsi_results['results']['bindings']:
            mapping = mapping.append({'ICD10': b['o']['value'], 'PMSI': b['l']['value']}, ignore_index=True)

        # correct typos
        mapping['PMSI'] = mapping['PMSI'].str.replace('DIAGNOSIC', 'DIAGNOSTIC')


        ########################
        # Récupération des noms associés aux ICD10
        ########################
        logger.debug(f"Querying blazegraph to get disease labels from ICD10")
        # query to retrieve links between ICD10 codes and the diseases names from the blazegraph
        icd_disease_query = "SELECT * WHERE \
                            {   ?s rdf:type <http://chu-bordeaux.fr/pmsi#diagnosticCode>. \
                                ?s rdfs:label ?x. \
                                ?s <http://chu-bordeaux.fr/m2sitis/iso11179-3/mdr.owl#hasMeaningPermissibleValueMeaning> ?o. \
                                ?o rdfs:label ?l }"
        disease = metadata_server.query(icd_disease_query)

        # create dictionary with ICD10 codes as keys and diseases names as values
        icd_disease_dict = dict()
        for b in disease['results']['bindings']:
            icd_disease_dict[b['x']['value']] = b['l']['value']

        # add diseases names to the data frame
        mapping['diseaseName'] = mapping['ICD10'].map(icd_disease_dict)

        #####################
        # Récupération des codes wikidata et UMLS à partir du code ICD10
        #####################

        logger.debug(f"Querying wikidata to get disease UMLS and wiki codes from ICD10")
        # use Wikidata to extract the UMLS codes and the wikidata codes associated to diseases
        server = sparql.SPARQLServer(wikidata_sparql_endpoint)

        # query to retrieve both wikidata and UMLS codes
        umls_wikidata_codes_query = """SELECT distinct ?disease ?CUI ?ICD10
                                        WHERE
                                        {
                                          ?disease wdt:P31 wd:Q12136 ;  # disease est une maladie
                                               wdt:P494 ?ICD10; # disease a un code ICD10
                                               wdt:P2892 ?CUI # disease a un ou plusieurs CUIs
                                        }"""

        # get the results
        res = server.query(umls_wikidata_codes_query)["results"]["bindings"]

        # create dictionaries with icd10 as keys and wiki codes and umls codes respectively as values
        icd_wiki_dict = dict()
        icd_umls_dict = dict()
        for r in res:
            icd_wiki_dict[r['ICD10']['value']] = r['disease']['value'].split('/')[-1]
            icd_umls_dict[r['ICD10']['value']] = r['CUI']['value']

        # add wiki codes and umls codes to the data frame
        mapping['Wikidata'] = mapping['ICD10'].map(icd_wiki_dict)
        mapping['UMLS'] = mapping['ICD10'].map(icd_umls_dict)

        ######################
        # Ajouter les synonymes des maladies depuis le fichier UMLS
        ######################

        logger.debug(f"Adding synonyms from the UMLS file frenchTerminoUMLS2019AB")

        # read csv file
        french_termino = pd.read_csv(Path(frenchTerminoUMLS2019AB_input_file), sep='\t')

        # UMLS codes in diseases dataframe
        umls_diseases = list(mapping['UMLS'].unique())
        umls_diseases = [elt for elt in umls_diseases if str(elt) != 'nan']

        # from the french_termino dataframe we only keep :
        #  - the rows with the CUI in umls_disease
        #  - the columns 'CUI' and 'libelle'
        #  and we remove duplicates
        sub_umls = french_termino[french_termino['CUI'].isin(umls_diseases)][['CUI', 'libelle']]
        sub_umls.drop_duplicates(inplace=True)
        sub_umls.reset_index(drop=True, inplace=True)

        # exract a dict with CUI as codes and synonyms as values
        synonyms_dict = sub_umls.groupby('CUI')['libelle'].apply(list).to_dict()

        # add the synonyms column
        mapping['synonyms'] = mapping['UMLS'].map(synonyms_dict)

        # replace nan values with 'n/a'
        mapping.fillna('n/a', inplace=True)

        # save to csv file
        logger.debug(f"Saving to {diseases_output_file}")
        mapping.to_csv(Path(diseases_output_file), sep="\t", index=False)

        logging.info(f"Done!")
        exit(0)

    except Exception as e:
        logger.error(f'Something happened : {str(e)}')
        exit(-1)


if __name__ == "__main__":
    main()

