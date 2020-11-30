import pandas as pd
from unidecode import unidecode
import nltk

nltk.download('stopwords')
from nltk.corpus import stopwords
from ia.get_csv_from_db import export_to_df


def clean(text):
    """
    A function to put text into lowercase

    :param text: (string)
    :return: (string) text in lowercase
    """
    text = text.lower()
    text = unidecode(text)
    return text


def clean2(text):
    """
    A second function for cleaning data

    :param text: (string)
    :return: (string)
    """
    text = text.lower()
    text = unidecode(text)
    tokenizer = nltk.RegexpTokenizer(r"\w+")
    stop_words = stopwords.words('french')
    text = " ".join([w for w in tokenizer.tokenize(text) if w not in stop_words])
    return text


def fill_ann_dict_from_diabete(k, col_names, row, ann_dict):
    """
    Add the medical terms from the 'diabete_concepts.csv' file to the annotation dictionary

    :param ann_dict: (dictionary) the annotation dictionary
    :param row: the row of the data frame
    :param k: (string) indicates the key of the dictionary
    :param col_names: (list) the columns names of the data frame
    """
    for col in col_names:
        if col == 'categorie':
            continue
        if row[col] not in ann_dict[k] and not pd.isnull(row[col]):
            ann_dict[k].append(row[col])


def get_data():
    """
    A function to collect the annotation data from the different csv files available

    :return: (dict) with the annotation data
    """

    # The csv files that will be used to extract the medical data
    df_medoc = export_to_df(dbname='ghpsj-v2', table='raw_medicament_cis_atc_mol')
    df_term_medicaux = export_to_df(dbname='ghpsj-v2', table='raw_medical_terms_dictionary_m2osw')

    # Apply the 'clean' function to 'libelle_atc' column of the df_medoc data frame
    df_medoc["libelle_atc"] = df_medoc["libelle_atc"].apply(clean)

    # Delete rows with NaN values from df_term_medicaux
    df_term_medicaux.dropna(inplace=True)
    df_term_medicaux.reset_index(drop=True, inplace=True)

    # Create the annotation dict
    ann_dict = dict()
    ann_dict.setdefault("LIBEL", [])
    ann_dict.setdefault("TRAIT", [])
    ann_dict.setdefault("MAL", [])
    ann_dict.setdefault("EXAM", [])
    ann_dict.setdefault("BIO", [])
    ann_dict.setdefault("SYM", [])

    # Add the terms from the data frame to the dict
    for medoc in df_medoc["libelle_atc"].unique():
        ann_dict["LIBEL"].append(medoc)
    for medoc in df_medoc["med_lib"].unique():
        ann_dict["TRAIT"].append(medoc)

    # Create a column in df_term_medicaux containing only the first word of the column 'definition'
    for index, row in df_term_medicaux.iterrows():
        tr = clean2(df_term_medicaux.loc[index, "definition"])
        df_term_medicaux.loc[index, "mot"] = tr.split(" ")[0]
        del tr

    # Add the diseases, drugs and exams to the annotation dict
    for index, row in df_term_medicaux.iterrows():
        if df_term_medicaux.loc[index, "mot"] == "maladie" and df_term_medicaux.loc[index, "term"] not in \
                ann_dict["MAL"]:
            ann_dict["MAL"].append(df_term_medicaux.loc[index, "term"])
        elif df_term_medicaux.loc[index, "mot"] == "medicament" and df_term_medicaux.loc[index, "term"] not in \
                ann_dict["TRAIT"]:
            ann_dict["TRAIT"].append(df_term_medicaux.loc[index, "term"])
        elif df_term_medicaux.loc[index, "mot"] == "examen" and df_term_medicaux.loc[index, "term"] not in \
                ann_dict["EXAM"]:
            ann_dict["EXAM"].append(df_term_medicaux.loc[index, "term"])

    # BIOLOGY
    bio = pd.read_excel("../data/ia/biologie_diabete2.xlsx")
    bio.label = bio.label.apply(clean2)

    for index, rox in bio.iterrows():
        tr = []
        bio_labels = bio.loc[index, "label"].split()
        for mot in range(len(bio_labels)):
            if len(bio_labels[mot]) > 2:
                tr.append(bio_labels[mot])
        bio.loc[index, "mots_nouveaux"] = " ".join(tr)

    # Add the BIO terms to the annotation dict
    for b in bio["mots_nouveaux"].unique():
        ann_dict["BIO"].append(b)

    # Use a second file to add more annotation to BIO
    bio2 = pd.read_csv('../data/ia/freq_terms_biology.csv', sep='\t', encoding='ISO-8859-1', header=None,
                       names=['terme', 'nbres séjour', 't'])
    bio_terms = list(bio2['terme'])

    # Add the new BIO terms to the dict
    for b in bio_terms:
        if unidecode(b) not in ann_dict['BIO']:
            ann_dict['BIO'].append(b)

    # SYMPTOM
    # get the symptoms from a csv file from wikidata
    symptoms = pd.read_csv('../data/ia/symptoms.csv')
    symptom_terms = list(symptoms['symptomLabel'].unique())
    # to lowercase
    symptom_terms = [unidecode(s.lower()) for s in symptom_terms]
    # add the symptoms to the annotation dict
    ann_dict['SYM'] = symptom_terms

    # EXAM
    # get additional exam terms from a csv file from wikidata
    exams = pd.read_csv('../data/ia/exams.csv')
    for exam in exams['examLabel'].unique():
        if unidecode(exam) not in ann_dict['EXAM']:
            ann_dict['EXAM'].append(unidecode(exam))

    # Additional terms from the 'diabete_concepts' csv file
    diabete = pd.read_csv('../data/ia/diabete_concepts.csv', sep=';', encoding = "ISO-8859-1")
    col_names = diabete.columns
    for index, row in diabete.iterrows():
        if row['categorie'] == 'maladie':
            fill_ann_dict_from_diabete(k='MAL', col_names=col_names, row=row, ann_dict=ann_dict)
        elif row['categorie'] == 'symptomes':
            fill_ann_dict_from_diabete(k='SYM', col_names=col_names, row=row, ann_dict=ann_dict)
        elif row['categorie'] == 'biologie':
            fill_ann_dict_from_diabete(k='BIO', col_names=col_names, row=row, ann_dict=ann_dict)
        elif row['categorie'] == 'examen':
            fill_ann_dict_from_diabete(k='EXAM', col_names=col_names, row=row, ann_dict=ann_dict)
        elif row['categorie'] == 'Traitement':
            fill_ann_dict_from_diabete(k='TRAIT', col_names=col_names, row=row, ann_dict=ann_dict)

    return ann_dict
