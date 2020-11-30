#!/usr/bin/python
import fhirclient.models.fhirreference as fhir_ref_mod
import fhirclient.models.identifier as fhir_id_mod
import fhirclient.models.fhirdate as fhir_date_mod
import fhirclient.models.procedure as fhir_procedure_mod
import fhirclient.models.codeableconcept as fhir_cod_concept_mod
import fhirclient.models.coding as fhir_coding_mod
from functools import lru_cache
from utils.db_connect import PostgresqlDB, SparqlDB
from utils.utils import date_to_datetime, patient_num_to_ref, encounter_num_to_ref


@lru_cache()
def _get_request_1():
    """
    Get and cache metadata search linking bdd labels and mds labels

    :return: pd.Frame
    """
    server = SparqlDB()
    query_diag = 'SELECT * WHERE {  ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://chu-bordeaux.fr/prescription-traceline#bloodDerivedDrug> .\
                                ?s <http://www.w3.org/2004/02/skos/core#prefLabel> ?label .\
                                ?s <http://chu-bordeaux.fr/m2sitis/iso11179-3/mdr.owl#isComponentOf> ?n .\
                                ?n <http://chu-bordeaux.fr/m2sitis/iso11179-3/mdr.owl#hasTarget> ?code .\
                                ?code <http://www.w3.org/2004/02/skos/core#prefLabel> ?mdsLabel .\
                                ?s <http://chu-bordeaux.fr/prescription-traceline#drugInDrugFamily> ?drugFamily .\
                                ?drugFamily <http://www.w3.org/2004/02/skos/core#prefLabel> ?drugFamilyLabel}'
    res = server.load_data(query_diag)
    hashed_map = {}
    for b in res['results']['bindings']:
        hashed_map[b['mdsLabel']['value']] = (b['label']['value'],
                                              (b['drugFamily']['value'], b['drugFamilyLabel']['value']))
    return hashed_map


def get_prescription_bdd_label_from_mds_label(mds_label, default_value=""):
    """
    look for a bdd label by its mds label via _get_request_1()

    :param mds_label: str
    :param default_value: value to return if not found
    :return: str
    """
    res = _get_request_1()
    if mds_label in res:
        return res[mds_label][0]
    return default_value


def get_drug_category_id_and_label_from_mds_label(mds_label, default_value=""):
    """
    look for a bdd label by its mds label via _get_request_1()

    :param mds_label: str
    :param default_value: value to return if not found
    :return: str
    """
    res = _get_request_1()
    if mds_label in res:
        return res[mds_label][1]
    return default_value, default_value


@lru_cache()
def _get_request_2():
    """
    Get and cache metadata search linking lbp labels and psl labels

    :return: pd.Frame
    """
    server = SparqlDB()
    query_diag = 'SELECT * WHERE {  ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://chu-bordeaux.fr/prescription-traceline#labileBloodProduct> .\
                                ?s <http://www.w3.org/2004/02/skos/core#prefLabel> ?label .\
                                ?s <http://chu-bordeaux.fr/m2sitis/iso11179-3/mdr.owl#isComponentOf> ?n .\
                                ?n <http://chu-bordeaux.fr/m2sitis/iso11179-3/mdr.owl#hasTarget> ?code .\
                                ?code <http://www.w3.org/2004/02/skos/core#prefLabel> ?pslLabel .\
                                ?s <http://chu-bordeaux.fr/prescription-traceline#drugInDrugFamily> ?drugFamily .\
                                ?drugFamily <http://www.w3.org/2004/02/skos/core#prefLabel> ?drugFamilyLabel}'
    res = server.load_data(query_diag)
    hashed_map = {}
    for b in res['results']['bindings']:
        hashed_map[b['pslLabel']['value']] = (b['label']['value'],
                                              (b['drugFamily']['value'], b['drugFamilyLabel']['value']))
    return hashed_map


def get_prescription_lbd_label_from_psl_label(psl_label, default_value=""):
    """
    look for a lbd label by its psl label via _get_request_2()

    :param concept_cd: str
    :param default_value: value to return if not found
    :return: str
    """
    res = _get_request_2()
    if psl_label in res:
        return res[psl_label][0]
    return default_value


def get_drug_category_id_and_label_from_psl_label(psl_label, default_value=""):
    """
    look for a lbd label by its psl label via _get_request_2()

    :param concept_cd: str
    :param default_value: value to return if not found
    :return: str
    """
    res = _get_request_2()
    if psl_label in res:
        return res[psl_label][1]
    return default_value, default_value


def get_proc_for_patient(patient_num):
    """
    searches procedures for a given patient

    :param patient_num: str
    :return: [fhirclient.models.procedure.Procedure() as json]
    """
    return _process_proc_request(
        """SELECT * FROM observation_fact WHERE "SOURCESYSTEM_CD" ='TRACELINE' AND "PATIENT_NUM" = """ + patient_num)


def get_proc_for_encounter(encounter_num):
    """
    searches procedures for a given encounter

    :param encounter_num: str
    :return: [fhirclient.models.procedure.Procedure() as json]
    """
    return _process_proc_request(
        """SELECT * FROM observation_fact WHERE "SOURCESYSTEM_CD" ='TRACELINE' and  "ENCOUNTER_NUM" = """ + encounter_num)


def _process_proc_request(sql_statement):
    """
    processes procedures for a sql_statement

    :param sql_statement: search statement
    :return: [fhirclient.models.procedure.Procedure() as json]
    """
    connect_to_db = PostgresqlDB()

    data = connect_to_db.load_data(sql_statement)
    df = list()
    for index, row in data.iterrows():
        procedure = fhir_procedure_mod.Procedure()
        # identifier attribute
        ident = fhir_id_mod.Identifier()
        ident.value = str(row["ENCOUNTER_NUM"]).replace(".0","") + "_" + str(row["INSTANCE_NUM"]).replace(".0","")
        procedure.identifier = [ident]
        # status attribute
        procedure.status = "completed"
        # category attribute
        cc_category = fhir_cod_concept_mod.CodeableConcept()
        coding_categ = fhir_coding_mod.Coding()
        coding_categ.system = "https://eds.chu-bordeaux.fr/fhir/traceline-domain"
        if "PSL" in str(row["CONCEPT_CD"]):
            coding_categ.code, coding_categ.display = get_drug_category_id_and_label_from_psl_label(str(row["CONCEPT_CD"]))
        else:
            coding_categ.code, coding_categ.display = get_drug_category_id_and_label_from_mds_label(str(row["CONCEPT_CD"]))
        cc_category.coding = [coding_categ]
        procedure.category = cc_category
        # subject attribute
        ref_subject = fhir_ref_mod.FHIRReference()
        ref_subject.reference = patient_num_to_ref(str(row["PATIENT_NUM"]).replace(".0",""))
        procedure.subject = ref_subject
        # encounter attribute
        ref_encounter = fhir_ref_mod.FHIRReference()
        ref_encounter.reference = encounter_num_to_ref(str(row["ENCOUNTER_NUM"]).replace(".0",""))
        procedure.encounter = ref_encounter
        # performedDateTime attribute
        efdt = fhir_date_mod.FHIRDate()
        efdt.date = date_to_datetime(row["START_DATE"])
        procedure.performedDateTime  = efdt
        # code attribute
        codeableconcept = fhir_cod_concept_mod.CodeableConcept()
        coding = fhir_coding_mod.Coding()
        coding.system = "https://eds.chu-bordeaux.fr/fhir/traceline-category"
        coding.code = str(row["CONCEPT_CD"])
        if "PSL" in str(row["CONCEPT_CD"]):
            coding.display = get_prescription_lbd_label_from_psl_label(coding.code)
        else:
            coding.display = get_prescription_bdd_label_from_mds_label(coding.code)
        codeableconcept.coding = [coding]
        procedure.code = codeableconcept

        json_val = procedure.as_json()
        # bug trouvé en testant   --> solved in fhirclient==4.0.0, not yet available on pip
        if 'encounter' not in json_val:
            json_val['encounter'] = ref_encounter.as_json()
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
    pprint.pprint(get_proc_for_patient('2'))


