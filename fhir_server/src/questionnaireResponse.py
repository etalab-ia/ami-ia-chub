#!/usr/bin/python
# coding: utf8
import fhirclient.models.questionnaireresponse as fhir_quest_mod
import fhirclient.models.fhirdate as fhir_date_mod
import fhirclient.models.identifier as fhir_id_mod
import fhirclient.models.fhirreference as fhir_ref_mod
import fhirclient.models.coding as fhir_coding_mod
from functools import lru_cache
import logging

from utils.db_connect import PostgresqlDB,SparqlDB
from utils.utils import date_to_datetime, patient_num_to_ref, encounter_num_to_ref


########################
# Questions - Réponses #
########################

@lru_cache()
def _get_request_1():
    """
    Get and cache metadata search linking question labels and text

    :return: pd.Frame
    """
    server = SparqlDB()
    query_diag = 'SELECT * WHERE {  ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://chu-bordeaux.fr/questionnaire-dxcare#question> .\
                                ?s <http://chu-bordeaux.fr/m2sitis/iso11179-3/mdr.owl#hasTarget> ?question .\
                                ?question <http://www.w3.org/2004/02/skos/core#prefLabel> ?questionLabel }'
    
    res = server.load_data(query_diag)
    hashed_map = {}
    hashed_map_rev = {}
    for b in res['results']['bindings']:
        hashed_map[b['questionLabel']['value']] = b['s']['value']
        hashed_map_rev[b['s']['value']] = b['questionLabel']['value']
    return hashed_map, hashed_map_rev


def get_question_id_by_questionlabel(question_label, default_value=""):
    """
    look for a question text by its label _get_request_1()

    :param question_label: str
    :param default_value: value to return if not found
    :return: str
    """
    res, _ = _get_request_1()
    if question_label in res:
        return res[question_label]
    return default_value


def get_questionlabel_by_question_id(question_id, default_value=""):
    """
    look for a question text by its label _get_request_1()

    :param question_label: str
    :param default_value: value to return if not found
    :return: str
    """
    _, res = _get_request_1()
    if question_id in res:
        return res[question_id]
    return default_value


@lru_cache()
def _get_request_2():
    """
    Get and cache metadata search linking responses label and text

    :return: pd.Frame
    """
    server = SparqlDB()
    query_diag = 'SELECT * WHERE {  ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://chu-bordeaux.fr/questionnaire-dxcare#response> .\
                                ?s <http://chu-bordeaux.fr/m2sitis/iso11179-3/mdr.owl#isComponentOf> ?n .\
                                ?n <http://chu-bordeaux.fr/m2sitis/iso11179-3/mdr.owl#hasTarget> ?code .\
                                ?code <http://www.w3.org/2004/02/skos/core#prefLabel> ?responseLabel }'
    res = server.load_data(query_diag)
    hashed_map = {}
    hashed_map_rev = {}
    for b in res['results']['bindings']:
        hashed_map[b['responseLabel']['value']] = b['s']['value']
        hashed_map_rev[b['s']['value']] = b['responseLabel']['value']
    return hashed_map, hashed_map_rev


def get_response_id_by_responselabel(response_label, default_value=""):
    """
    look for a response text by its label via _get_request_1()

    :param response_label: str
    :param default_value: value to return if not found
    :return: str
    """
    res, _ = _get_request_2()
    if response_label in res:
        return res[response_label]
    return default_value


def get_responselabel_by_responseid(response_id, default_value=""):
    """
    look for a response text by its label via _get_request_1()

    :param response_label: str
    :param default_value: value to return if not found
    :return: str
    """
    _, res = _get_request_2()
    if response_id in res:
        return res[response_id]
    return default_value


@lru_cache()
def _get_request_3():
    """
    Get and cache metadata search linking responses and questions

    :return: pd.Frame
    """
    server = SparqlDB()
    qr_query = "SELECT * WHERE { ?reponse <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://chu-bordeaux.fr/questionnaire-dxcare#response> .\
                                 ?reponse <http://www.w3.org/2004/02/skos/core#prefLabel> ?reponseLabel .\
                                 ?reponse <http://chu-bordeaux.fr/m2sitis/iso11179-3/mdr.owl#containsDomainPermissibleValueSet> ?valueSet .\
                                 ?valueSet <http://chu-bordeaux.fr/m2sitis/iso11179-3/mdr.owl#providesValuesForDataElementDomain> ?question .\
                                 ?question <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://chu-bordeaux.fr/questionnaire-dxcare#question> .\
                                 ?question <http://www.w3.org/2004/02/skos/core#prefLabel> ?questionLabel }"

    qr = server.load_data(qr_query)

    # le résultat est une liste de tuples
    # chaque tuple est de la forme (question_id, question_label, reponse_id, reponse_label)
    questions_labels = {}
    reponses_label = {}
    reponse_to_question_link = {}
    for b in qr['results']['bindings']:
        questions_labels[b['question']['value']] = b['questionLabel']['value']
        reponses_label[b['reponse']['value']] = b['reponseLabel']['value']
        reponse_to_question_link[b['reponse']['value']] = b['question']['value']
    return questions_labels, reponses_label, reponse_to_question_link


def get_questionnaire_question_label_by_questionid(question_label, default_value=""):
    """
    look for a question text by its label _get_request_1()

    :param question_label: str
    :param default_value: value to return if not found
    :return: str
    """
    questions_labels, reponses_label, reponse_to_question_link = _get_request_3()
    if question_label in questions_labels:
        return questions_labels[question_label]
    return default_value


def get_questionnaire_response_label_by_responseid(response_label, default_value=""):
    """
    look for a response text by its label via _get_request_1()

    :param response_label: str
    :param default_value: value to return if not found
    :return: str
    """
    questions_labels, reponses_label, reponse_to_question_link = _get_request_3()
    if response_label in reponses_label:
        return reponses_label[response_label]
    return default_value


def get_questionid_from_responseid(response_label, default_value=""):
    """
    look for a response text by its label via _get_request_1()

    :param response_label: str
    :param default_value: value to return if not found
    :return: str
    """
    questions_labels, reponses_label, reponse_to_question_link = _get_request_3()
    if response_label in reponse_to_question_link:
        return reponse_to_question_link[response_label]
    return default_value


@lru_cache()
def _get_request_4():
    """
    Get and cache metadata search for questionnaire structure

    :return: pd.Frame
    """
    server = SparqlDB()
    question_labels = {}
    question_to_section_links = {}
    section_labels = {}
    section_to_section_links = {}
    section_to_page_links = {}
    question_to_page_links = {}
    page_labels = {}
    page_to_form_links = {}
    form_labels = {}
    question_in_section = "SELECT * WHERE {  ?question <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://chu-bordeaux.fr/questionnaire-dxcare#question> .\
                                            ?question <http://www.w3.org/2004/02/skos/core#prefLabel> ?questionLabel .\
                                            ?question <http://chu-bordeaux.fr/questionnaire-dxcare#questionInSection> ?section .\
                                            ?section <http://www.w3.org/2004/02/skos/core#prefLabel> ?sectionLabel}"
    res = server.load_data(question_in_section)
    for b in res['results']['bindings']:
        question_labels[b['question']['value']] = b['questionLabel']['value']
        question_to_section_links[b['question']['value']] = b['section']['value']
        section_labels[b['section']['value']] = b['sectionLabel']['value']

    section_in_section = "SELECT * WHERE {  ?section <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://chu-bordeaux.fr/questionnaire-dxcare#section> .\
                                            ?section <http://www.w3.org/2004/02/skos/core#prefLabel> ?sectionLabel1 .\
                                            ?section <http://chu-bordeaux.fr/questionnaire-dxcare#sectionInSection> ?section2 .\
                                            ?section2 <http://www.w3.org/2004/02/skos/core#prefLabel> ?sectionLabel2}"
    res = server.load_data(section_in_section)
    for b in res['results']['bindings']:
        section_labels[b['section']['value']] = b['sectionLabel1']['value']
        section_labels[b['section2']['value']] = b['sectionLabel2']['value']
        section_to_section_links[b['section']['value']] = b['section2']['value']

    section_in_page = "SELECT * WHERE {  ?section <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://chu-bordeaux.fr/questionnaire-dxcare#section> .\
                                        ?section <http://www.w3.org/2004/02/skos/core#prefLabel> ?sectionLabel .\
                                        ?section <http://chu-bordeaux.fr/questionnaire-dxcare#sectionInPage> ?page .\
                                        ?page <http://www.w3.org/2004/02/skos/core#prefLabel> ?pageLabel}"
    res = server.load_data(section_in_page)
    for b in res['results']['bindings']:
        section_labels[b['section']['value']] = b['sectionLabel']['value']
        page_labels[b['page']['value']] = b['pageLabel']['value']
        section_to_page_links[b['section']['value']] = b['page']['value']

    question_in_page = "SELECT * WHERE {  ?question <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://chu-bordeaux.fr/questionnaire-dxcare#question> .\
                                            ?question <http://www.w3.org/2004/02/skos/core#prefLabel> ?questionLabel .\
                                            ?question <http://chu-bordeaux.fr/questionnaire-dxcare#questionInPage> ?page .\
                                            ?page <http://www.w3.org/2004/02/skos/core#prefLabel> ?pageLabel}"
    res = server.load_data(question_in_page)
    for b in res['results']['bindings']:
        question_labels[b['question']['value']] = b['questionLabel']['value']
        question_to_page_links[b['question']['value']] = b['page']['value']
        page_labels[b['page']['value']] = b['pageLabel']['value']

    page_in_form = "SELECT * WHERE {  ?page <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://chu-bordeaux.fr/questionnaire-dxcare#page> .\
                                        ?page <http://www.w3.org/2004/02/skos/core#prefLabel> ?pageLabel .\
                                        ?page <http://chu-bordeaux.fr/questionnaire-dxcare#pageInForm> ?form .\
                                        ?form <http://www.w3.org/2004/02/skos/core#prefLabel> ?formLabel}"
    res = server.load_data(page_in_form)
    for b in res['results']['bindings']:
        page_labels[b['page']['value']] = b['pageLabel']['value']
        form_labels[b['form']['value']] = b['formLabel']['value']
        page_to_form_links[b['page']['value']] = b['form']['value']

    return (question_labels, section_labels, page_labels, form_labels), \
            (question_to_section_links, section_to_section_links, section_to_page_links, question_to_page_links, page_to_form_links)


def get_question_to_form_links(question):
    _, (question_to_section_links, section_to_section_links, section_to_page_links, question_to_page_links, page_to_form_links) = _get_request_4()
    link = [question]
    if question in question_to_section_links:
        link.append(question_to_section_links[question])
        while link[-1] in section_to_section_links:
            link.append(section_to_section_links[link[-1]])
        if link[-1] not in section_to_page_links:
            raise ValueError(f'page not found for section {link[-1]}')
        link.append(section_to_page_links[link[-1]])
    elif question in question_to_page_links:
        link.append(question_to_page_links[question])
    else:
        raise ValueError(f'section or page not found for question {question}')
    if link[-1] not in page_to_form_links:
        raise ValueError(f'form not found for page {link[-1]}')
    link.append(page_to_form_links[link[-1]])
    return link


def add_questionid_to_questionnaire(question_id, questionlabel, questionnaire):
    (question_labels, section_labels, page_labels, form_labels), _ = _get_request_4()
    descending_links = list(reversed(get_question_to_form_links(question_id)))

    items_idxs = []
    # form
    forms = [elt.linkId for elt in questionnaire.item]
    if descending_links[0] in forms:
        form_idx = forms.index(descending_links[0])
    else:
        quest_item = fhir_quest_mod.QuestionnaireResponseItem()
        quest_item.linkId = descending_links[0]
        quest_item.text = form_labels[descending_links[0]]
        quest_item.item = []
        questionnaire.item.append(quest_item)
        form_idx = len(questionnaire.item) - 1
    items_idxs.append(form_idx)

    # page
    pages = [elt.linkId for elt in questionnaire.item[form_idx].item]
    if descending_links[1] in pages:
        page_idx = pages.index(descending_links[1])
    else:
        quest_item = fhir_quest_mod.QuestionnaireResponseItem()
        quest_item.linkId = descending_links[1]
        quest_item.text = page_labels[descending_links[1]]
        quest_item.item = []
        questionnaire.item[form_idx].item.append(quest_item)
        page_idx = len(questionnaire.item[form_idx].item) - 1
    items_idxs.append(page_idx)

    # sections
    start_item = questionnaire.item[form_idx].item[page_idx]
    for i in range(2, len(descending_links)-1):
        sections = [elt.linkId for elt in start_item.item]
        if descending_links[i] in sections:
            section_idx = sections.index(descending_links[i])
        else:
            quest_item = fhir_quest_mod.QuestionnaireResponseItem()
            quest_item.linkId = descending_links[i]
            quest_item.text = section_labels[descending_links[i]]
            quest_item.item = []
            start_item.item.append(quest_item)
            section_idx = len(start_item.item) - 1
        start_item = start_item.item[section_idx]
        items_idxs.append(section_idx)

    # question
    if not questionlabel:
        questionlabel = get_questionlabel_by_question_id(descending_links[-1])
    questions = [elt.linkId for elt in start_item.item]
    if descending_links[-1] in questions:
        question_idx = questions.index(descending_links[-1])
        if not start_item.item[question_idx].definition:
            start_item.item[question_idx].definition = questionlabel
    else:
        quest_item = fhir_quest_mod.QuestionnaireResponseItem()
        quest_item.definition = questionlabel
        quest_item.linkId = question_id
        quest_item.text = question_labels[descending_links[-1]]
        quest_item.item = []
        start_item.item.append(quest_item)
        question_idx = len(start_item.item) - 1
    items_idxs.append(question_idx)

    return items_idxs


def add_questionlabel_to_questionnaire(questionlabel, questionnaire):
    question_id = get_question_id_by_questionlabel(questionlabel)
    return add_questionid_to_questionnaire(question_id, questionlabel, questionnaire)


def add_responselabel_to_questionnaire(responselabel, val_type, val, questionnaire):
    response_id = get_response_id_by_responselabel(responselabel)
    question_id = get_questionid_from_responseid(response_id)
    items_idx = add_questionid_to_questionnaire(question_id, "", questionnaire)
    start_item = questionnaire
    for idx in items_idx:
        start_item = start_item.item[idx]

    answer_item = fhir_quest_mod.QuestionnaireResponseItemAnswer()
    coding = fhir_coding_mod.Coding()
    coding.system = "https://eds.chu-bordeaux.fr/DxCareForms"
    coding.code = get_responselabel_by_responseid(response_id)
    coding.display = get_questionnaire_response_label_by_responseid(response_id)
    answer_item.valueCoding = coding
    if val_type == "N":
        answer_item.valueDecimal = val
    elif val_type == "T":
        answer_item.valueString = str(val)  # .encode('ascii', 'ignore'))
    if not start_item.answer:
        start_item.answer = []
    start_item.answer.append(answer_item)


def get_quest_for_patient(patient_num):
    """
    searches questionnaire responses for a given patient

    :param patient_num: str
    :return: [fhirclient.models.questionnaireresponse.QuestionnaireResponse() as json]
    """
    return _process_quest_request(
        """SELECT * FROM observation_fact WHERE "SOURCESYSTEM_CD" ='CHU_BORDEAUX_QUESTIONNAIRES_DXC' AND "PATIENT_NUM" = """ + patient_num)


def get_quest_for_encounter(encounter_num):
    """
    searches questionnaire responses for a given encounter

    :param encounter_num: str
    :return: [fhirclient.models.questionnaireresponse.QuestionnaireResponse() as json]
    """
    return _process_quest_request(
        """SELECT * FROM observation_fact WHERE "SOURCESYSTEM_CD" ='CHU_BORDEAUX_QUESTIONNAIRES_DXC' and  "ENCOUNTER_NUM" = """ + encounter_num)


def _process_quest_request(sql_statement):
    """
    processes questionnaire responses for a sql_statement

    :param sql_statement: search statement
    :return: [fhirclient.models.questionnaireresponse.QuestionnaireResponse() as json]
    """
    connect_to_db = PostgresqlDB()
    data = connect_to_db.load_data(sql_statement)
    questionnaires = {}
    df = list()
    for index, row in data.iterrows():
        q_id = str(row["ENCOUNTER_NUM"]).replace(".0","") + "_" + str(row["INSTANCE_NUM"]).replace(".0","")
        if q_id not in questionnaires:
            questionnaireResponse = fhir_quest_mod.QuestionnaireResponse()
            # identifier attribute
            ident = fhir_id_mod.Identifier()
            ident.value = str(row["ENCOUNTER_NUM"]).replace(".0","") + "_" + str(row["INSTANCE_NUM"]).replace(".0","")
            questionnaireResponse.identifier = ident
            # status attribute
            questionnaireResponse.status = "completed"
            # subject attribute
            ref_subject = fhir_ref_mod.FHIRReference()
            ref_subject.reference = patient_num_to_ref(str(row["PATIENT_NUM"]).replace(".0",""))
            questionnaireResponse.subject = ref_subject
            # encounter attribute
            ref_encounter = fhir_ref_mod.FHIRReference()
            ref_encounter.reference = encounter_num_to_ref(str(row["ENCOUNTER_NUM"]).replace(".0",""))
            questionnaireResponse.encounter = ref_encounter
            # authored attribute
            efdt = fhir_date_mod.FHIRDate()
            efdt.date = date_to_datetime(row["START_DATE"])
            questionnaireResponse.authored = efdt
            #items
            questionnaireResponse.item = []
            questionnaires[q_id] = questionnaireResponse

        try:
            qr = questionnaires[q_id]
            if "QUESTION" in str(row["CONCEPT_CD"]):
                add_questionlabel_to_questionnaire(str(row["CONCEPT_CD"]), qr)
            if "REPONSE" in str(row["CONCEPT_CD"]):
                val = ""
                if row['VALTYPE_CD'] == "N":
                    val = row["NVAL_NUM"]
                elif row['VALTYPE_CD'] == "T":
                    val = str(row["OBSERVATION_BLOB"])  # .encode('ascii', 'ignore'))
                add_responselabel_to_questionnaire(str(row["CONCEPT_CD"]), row['VALTYPE_CD'], val, qr)
        except ValueError as e:
            logging.getLogger('questionnaireResponse').warning(f'Could not place {str(row["CONCEPT_CD"])}: {e}')
            continue

    for qr in questionnaires.values():
        json_val = qr.as_json()
        # bug trouvé en testant   --> solved in fhirclient==4.0.0, not yet available on pip
        if 'encounter' not in json_val:
            json_val['encounter'] = qr.encounter.as_json()
        df.append(json_val)

    return df


# entry point for PySpark application
if __name__ == '__main__':
    import yaml

    # init postgres DB
    with open('config.yaml') as f:
        config = yaml.safe_load(f)

    postgres_db = PostgresqlDB(None, **config['postgres_db'])
    sparql_db = SparqlDB(**config['sparql_db'])
    import pprint

    pprint.pprint(get_quest_for_patient('1'))