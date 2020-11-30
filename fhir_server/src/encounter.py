#!/usr/bin/python
# coding: utf8
import fhirclient.models.encounter as fhir_encounter_mod
import fhirclient.models.fhirdate as fhir_date_mod
import fhirclient.models.identifier as fhir_id_mod
import fhirclient.models.period as fhir_period_mod
import fhirclient.models.fhirreference as fhir_ref_mod
import fhirclient.models.codeableconcept as fhir_cod_concept_mod
from utils.db_connect import PostgresqlDB
from utils.utils import date_to_datetime, patient_num_to_ref


def get_encounter(encounter_num):
    """
    Process encounter data for a given encounter

    :param encounter_num: str
    :return: fhirclient.models.encounter.Encounter()
    """
    connect_to_db = PostgresqlDB()
    sql_statement = """
        SELECT 
            a."PATIENT_NUM",
            a."ENCOUNTER_NUM", 
            a."START_DATE",
            a."END_DATE",
            a."SOURCESYSTEM_CD",
            a."UPLOAD_ID",
            b."TYPE",
            c."UAM",
            c."START_DATE" as start_date,
            c."END_DATE" as end_date
        FROM 
            visit_dimension a
        INNER JOIN visit_type b
        ON a."ENCOUNTER_NUM" = b."ENCOUNTER_NUM"
        INNER JOIN visit_location c
        ON a."ENCOUNTER_NUM" = c."ENCOUNTER_NUM"
        WHERE a."ENCOUNTER_NUM" =
         """ + encounter_num

    data = connect_to_db.load_data(sql_statement)
    if data.empty:
        raise ValueError()

    encounter_data = data.iloc[0]
    encounter = fhir_encounter_mod.Encounter()
    # id attribute
    encounter.id = str(encounter_data["ENCOUNTER_NUM"]).replace(".0","")
    # status attribute
    encounter.status = "finished"
    # identifier attribute
    ident = fhir_id_mod.Identifier()
    ident.system = str(encounter_data["SOURCESYSTEM_CD"])
    ident.value = str(encounter_data["UPLOAD_ID"])
    encounter.identifier = [ident]
    # period attribute
    startdate = fhir_date_mod.FHIRDate()
    startdate.date = date_to_datetime(encounter_data["START_DATE"])
    period = fhir_period_mod.Period()
    period.start = startdate
    enddate = fhir_date_mod.FHIRDate()
    enddate.date = date_to_datetime(encounter_data["END_DATE"])
    period.end = enddate
    encounter.period = period
    # subject attribute
    ref_subject = fhir_ref_mod.FHIRReference()
    ref_subject.reference = patient_num_to_ref(str(encounter_data["PATIENT_NUM"]).replace(".0",""))
    encounter.subject = ref_subject
    # type attribute
    codeableconcept = fhir_cod_concept_mod.CodeableConcept()
    codeableconcept.text = str(encounter_data["TYPE"])
    encounter.type = [codeableconcept]
    # location attribute
    encounter.location = []
    for index in range(data.shape[0]):

        enc_location = fhir_encounter_mod.EncounterLocation()
        ref_location = fhir_ref_mod.FHIRReference()
        ref_location.reference = data["UAM"].astype(str)[index]
        enc_location.location = ref_location
        loc_startdate = fhir_date_mod.FHIRDate()
        loc_startdate.date = date_to_datetime(data["start_date"][index])
        loc_period = fhir_period_mod.Period()
        loc_period.start = loc_startdate
        loc_enddate = fhir_date_mod.FHIRDate()
        loc_enddate.date = date_to_datetime(data["end_date"][index])
        loc_period.end = loc_enddate
        enc_location.period = loc_period
        encounter.location.append(enc_location)

    return encounter.as_json()


# entry point for PySpark application
if __name__ == '__main__':
    import yaml
    # init postgres DB
    with open('config.yaml') as f:
        config = yaml.safe_load(f)

    postgres_db = PostgresqlDB(None, **config['postgres_db'])

    import pprint
    pprint.pprint(get_encounter('22'))