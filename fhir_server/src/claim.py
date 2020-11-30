#!/usr/bin/python
import fhirclient.models.fhirreference as fhir_ref_mod
import fhirclient.models.identifier as fhir_id_mod
import fhirclient.models.fhirdate as fhir_date_mod
import fhirclient.models.claim as fhir_claim_mod
import fhirclient.models.codeableconcept as fhir_cod_concept_mod
import fhirclient.models.coding as fhir_coding_mod
from functools import lru_cache
from utils.db_connect import PostgresqlDB, SparqlDB
from utils.utils import date_to_datetime, patient_num_to_ref, encounter_num_to_ref


@lru_cache()
def _get_request_1():
    """
    Get and cache metadata search linking pmsi and its diagnosticCode

    :return: pd.Frame
    """
    server = SparqlDB()
    query_diag = 'SELECT * WHERE {  ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://chu-bordeaux.fr/pmsi#diagnosticCode> .\
                                    ?s <http://chu-bordeaux.fr/m2sitis/iso11179-3/mdr.owl#hasMeaningPermissibleValueMeaning> ?d .\
                                    ?d <http://www.w3.org/2004/02/skos/core#prefLabel> ?l .\
                                    ?s <http://chu-bordeaux.fr/m2sitis/iso11179-3/mdr.owl#isComponentOf> ?n .\
                                    ?n <http://chu-bordeaux.fr/m2sitis/iso11179-3/mdr.owl#hasTarget> ?pmsi .\
                                    ?pmsi <http://www.w3.org/2004/02/skos/core#prefLabel> ?pmsi_label }'
    res = server.load_data(query_diag)
    hashed_map = {}
    for b in res['results']['bindings']:
        hashed_map[b['pmsi_label']['value']] = b['l']['value']
    return hashed_map


def get_pmsi_diagcode_value_by_pmsilabel(pmsi_label, default_value=""):
    """
    look for a diagnosticCode label by a pmsi prefLabel via _get_request_1()

    :param pmsi_label: str
    :param default_value: value to return if not found
    :return: str
    """
    res = _get_request_1()
    if pmsi_label in res:
        return res[pmsi_label]
    return default_value
    # for b in pmsi_diag['results']['bindings']:
    #     if pmsi_label in b['pmsi_label']['value'] and b['l']['value']:
    #         return b['l']['value']
    # return default_value


@lru_cache()
def _get_request_2():
    """
    Get and cache metadata search linking pmsi and its procedureCode

    :return: pd.Frame
    """
    server = SparqlDB()
    query_diag = 'SELECT * WHERE {  ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://chu-bordeaux.fr/pmsi#procedureCode> .\
                                ?s <http://www.w3.org/2004/02/skos/core#prefLabel> ?label .\
                                ?s <http://chu-bordeaux.fr/m2sitis/iso11179-3/mdr.owl#isComponentOf> ?n .\
                                ?n <http://chu-bordeaux.fr/m2sitis/iso11179-3/mdr.owl#hasTarget> ?pmsi .\
                                ?pmsi <http://www.w3.org/2004/02/skos/core#prefLabel> ?pmsiLabel }'
    res = server.load_data(query_diag)
    hashed_map = {}
    for b in res['results']['bindings']:
        hashed_map[b['pmsiLabel']['value']] = b['label']['value']
    return hashed_map


def get_pmsi_proccode_label_by_pmsilabel(pmsi_label, default_value=""):
    """
    look for a procedureCode label by a pmsi prefLabel via _get_request_2()

    :param pmsi_label: str
    :param default_value: value to return if not found
    :return: str
    """
    res = _get_request_2()
    if pmsi_label in res:
        return res[pmsi_label]
    return default_value


def get_pmsis_for_patient(patient_num):
    """
    searches claims for a given patient

    :param patient_num: str
    :return: [fhirclient.models.claim.Claim() as json]
    """
    return _process_pmsi_request(
        """SELECT * FROM observation_fact WHERE "SOURCESYSTEM_CD" ='DXCARE-PMSI' AND "PATIENT_NUM" = """ + patient_num + """ ORDER BY "START_DATE" """)


def get_pmsis_for_encounter(encounter_num):
    """
    searches claims for a given encounter

    :param encounter_num: str
    :return: [fhirclient.models.claim.Claim() as json]
    """
    return _process_pmsi_request(
        """SELECT * FROM observation_fact WHERE "SOURCESYSTEM_CD" ='DXCARE-PMSI' and  "ENCOUNTER_NUM" = """ + encounter_num + """ ORDER BY "START_DATE" """)


def _process_pmsi_request(sql_statement):
    """
    processes claims for a sql_statement

    :param sql_statement: search statement
    :return: [fhirclient.models.claim.Claim() as json]
    """
    connect_to_db = PostgresqlDB()
    data = connect_to_db.load_data(sql_statement)

    list_of_claims = []

    data = data.groupby(["INSTANCE_NUM"])
    for group_ind, group_data in data:
        claim = fhir_claim_mod.Claim()
        claim.procedure = []
        claim.diagnosis = []
        # identifier attribute
        ident = fhir_id_mod.Identifier()
        ident.value = str(group_data.iloc[0]["ENCOUNTER_NUM"]).replace(".0", "")+ "_" + \
                      str(group_data.iloc[0]["INSTANCE_NUM"]).replace(".0", "")
        claim.identifier = [ident]
        # status attribute
        claim.status = "active"
        # category attribute
        cc_category = fhir_cod_concept_mod.CodeableConcept()
        coding_categ = fhir_coding_mod.Coding()
        coding_categ.system = "http://terminology.hl7.org/CodeSystem/claim-type"
        coding_categ.code = "institutional"
        cc_category.coding = [coding_categ]
        claim.type = cc_category
        # patient attribute
        ref_subject = fhir_ref_mod.FHIRReference()
        ref_subject.reference = patient_num_to_ref(str(group_data.iloc[0]["PATIENT_NUM"]).replace(".0", ""))
        claim.patient = ref_subject
        # encounter attribute
        claim_item = fhir_claim_mod.ClaimItem()
        ref_encounter = fhir_ref_mod.FHIRReference()
        ref_encounter.reference = encounter_num_to_ref(str(group_data.iloc[0]["ENCOUNTER_NUM"]).replace(".0", ""))
        claim_item.encounter = [ref_encounter]
        claim_item.sequence = 0
        claim.item = [claim_item]
        # created attribute
        efdt = fhir_date_mod.FHIRDate()
        efdt.date = date_to_datetime(group_data.iloc[0]["START_DATE"])
        claim.created = efdt
        for index, row in group_data.iterrows():
            if "DIAG" in row["CONCEPT_CD"]:
                # diagnosis attribute
                diag = fhir_claim_mod.ClaimDiagnosis()
                codeableconcept = fhir_cod_concept_mod.CodeableConcept()
                coding = fhir_coding_mod.Coding()
                coding.system = "https://eds.chu-bordeaux.fr/fhir/CodeSystem/pmsi-diagnostic-code"
                coding.code = row["CONCEPT_CD"]
                coding.display = get_pmsi_diagcode_value_by_pmsilabel(row["CONCEPT_CD"])
                codeableconcept.coding = [coding]
                diag.diagnosisCodeableConcept = codeableconcept
                codeableconcept_type = fhir_cod_concept_mod.CodeableConcept()
                if "@" not in row["MODIFIER_CD"]:
                    coding_type = fhir_coding_mod.Coding()
                    coding_type.system = "https://eds.chu-bordeaux.fr/fhir/CodeSystem/pmsi-diagnostic-type"
                    coding_type.code = row["MODIFIER_CD"]
                    codeableconcept_type.coding = [coding_type]
                    diag.type = [codeableconcept_type]
                diag.sequence = row["INSTANCE_NUM"]
                claim.diagnosis.append(diag)
            if "ACTE" in row["CONCEPT_CD"]:
                # procedure attribute
                coding_proc = fhir_coding_mod.Coding()
                coding_proc.code = row["CONCEPT_CD"]
                proc = fhir_claim_mod.ClaimProcedure()
                codeableconcept_proc = fhir_cod_concept_mod.CodeableConcept()
                coding_proc.system = "https://eds.chu-bordeaux.fr/fhir/CodeSystem/pmsi-procedure-code"
                coding_proc.display = get_pmsi_proccode_label_by_pmsilabel(row["CONCEPT_CD"])
                codeableconcept_proc.coding = [coding_proc]
                proc.sequence = row["INSTANCE_NUM"]
                proc.procedureCodeableConcept = codeableconcept_proc
                claim.procedure.append(proc)
        list_of_claims.append(claim.as_json())

    return list_of_claims

# entry point for PySpark application
if __name__ == '__main__':
    import yaml

    # init postgres DB
    with open('config.yaml') as f:
        config = yaml.safe_load(f)

    postgres_db = PostgresqlDB(None, **config['postgres_db'])
    sparql_db = SparqlDB(**config['sparql_db'])

    import pprint
    pprint.pprint(get_pmsis_for_patient('1'))
