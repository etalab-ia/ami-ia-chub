from ia import get_data_from_csv
from ia import get_data_from_bg
from ia.final_ann_dict import merge, clean
from ia.preprocess_obs import preprocess
from ia import spacy_ner_modeling
import random

import pymantic.sparql as sparql
import pandas as pd
import spacy
from pathlib import Path


def main():
    """
    Main script for training a NER model

    saves it in spacy_NER_models/

    :return: None
    """
    # get data from the csv files
    csv_dict = get_data_from_csv.get_data()

    # get data from the blazegraph
    server = sparql.SPARQLServer('http://localhost:8888/sparql-endpoint')
    bg_dict = get_data_from_bg.get_data(server)

    # merge the 2 annotations dictionaries
    ann_dict = merge(bg_dict, csv_dict)
    ann_dict = clean(ann_dict)
    print('Annotation dictionary constructed and pre-processed !')

    # read the DPI file
    dpi = pd.read_csv('../data/ia/dpi.csv', sep='|')
    print('DPI loaded !')
    
    print(dpi.SOURCESYSTEM_CD.unique())
    # CHU_BORDEAUX_QUESTIONNAIRES_DXC: DxCare forms (some responses are free text)
    # SRV_DOC: discharge summaries... (free text)
    # SRV_IMAGERIE: radiological reports (free text)
    # SYNERGIE: bacteriology (structured)
    # TRACELINE: blood transfusion (structured)
    # DXCARE_PRESCRIPTION: drug prescription (structured)
    # DXCARE-PMSI: billing codes (structured)
    
    dpi_tmp = dpi.loc[dpi['SOURCESYSTEM_CD'].isin(["SRV_DOC",
                                                         "SRV_IMAGERIE",
                                                         "CHU_BORDEAUX_QUESTIONNAIRES_DXC"])]
    
    ## Remove structured responses from DxCare responses:
    bool_response = dpi_tmp.CONCEPT_CD.str.contains('^DXC\\|REPONSE')
    dpi_free_text = dpi_tmp[~bool_response] # CONCEPT_CD doesn't start by DXC|REPONSE
    
    # extract the OBSERVATION_BLOB and TVAL_CHAR columns which contain the free text written by health professionnals
    obs_blob = list(dpi_free_text['OBSERVATION_BLOB'])
    tval_char = list(dpi_free_text['TVAL_CHAR'])
    texts = obs_blob + tval_char

    # pre-process the texts
    clean_texts = preprocess(texts)
    print('Observations extracted and cleaned !')

    #############################
    # Annotation for data frame #
    #############################

    # Create a blank model
    #nlp = spacy.blank('fr')

    # Create the SpaCy PhraseMatcher
    #matcher = annotation_for_df.create_matcher(nlp, ann_dict)

    # Tag the texts and fix the tags
    #tags = annotation_for_df.tag_texts(nlp, matcher, clean_texts)
    #final_tags = annotation_for_df.fix_tags(tags)

    # Create data frame
    #df = dataframe.create(clean_texts, nlp)

    # Fill the tags column
    #df = dataframe.fill_tags_column(df, final_tags)

    # Fill the NaN values with 'O' as we are going to use the BIO method
    #df['Tag'].fillna('O', inplace=True)

    # Fill the BIO_Tags column
    #df['BIO_tags'] = dataframe.bio_tagging(list(df['Tag']))

    #####################################
    # Annotation for SpaCy NER modeling #
    #####################################

    # Create a blank model
    nlp = spacy.blank('fr')

    # Create the SpaCy PhraseMatcher
    matcher = spacy_ner_modeling.create_matcher(nlp, ann_dict)

    # Tag the texts and fix the tags
    tags = spacy_ner_modeling.tag_texts(nlp, matcher, clean_texts)
    final_tags = spacy_ner_modeling.fix_tags(tags)

    # Put the texts into the right format for the spacy NER modeling
    data = spacy_ner_modeling.format_data_4_spacy_ner_modeling(clean_texts, final_tags)

    # Remove observations that do not contain any tags
    DATA = spacy_ner_modeling.filter_data(data)

    # Train SpaCy models

    # Shuffle data
    random.shuffle(DATA)

    # Split data into train and test
    cut = int(0.7 * len(DATA))
    DATA_TRAIN_SPACY = DATA[:cut]
    DATA_TEST_SPACY = DATA[cut:]

    # Change the values of the number of iterations and drop-out rate
    iterations_list = [20, 30, 40, 50]
    dropout_list = [0.1, 0.2, 0.3]

    for iteration in iterations_list:
        for dropout in dropout_list:
            print('#########################')
            print('Number of iterations :', iteration)
            print('Drop-out rate :', dropout)
            print('#########################')

            # Train model
            prdnlp = spacy_ner_modeling.train_spacy(data=DATA_TRAIN_SPACY, iterations=iteration, drop_rate=dropout)

            # Set model name and directory
            model_name = 'spacy_NER_model_nIter_' + str(iteration) + '_drop_' + str(dropout).replace('.', '')
            models_dir = 'spacy_NER_models/'
            model_dir = models_dir + model_name
            model_dir = Path(model_dir)
            if not model_dir.exists():
                model_dir.mkdir(parents=True)
            prdnlp.meta['name'] = model_name

            # Save model
            prdnlp.to_disk(model_dir)
            print('\nModel saved to ', model_dir)
            print()

            # Evaluate model
            print('Evaluating model with SpaCy default scorer')
            # On train set
            print('\n= On train set :')
            train_spacy_scorer = spacy_ner_modeling.evaluate_model_spacy_scorer(prdnlp, DATA_TRAIN_SPACY)
            # On test set
            print('\n= On test set :')
            test_spacy_scorer = spacy_ner_modeling.evaluate_model_spacy_scorer(prdnlp, DATA_TEST_SPACY)


if __name__ == "__main__":
    main()
