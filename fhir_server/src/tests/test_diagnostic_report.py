import sys, os
sys.path.append(os.path.abspath('..'))
import unittest
import fhirclient.models.diagnosticreport as fhir_diag_mod
from datetime import datetime
from pprint import pprint
import requests

from .utils_test import datetime_fromisoformat
from src import web


class ClinicalReportTest(unittest.TestCase):

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
        response = self._get_route(f'/patients/{patient_num}/clinicalReports')
        self.assertEqual(200, response.status_code)
        self._check_ressource(response.json)
        
        encounter_num = 22
        response = self._get_route(f'/encounters/{encounter_num}/clinicalReports')
        self.assertEqual(200, response.status_code)
        self._check_ressource(response.json)
        
    def _check_ressource(self, json_result):
        if self.verbose:
            pprint(json_result)

        self.assertIsInstance(json_result, list)
        for res in json_result:
            ## fhir_diag_mod.DiagnosticReport(jsondict=res)   --> raises an error which is solved in fhirclient==4.0.0, not yet available on pip

            self.assertEqual('DiagnosticReport', res['resourceType'])

            self.assertIn('identifier', res)
            for ident in res['identifier']:
                self.assertIn('value', ident)

            # not implemented because not in FHIR standard
            self.assertIn('conclusion', res)

            self.assertIn('status', res)

            self.assertIn('category', res)
            self.assertIn('coding', res['category'])
            for coding in res['category']['coding']:
                self.assertIn('system', coding)
                self.assertIn('code', coding)
                self.assertIn('display', coding)

            self.assertIn('subject', res)
            self.assertIn('reference', res['subject'])
            self.assertEqual('Patient/', res['subject']['reference'][:len('Patient/')])

            self.assertIn('encounter', res)
            self.assertIn('reference', res['encounter'])
            self.assertEqual('Encounter/', res['encounter']['reference'][:len('Encounter/')])

            self.assertIn('issued', res)
            self.assertIsInstance(datetime_fromisoformat(res['issued']), datetime)

            self.assertIn('code', res)
            self.assertIn('coding', res['code'])
            for coding in res['code']['coding']:
                self.assertIn('system', coding)
                self.assertIn('code', coding)
                self.assertIn('display', coding)
            self.assertIn('text', res['code'])

    def test_ressource_failure(self):
        # When
        response = self._get_route(f'/patients/test/clinicalReports')
        self.assertEqual(404, response.status_code)

        response = self._get_route(f'/patients//clinicalReports')
        self.assertEqual(404, response.status_code)

        response = self._get_route('/encounters/test/clinicalReports')
        self.assertEqual(404, response.status_code)

        response = self._get_route('/encounters//clinicalReports')
        self.assertEqual(404, response.status_code)

    # def tearDown(self):
    #     pass