import sys, os
sys.path.append(os.path.abspath('..'))
import unittest
import fhirclient.models.observation as fhir_observation_mod
import requests
from datetime import datetime
from pprint import pprint

from .utils_test import datetime_fromisoformat
from src import web


class BiologyTest(unittest.TestCase):

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
        response = self._get_route(f'/patients/{patient_num}/labResults')
        self.assertEqual(200, response.status_code)
        self._check_ressource(response.json)
        
        encounter_num = 22
        response = self._get_route(f'/encounters/{encounter_num}/labResults')
        self.assertEqual(200, response.status_code)
        self._check_ressource(response.json)
        
    def _check_ressource(self, json_result):
        if self.verbose:
            pprint(json_result)

        self.assertIsInstance(json_result, list)
        for res in json_result:
            ## fhir_observation_mod.Observation(jsondict=res)  --> raises an error which is solved in fhirclient==4.0.0, not yet available on pip

            self.assertEqual('Observation', res['resourceType'])
            self.assertIn('identifier', res)
            for ident in res['identifier']:
                self.assertIn('value', ident)

            self.assertIn('status', res)

            self.assertIn('category', res)
            for cat in res['category']:
                self.assertIn('coding', cat)
                for coding in cat['coding']:
                    self.assertIn('system', coding)
                    self.assertIn('code', coding)

            self.assertIn('subject', res)
            self.assertIn('reference', res['subject'])
            self.assertEqual('Patient/', res['subject']['reference'][:len('Patient/')])

            self.assertIn('encounter', res)
            self.assertIn('reference', res['encounter'])
            self.assertEqual('Encounter/', res['encounter']['reference'][:len('Encounter/')])

            self.assertIn('effectiveDateTime', res)
            self.assertIsInstance(datetime_fromisoformat(res['effectiveDateTime']), datetime)

            self.assertIn('code', res)
            self.assertIn('coding', res['code'])
            for coding in res['code']['coding']:
                self.assertIn('system', coding)
                self.assertIn('code', coding)
                self.assertIn('display', coding)
            self.assertIn('text', res['code'])

            self.assertIn('valueQuantity', res)
            self.assertIn('value', res['valueQuantity'])
            self.assertIn('unit', res['valueQuantity'])

            self.assertIn('referenceRange', res)
            self.assertIn('text', res['referenceRange'][0])

    def test_ressource_failure(self):
        # When
        response = self._get_route(f'/patients/test/labResults')
        self.assertEqual(404, response.status_code)

        response = self._get_route(f'/patients//labResults')
        self.assertEqual(404, response.status_code)

        response = self._get_route('/encounters/test/labResults')
        self.assertEqual(404, response.status_code)

        response = self._get_route('/encounters//labResults')
        self.assertEqual(404, response.status_code)

    # def tearDown(self):
    #     pass