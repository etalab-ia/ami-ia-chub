#!/usr/bin/python
# coding: utf8
import fhirclient.models.patient as fhir_patient_mod
import fhirclient.models.fhirdate as fhir_date_mod
import fhirclient.models.identifier as fhir_id_mod
from utils.db_connect import PostgresqlDB
from utils.utils import date_to_datetime


def get_patient(patient_num):
    """
    search and process patient data for a given encounter

    :param patient_num: str
    :return: fhirclient.models.patient.Patient()
    """
    connect_to_db = PostgresqlDB()
    data = connect_to_db.load_data("""SELECT * FROM patient_dimension  WHERE  "PATIENT_NUM" = """ + patient_num)
    if data.empty:
        raise ValueError()

    patient_data = data.iloc[0]
    patient = fhir_patient_mod.Patient()
    # id attribute
    patient.id = str(patient_data["PATIENT_NUM"]).replace(".0","")
    # status attribute
    patient.status = "generated"
    # identifier attribute
    ident = fhir_id_mod.Identifier()
    ident.system = patient_data["SOURCESYSTEM_CD"]
    ident.value = str(patient_data["PATIENT_NUM"]).replace(".0", "")
    patient.identifier = [ident]
    # gender attribute
    if data["SEX_CD"].item() == 'DEM|SEX:F':
        patient.gender = 'female'
    elif data["SEX_CD"].item() == 'DEM|SEX:M':
        patient.gender = 'male'
    else :
        patient.gender = 'other'
    # birthdate attribute
    birthdate = fhir_date_mod.FHIRDate()
    birthdate.date = date_to_datetime(patient_data["BIRTH_DATE"])
    patient.birthDate = birthdate
    # deathdate attribute
    deathdate = fhir_date_mod.FHIRDate()
    deathdate.date = date_to_datetime(patient_data["DEATH_DATE"])
    patient.deceasedDateTime = deathdate

    return patient.as_json()


# entry point for PySpark application
if __name__ == '__main__':
    import yaml
    # init postgres DB
    with open('config.yaml') as f:
        config = yaml.safe_load(f)

    postgres_db = PostgresqlDB(None, **config['postgres_db'])

    import pprint
    pprint.pprint(get_patient('1'))


