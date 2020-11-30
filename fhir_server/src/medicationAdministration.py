#!/usr/bin/python
# coding: utf8
import fhirclient.models.fhirreference as fhir_ref_mod
import fhirclient.models.identifier as fhir_id_mod
import fhirclient.models.fhirdate as fhir_date_mod
import fhirclient.models.medicationadministration as fhir_med_mod
import fhirclient.models.quantity as fhir_qty_mod
import fhirclient.models.codeableconcept as fhir_cod_concept_mod
import fhirclient.models.coding as fhir_coding_mod
import fhirclient.models.medication as fhir_medication_mod
from functools import lru_cache
from utils.db_connect import PostgresqlDB, SparqlDB
from utils.utils import date_to_datetime, patient_num_to_ref, encounter_num_to_ref


@lru_cache()
def _get_request_1():
    """
    Get and cache metadata search linking drug administrations and the drugs listed inside

    :return: pd.Frame
    """
    server = SparqlDB()
    query_diag = 'SELECT * WHERE {  ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://chu-bordeaux.fr/prescription-dxcare#drug> .\
                                ?s <http://www.w3.org/2004/02/skos/core#prefLabel> ?label .\
                                ?s <http://chu-bordeaux.fr/m2sitis/iso11179-3/mdr.owl#isComponentOf> ?n .\
                                ?n <http://chu-bordeaux.fr/m2sitis/iso11179-3/mdr.owl#hasTarget> ?code .\
                                ?code <http://www.w3.org/2004/02/skos/core#prefLabel> ?admLabel }'
    res = server.load_data(query_diag)
    hashed_map = {}
    for b in res['results']['bindings']:
        hashed_map[b['admLabel']['value']] = b['label']['value']
    return hashed_map


def get_prescription_drug_label_by_adm_label(adm_label, default_value=""):
    """
    look for a drug label by its administration label via _get_request_1()

    :param adm_label: str
    :param default_value: value to return if not found
    :return: str
    """
    res = _get_request_1()
    if adm_label in res:
        return res[adm_label]
    return default_value


def get_med_for_patient(patient_num):
    """
    searches medication administrations for a given patient

    :param patient_num: str
    :return: [fhirclient.models.medicationadministration.MedicationAdministration() as json]
    """
    return _process_med_request(
        """SELECT * FROM observation_fact WHERE "SOURCESYSTEM_CD" ='DXCARE_PRESCRIPTION' AND "PATIENT_NUM" = """ + patient_num)


def get_med_for_encounter(encounter_num):
    """
    searches medication administrations for a given encounter

    :param encounter_num: str
    :return: [fhirclient.models.medicationadministration.MedicationAdministration() as json]
    """
    return _process_med_request(
        """SELECT * FROM observation_fact WHERE "SOURCESYSTEM_CD" ='DXCARE_PRESCRIPTION' and  "ENCOUNTER_NUM" = """ + encounter_num)


def _process_med_request(sql_statement):
    """
    processes medication administrations for a sql_statement

    :param sql_statement: search statement
    :return: [fhirclient.models.medicationadministration.MedicationAdministration() as json]
    """
    connect_to_db = PostgresqlDB()
    data = connect_to_db.load_data(sql_statement)

    df = list()
    for index, row in data.iterrows():
        medicationAdministration = fhir_med_mod.MedicationAdministration()
        # identifier attribute
        ident = fhir_id_mod.Identifier()
        ident.value = str(row["ENCOUNTER_NUM"]).replace(".0","") + "_" + str(row["INSTANCE_NUM"]).replace(".0","")
        medicationAdministration.identifier = [ident]
        # status attribute
        medicationAdministration.status = "completed"
        # medicationReference attribute
        ref_med = fhir_ref_mod.FHIRReference()
        ref_med.reference = str(row["CONCEPT_CD"]).rsplit("|")[1]
        medicationAdministration.medicationReference = ref_med
        # subject attribute
        ref_subject = fhir_ref_mod.FHIRReference()
        ref_subject.reference = patient_num_to_ref(str(row["PATIENT_NUM"]).replace(".0",""))
        medicationAdministration.subject = ref_subject
        # encounter attribute
        ref_encounter = fhir_ref_mod.FHIRReference()
        ref_encounter.reference = encounter_num_to_ref(str(row["ENCOUNTER_NUM"]).replace(".0",""))
        medicationAdministration.context = ref_encounter
        # effectiveDateTime attribute
        startdate = fhir_date_mod.FHIRDate()
        startdate.date = date_to_datetime(row["START_DATE"])
        medicationAdministration.effectiveDateTime = startdate
        # contained attribute
        contained_resource = fhir_medication_mod.Medication()
        contained_codeableconcept = fhir_cod_concept_mod.CodeableConcept()
        coding = fhir_coding_mod.Coding()
        coding.system = "https://eds.chu-bordeaux.fr/fhir/CodeSystem/drug-code"
        coding.code = str(row["CONCEPT_CD"])
        coding.display = get_prescription_drug_label_by_adm_label(coding.code)
        contained_codeableconcept.coding = [coding]
        contained_codeableconcept.text = coding.display
        contained_resource.code = contained_codeableconcept
        medicationAdministration.contained = [contained_resource]
        # dosage attribute
        if row["QUANTITY_NUM"]:
            dosage = fhir_med_mod.MedicationAdministrationDosage()
            dose = fhir_qty_mod.Quantity()
            dose.value = row["QUANTITY_NUM"]
            dosage.dose = dose
            medicationAdministration.dosage = dosage
        df.append(medicationAdministration.as_json())

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
    pprint.pprint(get_med_for_patient('1'))
