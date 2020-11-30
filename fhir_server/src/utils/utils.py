from datetime import datetime


def date_to_datetime(date):
    return datetime.combine(date, datetime.min.time())


def patient_num_to_ref(patient_num):
    return "Patient/{}".format(patient_num)


def encounter_num_to_ref(encounter_num):
    return "Encounter/{}".format(encounter_num)


def instance_num_to_ref(instance_num):
    return "Observation/{}".format(instance_num)