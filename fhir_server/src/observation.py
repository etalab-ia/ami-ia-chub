#!/usr/bin/python
import fhirclient.models.fhirreference as fhir_ref_mod
import fhirclient.models.identifier as fhir_id_mod
import fhirclient.models.fhirdate as fhir_date_mod
import fhirclient.models.observation as fhir_observation_mod
import fhirclient.models.codeableconcept as fhir_cod_concept_mod
import fhirclient.models.coding as fhir_coding_mod
import fhirclient.models.quantity as fhir_qty_mod
from fhirclient.models.observation import ObservationReferenceRange
from functools import lru_cache
from utils.db_connect import PostgresqlDB, SparqlDB
from utils.utils import date_to_datetime, patient_num_to_ref, encounter_num_to_ref


@lru_cache()
def _get_request_1():
    """
    Get and cache metadata search linking drug biological results and their targets

    :return: pd.Frame
    """
    server = SparqlDB()
    bio_result = 'SELECT * WHERE {  ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://chu-bordeaux.fr/biologie-dxcare-num#biologicalResult> .\
                                    ?s <http://chu-bordeaux.fr/m2sitis/iso11179-3/mdr.owl#hasTarget> ?t .\
                                    ?t <http://www.w3.org/2000/01/rdf-schema#label> ?t_label .\
                                    ?s <http://www.w3.org/2000/01/rdf-schema#label> ?r_label }'
    res = server.load_data(bio_result)
    hashed_map = {}
    for b in res['results']['bindings']:
        hashed_map[b['t_label']['value']] = b['r_label']['value']
    return hashed_map


@lru_cache()
def get_bio_result_label_from_concept_cd(concept_cd, default_value=""):
    """
    look for a bio result label by its concept_cd via _get_request_1()

    :param concept_cd: str
    :param default_value: value to return if not found
    :return: str
    """
    res = _get_request_1()
    if concept_cd in res:
        return res[concept_cd]
    return default_value


def get_obs_for_patient(patient_num):
    """
    searches observations for a given patient

    :param patient_num: str
    :return: [fhirclient.models.observation.Observation() as json]
    """
    return _process_obs_request(
        """SELECT * FROM observation_fact WHERE "SOURCESYSTEM_CD" ='DXCARE_RESULTATS' AND "PATIENT_NUM" = """ + patient_num)


def get_obs_for_encounter(encounter_num):
    """
    searches observations for a given encounter

    :param encounter_num: str
    :return: [fhirclient.models.observation.Observation() as json]
    """
    return _process_obs_request(
        """SELECT * FROM observation_fact WHERE "SOURCESYSTEM_CD" ='DXCARE_RESULTATS' and  "ENCOUNTER_NUM" = """ + encounter_num)


def _process_obs_request(sql_statement):
    """
    processes observations for a sql_statement

    :param sql_statement: search statement
    :return: [fhirclient.models.observation.Observation() as json]
    """
    connect_to_db = PostgresqlDB()
    data = connect_to_db.load_data(sql_statement)

    df = list()
    for index, row in data.iterrows():
        observation = fhir_observation_mod.Observation()
        # identifier attribute
        ident = fhir_id_mod.Identifier()
        ident.value = str(row["PATIENT_NUM"]).replace(".0","") + "_" + str(row["ENCOUNTER_NUM"]).replace(".0","")
        observation.identifier = [ident]
        # status attribute
        observation.status = "final"
        # category attribute
        cc_category = fhir_cod_concept_mod.CodeableConcept()
        coding_categ = fhir_coding_mod.Coding()
        coding_categ.system = "https://eds.chu-bordeaux.fr/fhir/bio-category"
        coding_categ.code = str(row["CONCEPT_CD"]).replace(".0","")
        cc_category.coding = [coding_categ]
        observation.category = [cc_category]
        # subject attribute
        ref_subject = fhir_ref_mod.FHIRReference()
        ref_subject.reference = patient_num_to_ref(str(row["PATIENT_NUM"]).replace(".0",""))
        observation.subject = ref_subject
        # encounter attribute
        ref_encounter = fhir_ref_mod.FHIRReference()
        ref_encounter.reference = encounter_num_to_ref(str(row["ENCOUNTER_NUM"]).replace(".0",""))
        observation.encounter = ref_encounter
        # effectiveDateTime attribute
        efdt = fhir_date_mod.FHIRDate()
        efdt.date = date_to_datetime(row["START_DATE"])
        observation.effectiveDateTime = efdt
        # code attribute
        codeableconcept = fhir_cod_concept_mod.CodeableConcept()
        coding = fhir_coding_mod.Coding()
        coding.system = "https://eds.chu-bordeaux.fr/fhir/bio-code"
        coding.code = str(row["CONCEPT_CD"])
        coding.display = get_bio_result_label_from_concept_cd(coding.code)
        codeableconcept.coding = [coding]
        codeableconcept.text = coding.display
        observation.code = codeableconcept
        # valueQuantity attribute
        quantity = fhir_qty_mod.Quantity()
        quantity.value = row["NVAL_NUM"]
        quantity.unit = str(row["UNITS_CD"])  #.encode('ascii', 'ignore')
        observation.valueQuantity = quantity
        # referenceRange attribute
        ref_range = ObservationReferenceRange()
        ref_range.text = str(row["VALUEFLAG_CD"])
        observation.referenceRange = [ref_range]
        json_val = observation.as_json()
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
    pprint.pprint(get_obs_for_patient('1'))


