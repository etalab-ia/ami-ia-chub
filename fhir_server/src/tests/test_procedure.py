import sys, os
sys.path.append(os.path.abspath('..'))
import unittest
import fhirclient.models.procedure as fhir_procedure_mod
import requests
from datetime import datetime
from pprint import pprint

from .utils_test import datetime_fromisoformat
from src import web


class ProcedureTest(unittest.TestCase):

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
        patient_num = 2
        response = self._get_route(f'/patients/{patient_num}/procedures')
        self.assertEqual(200, response.status_code)
        self._check_ressource(response.json)
        
        encounter_num = 21
        response = self._get_route(f'/encounters/{encounter_num}/procedures')
        self.assertEqual(200, response.status_code)
        self._check_ressource(response.json)
        
    def _check_ressource(self, json_result):
        if self.verbose:
            pprint(json_result)

        self.assertIsInstance(json_result, list)
        for res in json_result:
            ## fhir_procedure_mod.Procedure(jsondict=res)  --> raises an error which is solved in fhirclient==4.0.0, not yet available on pip

            self.assertEqual('Procedure', res['resourceType'])
            self.assertIn('identifier', res)
            for ident in res['identifier']:
                self.assertIn('value', ident)

            self.assertIn('status', res)

            self.assertIn('category', res)
            self.assertIn('coding', res['category'])
            for coding in res['category']['coding']:
                self.assertIn('system', coding)
                self.assertIn('code', coding)
                self.assertIn('display', coding)

            self.assertIn('performedDateTime', res)
            self.assertIsInstance(datetime_fromisoformat(res['performedDateTime']), datetime)

            self.assertIn('subject', res)
            self.assertIn('reference', res['subject'])
            self.assertEqual('Patient/', res['subject']['reference'][:len('Patient/')])

            self.assertIn('encounter', res)
            self.assertIn('reference', res['encounter'])
            self.assertEqual('Encounter/', res['encounter']['reference'][:len('Encounter/')])

            self.assertIn('code', res)
            self.assertIn('coding', res['code'])
            for coding in res['code']['coding']:
                self.assertIn('system', coding)
                self.assertIn('code', coding)
                self.assertIn('display', coding)

    def test_ressource_failure(self):
        # When
        response = self._get_route(f'/patients/test/procedures')
        self.assertEqual(404, response.status_code)

        response = self._get_route(f'/patients//procedures')
        self.assertEqual(404, response.status_code)

        response = self._get_route('/encounters/test/procedures')
        self.assertEqual(404, response.status_code)

        response = self._get_route('/encounters//procedures')
        self.assertEqual(404, response.status_code)

    # def tearDown(self):
    #     pass