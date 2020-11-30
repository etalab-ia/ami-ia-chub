#!/usr/bin/python
# coding: utf8
import fhirclient.models.fhirreference as fhir_ref_mod
import fhirclient.models.identifier as fhir_id_mod
import fhirclient.models.fhirdate as fhir_date_mod
import fhirclient.models.diagnosticreport as fhir_diag_mod
import fhirclient.models.codeableconcept as fhir_cod_concept_mod
import fhirclient.models.coding as fhir_coding_mod
from functools import lru_cache
from utils.db_connect import PostgresqlDB, SparqlDB
from utils.utils import date_to_datetime, patient_num_to_ref, encounter_num_to_ref


@lru_cache()
def _get_request_1():
    """
    Get and cache metadata search linking documents and their categories

    :return: pd.Frame
    """
    server = SparqlDB()
    query_diag = 'SELECT * WHERE {  ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://chu-bordeaux.fr/document#document> .\
                                ?s <http://www.w3.org/2004/02/skos/core#prefLabel> ?label .\
                                ?s <http://chu-bordeaux.fr/m2sitis/iso11179-3/mdr.owl#hasTarget> ?doc .\
                                ?doc <http://www.w3.org/2004/02/skos/core#prefLabel> ?docLabel }'
    res = server.load_data(query_diag)
    hashed_map = {}
    for b in res['results']['bindings']:
        hashed_map[b['docLabel']['value']] = b['label']['value']
    return hashed_map


def get_doccat_label_by_doclabel(doc_label, default_value=""):
    """
    look for a document "category label" by its label via _get_request_1()

    :param doc_label: str
    :param default_value: value to return if not found
    :return: str
    """
    res = _get_request_1()
    if doc_label in res:
        return res[doc_label]
    return default_value


def get_report_for_patient(patient_num):
    """
    searches diagnostic reports for a given patient

    :param patient_num: str
    :return: [fhirclient.models.diagnosticreport.DiagnosticReport() as json]
    """
    return _process_report_request(
        """SELECT * FROM observation_fact WHERE "SOURCESYSTEM_CD" IN ('SRV_DOC', 'SRV_IMAGERIE') AND "PATIENT_NUM" = """ + patient_num)


def get_report_for_encounter(encounter_num):
    """
    searches diagnostic reports for a given encounter

    :param encounter_num: str
    :return: [fhirclient.models.diagnosticreport.DiagnosticReport() as json]
    """
    return _process_report_request(
        """SELECT * FROM observation_fact WHERE "SOURCESYSTEM_CD" IN ('SRV_DOC', 'SRV_IMAGERIE') AND "ENCOUNTER_NUM" = """ + encounter_num)


def _process_report_request(sql_statement):
    """
    processes diagnostic reports for a sql_statement

    :param sql_statement: search statement
    :return: [fhirclient.models.DiagnosticReport.DiagnosticReport() as json]
    """
    connect_to_db = PostgresqlDB()
    data = connect_to_db.load_data(sql_statement)

    df = list()
    for index, row in data.iterrows():
        diagnosticReport = fhir_diag_mod.DiagnosticReport()
        # identifier attribute
        ident = fhir_id_mod.Identifier()
        ident.value = str(row["ENCOUNTER_NUM"]).replace(".0","") + "_" + str(row["INSTANCE_NUM"]).replace(".0","")
        diagnosticReport.identifier = [ident]
        # status attribute
        diagnosticReport.status = "final"
        # category attribute
        cc_category = fhir_cod_concept_mod.CodeableConcept()
        coding_categ = fhir_coding_mod.Coding()
        coding_categ.system = "https://eds.chu-bordeaux.fr/fhir/document-domain"
        coding_categ.code = "https://eds.chu-bordeaux.fr/fhir/document-domain/1"
        coding_categ.display = "Document de sortie"
        cc_category.coding = [coding_categ]
        diagnosticReport.category = cc_category
        # subject attribute
        ref_subject = fhir_ref_mod.FHIRReference()
        ref_subject.reference = patient_num_to_ref(str(row["PATIENT_NUM"]).replace(".0",""))
        diagnosticReport.subject = ref_subject
        # encounter attribute
        ref_encounter = fhir_ref_mod.FHIRReference()
        ref_encounter.reference = encounter_num_to_ref(str(row["ENCOUNTER_NUM"]).replace(".0",""))
        diagnosticReport.encounter = ref_encounter
        # issued attribute
        issued = fhir_date_mod.FHIRDate()
        issued.date = date_to_datetime(row["START_DATE"])
        diagnosticReport.issued = issued
        # code attribute
        codeableconcept = fhir_cod_concept_mod.CodeableConcept()
        coding = fhir_coding_mod.Coding()
        coding.system = "https://eds.chu-bordeaux.fr/fhir/document-category"
        coding.code = str(row["CONCEPT_CD"])
        coding.display = get_doccat_label_by_doclabel(coding.code)
        codeableconcept.coding = [coding]
        codeableconcept.text = coding.display
        diagnosticReport.code = codeableconcept
        # text
        diagnosticReport.conclusion = row["OBSERVATION_BLOB"]

        # bug trouvé en testant   --> solved in fhirclient==4.0.0, not yet available on pip
        json_val = diagnosticReport.as_json()
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
    pprint.pprint(get_report_for_patient('1'))
