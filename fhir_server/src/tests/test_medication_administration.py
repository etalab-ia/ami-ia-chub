import sys, os
sys.path.append(os.path.abspath('..'))
import unittest
import fhirclient.models.medicationadministration as fhir_med_mod
import requests
from datetime import datetime
from pprint import pprint

from .utils_test import datetime_fromisoformat
from src import web


class MedicationAdministrationTest(unittest.TestCase):

    def setUp(self):
        self.app = None
        self.docker_adress = os.environ.get('TEST_DOCKER_ADRESS', None)
        if self.docker_adress is None:
            self.app = web.app.test_client()
        self.verbose = os.environ.get('TEST_VERBOSE', False)

    def _get_route(self, api_path):
        if self.docker_adress is not None:
            res = requests.get(f'http://{self.docker_adress}{api_path}')
            res.json = res.json()
            return res
        else:
            return self.app.get(api_path)
        
    def test_ressource_ok(self):
        # When
        patient_num = 1
        response = self._get_route(f'/patients/{patient_num}/medicationAdministrations')
        self.assertEqual(200, response.status_code)
        self._check_ressource(response.json)
        
        encounter_num = 22
        response = self._get_route(f'/encounters/{encounter_num}/medicationAdministrations')
        self.assertEqual(200, response.status_code)
        self._check_ressource(response.json)
        
    def _check_ressource(self, json_result):

        if self.verbose:
            pprint(json_result)

        self.assertIsInstance(json_result, list)
        for res in json_result:
            fhir_med_mod.MedicationAdministration(jsondict=res)

            self.assertEqual('MedicationAdministration', res['resourceType'])
            self.assertIn('identifier', res)
            for ident in res['identifier']:
                self.assertIn('value', ident)

            # not implemented because not in FHIR standard
            # self.assertIn('text', res)
            # self.assertIn('status', res['text'])
            # self.assertIn('div', res['text'])

            self.assertIn('status', res)

            self.assertIn('medicationReference', res)
            self.assertIn('reference', res['medicationReference'])

            self.assertIn('subject', res)
            self.assertIn('reference', res['subject'])
            self.assertEqual('Patient/', res['subject']['reference'][:len('Patient/')])

            self.assertIn('context', res)
            self.assertIn('reference', res['context'])
            self.assertEqual('Encounter/', res['context']['reference'][:len('Encounter/')])

            self.assertIn('effectiveDateTime', res)
            self.assertIsInstance(datetime_fromisoformat(res['effectiveDateTime']), datetime)

            self.assertIn('contained', res)
            self.assertIsInstance(res['contained'], list)
            for med in res['contained']:
                self.assertEqual("Medication", med['resourceType'])
                # self.assertIn('id', med)
                self.assertIn('code', med)
                self.assertIn('coding', med['code'])
                for coding in med['code']['coding']:
                    self.assertIn('system', coding)
                    self.assertIn('code', coding)
                    self.assertIn('display', coding)
                self.assertIn('text', med['code'])

            if 'dosage' in res:
                self.assertIn('dose', res['dosage'])
                self.assertIn('value', res['dosage']['dose'])

    def test_ressource_failure(self):
            # When
            response = self._get_route(f'/patients/test/medicationAdministrations')
            self.assertEqual(404, response.status_code)

            response = self._get_route(f'/patients//medicationAdministrations')
            self.assertEqual(404, response.status_code)

            response = self._get_route('/encounters/test/medicationAdministrations')
            self.assertEqual(404, response.status_code)

            response = self._get_route('/encounters//medicationAdministrations')
            self.assertEqual(404, response.status_code)

    # def tearDown(self):
    #     pass