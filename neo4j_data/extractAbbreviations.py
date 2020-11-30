import requests
from bs4 import BeautifulSoup
from pathlib import Path
import yaml
import logging.config
import os
import json


def main():
    """
    A script that :

        - looks into this wikipedia page : 'https://fr.wikipedia.org/wiki/Liste_d%27abr%C3%A9viations_en_m%C3%A9decine'
          in order to extract the abbreviations of medical terms (diseases for now).
        - gets the wikidata codes associated to these concepts
        - gets the ICD10 codes associated to these wikidata codes
        - saves the results to a json file *abbreviations.json*
    """

    logging.config.fileConfig('logging.ini')
    logger = logging.getLogger(os.path.basename(__file__))
    logger.info('Starting')


    logger.debug('Loading config')
    with open('config.yaml') as f:
        config = yaml.safe_load(f)

    abbreviations_output_file = os.path.abspath(os.path.join(config['data']['output_dir'],
                                                             config['data']['output_files']['abbreviations']))
    os.makedirs(config['data']['output_dir'], exist_ok=True)

    main_wikidata_url = config['sources']['wikidata']['main_url']
    main_wikipedia_url = config['sources']['wikipedia']['main_url']
    abbreviation_page_url = config['sources']['wikipedia']['abb_url']

    if os.path.exists(abbreviations_output_file):
        logger.error(f"output file {abbreviations_output_file} exists, stopping")
        exit(-1)

    try:

        #################################################################
        # get the abbreviation, the concept name and its wikipedia link #
        #################################################################
        logger.debug(f"Scraping the wikipedia page for abbreviations of medical terms.")

        abbreviation_page = requests.get(abbreviation_page_url)

        soup = BeautifulSoup(abbreviation_page.content, 'html.parser')

        counter = 0
        abb_dict = dict()

        for ultag in soup.find_all('ul'):
            for litag in ultag.find_all('li'):
                # some links are not from wikipedia, that's why we condition on the first part of the link
                if litag.a and litag.a['href'][:5] == '/wiki':
                    abb_dict[litag.text.split(':')[0].replace(u'\xa0', '')] = list((litag.a.text, litag.a['href']))

            counter += 1

            # exit the loop when reaching the last letter
            if counter == 26:
                break

        ##########################################################
        # get the wikidata code associated to each concept found #
        ##########################################################

        logger.debug(f"Getting the wikidata codes of each concept")
        logger.info('Total iterations : ' + str(len(abb_dict)))
        for i, (k, v) in enumerate(abb_dict.items()):
            try:
                wikipedia_page_url = v[1]
                wikipedia_page = requests.get(main_wikipedia_url + wikipedia_page_url)
                soup = BeautifulSoup(wikipedia_page.content, 'html.parser')
                if soup.find(id='t-wikibase') is not None:
                    wikidata_code = soup.find(id='t-wikibase').a['href'].split('/')[-1]
                    abb_dict[k][1] = wikidata_code
                if i % 100 == 0:
                    logger.info(str(i) + ' iterations done !')
            except :
                continue

        ##################################################################################################################
        # scrape wikidata using the wikidata codes in order to get the ICD10 codes and match them with tha abbreviations #
        ##################################################################################################################

        logger.debug(f"Scraping each wikidata page of each concept found to extract the ICD10 code(s) associated")

        # the dictionary that will contain the mapping ICD10 <-> Abbreviation
        icd_abb_dict = dict()

        logger.info('Total iterations : ' + str(len(abb_dict)))

        for i, (k, v) in enumerate(abb_dict.items()):
            try:
                wikidataURL = (main_wikidata_url + v[1])
                page = requests.get(wikidataURL)
                soup = BeautifulSoup(page.content, 'html.parser')

                # store the ICD10 in a list
                icd10 = []
                for elt in soup.find_all('a', class_='wb-external-id external'):
                    if 'icd.who' in elt['href']:
                        icd10.append(elt['href'].split('/')[-1])
                    if 'icdcodelookup' in elt['href']:
                        icd10.append(elt['href'].split('/')[-1])

                # remove duplicates
                icd10 = list(set(icd10))

                # fill the dictionary with the ICD10 as keys and the abbreviation(s) as values
                for c in icd10:
                    if c not in icd_abb_dict.keys():
                        icd_abb_dict[c] = []
                    icd_abb_dict[c].append(k)

                if i % 100 == 0:
                    logger.info(str(i) + ' iterations done !')
            except :
                continue

        # save to json file
        logger.debug(f"Saving to {abbreviations_output_file}")
        with open(Path(abbreviations_output_file), 'w') as outfile:
            json.dump(icd_abb_dict, outfile)

        logging.info(f"Done!")
        exit(0)

    except Exception as e:
        logger.error(f'Something happened : {str(e)}')
        exit(-1)


if __name__ == "__main__":
    main()