import sys, os
sys.path.append(os.path.abspath('..'))
import unittest
import fhirclient.models.bundle as fhir_bundle_mod
import requests
from datetime import datetime
from pprint import pprint

from .utils_test import datetime_fromisoformat
from src import web


class BacterioTest(unittest.TestCase):

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
        response = self._get_route(f'/patients/{patient_num}/bacteriology')
        self.assertEqual(200, response.status_code)
        self._check_ressource(response.json)
        
        encounter_num = 22
        response = self._get_route(f'/encounters/{encounter_num}/bacteriology')
        self.assertEqual(200, response.status_code)
        self._check_ressource(response.json)
        
    def _check_ressource(self, json_result):

        if self.verbose:
            pprint(json_result)

        self.assertIsInstance(json_result, list)
        for res in json_result:
            ## fhir_bundle_mod.Bundle(jsondict=res)   --> raises an error which is solved in fhirclient==4.0.0, not yet available on pip

            self.assertEqual('Bundle', res['resourceType'])
            self.assertIn('identifier', res)
            for ident in res['identifier']:
                self.assertIn('value', ident)

            self.assertIn('type', res)

            self.assertIn('entry', res)
            self.assertIsInstance(res['entry'], list)
            for entry in res['entry']:
                self.assertIn('fullUrl', entry)
                self.assertIn('resource', entry)
                resource = entry['resource']
                self.assertIn('resourceType', resource)
                self.assertIn('identifier', resource)
                for ident in resource['identifier']:
                    self.assertIn('value', ident)
                self.assertIn('status', resource)

                if 'category' in resource:
                    self.assertIn('coding', resource['category'])
                    for coding in resource['category']['coding']:
                        self.assertIn('system', coding)
                        self.assertIn('code', coding)
                        self.assertIn('display', coding)

                self.assertIn('code', resource)
                self.assertIn('coding', resource['code'])
                for coding in resource['code']['coding']:
                    self.assertIn('system', coding)
                    self.assertIn('code', coding)
                    self.assertIn('display', coding)

                self.assertIn('subject', resource)
                self.assertIn('reference', resource['subject'])
                self.assertEqual('Patient/', resource['subject']['reference'][:len('Patient/')])

                if "issued" in resource:
                    self.assertIsInstance(datetime_fromisoformat(resource['issued']), datetime)

                if "result" in resource:
                    for res in resource['result']:
                        self.assertIn('reference', res)
                        self.assertIn('display', res)

                if "hasMember" in resource:
                    for member in resource['hasMember']:
                        self.assertIn('reference', member)

                if "valueQuantity" in resource:
                    self.assertIn('value', resource['valueQuantity'])
                    self.assertIn('unit', resource['valueQuantity'])

                if "interpretation" in resource:
                    for coding in resource['interpretation']['coding']:
                        self.assertIn('system', coding)
                        self.assertIn('code', coding)
                        self.assertIn('display', coding)

                if "component" in resource:
                    for comp in resource['component']:
                        self.assertIn('valueCodeableConcept', comp)
                        self.assertIn('coding', comp['valueCodeableConcept'])
                        for coding in comp['valueCodeableConcept']['coding']:
                            self.assertIn('system', coding)
                            self.assertIn('code', coding)

    def test_ressource_failure(self):
        # When
        response = self._get_route(f'/patients/test/bacteriology')
        self.assertEqual(404, response.status_code)

        response = self._get_route(f'/patients//bacteriology')
        self.assertEqual(404, response.status_code)

        response = self._get_route('/encounters/test/bacteriology')
        self.assertEqual(404, response.status_code)

        response = self._get_route('/encounters//bacteriology')
        self.assertEqual(404, response.status_code)

    # def tearDown(self):
    #     pass