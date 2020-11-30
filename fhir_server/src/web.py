from flask import Flask, abort, jsonify
from werkzeug.exceptions import HTTPException
import json
import logging.config

from utils.db_connect import PostgresqlDB, SparqlDB
from utils.config_parser import get_local_file, parse_full_config
import patient
import encounter
import observation
import diagnostic_report
import medicationAdministration
import procedure
import claim
import questionnaireResponse
import bacteriologie

# init postgres DB
config = parse_full_config(get_local_file('config.yaml'), get_local_file('config_env.yaml'))
logging.config.fileConfig(get_local_file('logging.ini'))
logging.getLogger().setLevel(config['app']['log_level'])

logger = logging.getLogger('Flask')
logger.debug('Creating app')

# base port is 5000
app = Flask(__name__)
app.config.from_object('config.Config')

postgres_db = PostgresqlDB(app)
sparql_db = SparqlDB(**config['sparql_db'])


##########
# Handle errors
##########

def handle_bad_request(e):
    logger.debug(str(e))
    return 'bad request!', 400


app.register_error_handler(400, handle_bad_request)


@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        # "description": e.description,
    })
    response.content_type = "application/json"
    logger.error(str(e))
    return response


@app.errorhandler(404)
def resource_not_found(e):
    logger.info(str(e))
    return jsonify({'error': str(e)}), 404


########
# API routes
#######

def process_data(ressource_desc, func, *args):
    try:
        return jsonify(func(*args))
    except ValueError as e:
        print(e)
        abort(404, description=f"Resource not found : {ressource_desc}")
    except Exception as e:
        print(e)
        abort(500, description=f"Unknow error : {e}")


@app.route('/patients/<patient_num>')
def get_patient(patient_num):
    return process_data(f"Patient with PATIENT_NUM = {patient_num}",
                        patient.get_patient, patient_num)


@app.route('/encounters/<encounter_num>')
def get_encounter(encounter_num):
    return process_data(f"Encounter with ENCOUNTER_NUM = {encounter_num}",
                        encounter.get_encounter, encounter_num)


@app.route('/patients/<patient_num>/labResults')
def get_labresults_patient(patient_num):
    return process_data(f"Observations for PATIENT_NUM = {patient_num}",
                        observation.get_obs_for_patient, patient_num)


@app.route('/encounters/<encounter_num>/labResults')
def get_labresults_encounter(encounter_num):
    return process_data(f"Observations for ENCOUNTER_NUM = {encounter_num}",
                        observation.get_obs_for_encounter, encounter_num)


@app.route('/patients/<patient_num>/clinicalReports')
def get_clinicalreport_patient(patient_num):
    return process_data(f"Diag Reports for PATIENT_NUM = {patient_num}",
                        diagnostic_report.get_report_for_patient, patient_num)


@app.route('/encounters/<encounter_num>/clinicalReports')
def get_clinicalreport_encounter(encounter_num):
    return process_data(f"Diag Reports for ENCOUNTER_NUM = {encounter_num}",
                        diagnostic_report.get_report_for_encounter, encounter_num)


@app.route('/patients/<patient_num>/medicationAdministrations')
def get_medication_patient(patient_num):
    return process_data(f"Medication Administrations for PATIENT_NUM = {patient_num}",
                        medicationAdministration.get_med_for_patient, patient_num)


@app.route('/encounters/<encounter_num>/medicationAdministrations')
def get_medication_encounter(encounter_num):
    return process_data(f"Medication Administrations for ENCOUNTER_NUM = {encounter_num}",
                        medicationAdministration.get_med_for_encounter, encounter_num)


@app.route('/patients/<patient_num>/procedures')
def get_procedure_patient(patient_num):
    return process_data(f"Procedures for PATIENT_NUM = {patient_num}",
                        procedure.get_proc_for_patient, patient_num)


@app.route('/encounters/<encounter_num>/procedures')
def get_procedure_encounter(encounter_num):
    return process_data(f"Procedures for ENCOUNTER_NUM = {encounter_num}",
                        procedure.get_proc_for_encounter, encounter_num)


@app.route('/patients/<patient_num>/pmsis')
def get_pmsi_patient(patient_num):
    return process_data(f"PMSIs for PATIENT_NUM = {patient_num}",
                        claim.get_pmsis_for_patient, patient_num)


@app.route('/encounters/<encounter_num>/pmsis')
def get_pmsi_encounter(encounter_num):
    return process_data(f"PMSIs for ENCOUNTER_NUM = {encounter_num}",
                        claim.get_pmsis_for_encounter, encounter_num)


@app.route('/patients/<patient_num>/questionnaireResponses')
def get_quest_patient(patient_num):
    return process_data(f"Questionnaire Responses for PATIENT_NUM = {patient_num}",
                        questionnaireResponse.get_quest_for_patient, patient_num)


@app.route('/encounters/<encounter_num>/questionnaireResponses')
def get_quest_encounter(encounter_num):
    return process_data(f"Questionnaire Responses for ENCOUNTER_NUM = {encounter_num}",
                        questionnaireResponse.get_quest_for_encounter, encounter_num)


@app.route('/patients/<patient_num>/bacteriology')
def get_bacterio_patient(patient_num):
    return process_data(f"Bacteriology for PATIENT_NUM = {patient_num}",
                        bacteriologie.get_synergy_for_patient, patient_num)


@app.route('/encounters/<encounter_num>/bacteriology')
def get_bacterio_encounter(encounter_num):
    return process_data(f"Bacteriology for ENCOUNTER_NUM = {encounter_num}",
                        bacteriologie.get_synergy_for_encounter, encounter_num)


if __name__ == "__main__":
    if config['app']['preload_metadata']:
        logger.info('Preloading metadata...')
        logger.info('       for observations')
        observation._get_request_1()
        logger.info('       for diagnostic reports')
        diagnostic_report._get_request_1()
        logger.info('       for medication administrations')
        medicationAdministration._get_request_1()
        logger.info('       for procedures')
        procedure._get_request_1()
        procedure._get_request_2()
        logger.info('       for claims')
        claim._get_request_1()
        claim._get_request_2()
        logger.info('       for questionnaireResponses')
        questionnaireResponse._get_request_1()
        questionnaireResponse._get_request_2()
        questionnaireResponse._get_request_3()
        questionnaireResponse._get_request_4()
        logger.info('       for bacteriology')
        bacteriologie._get_request_1()
        bacteriologie._get_request_2()

    logger.info('Starting FHIR API')
    app.run()