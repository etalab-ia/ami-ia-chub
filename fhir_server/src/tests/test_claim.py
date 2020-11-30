import sys, os
sys.path.append(os.path.abspath('..'))
import unittest
import fhirclient.models.claim as fhir_claim_mod
import requests
from datetime import datetime
from pprint import pprint

from .utils_test import datetime_fromisoformat
from src import web


class PMSITest(unittest.TestCase):

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
        response = self._get_route(f'/patients/{patient_num}/pmsis')
        self.assertEqual(200, response.status_code)
        self._check_ressource(response.json)
        
        encounter_num = 22
        response = self._get_route(f'/encounters/{encounter_num}/pmsis')
        self.assertEqual(200, response.status_code)
        self._check_ressource(response.json)
        
    def _check_ressource(self, json_result):

        if self.verbose:
            pprint(json_result)

        self.assertIsInstance(json_result, list)
        for res in json_result:
            fhir_claim_mod.Claim(jsondict=res)

            self.assertEqual('Claim', res['resourceType'])

            self.assertIn('identifier', res)
            for ident in res['identifier']:
                self.assertIn('value', ident)

            # not implemented because not in FHIR standard
            # self.assertIn('text', res)
            # self.assertIn('status', res['text'])
            # self.assertIn('div', res['text'])

            self.assertIn('status', res)

            self.assertIn('type', res)
            self.assertIn('coding', res['type'])
            for coding in res['type']['coding']:
                self.assertIn('system', coding)
                self.assertIn('code', coding)

            self.assertIn('created', res)
            self.assertIsInstance(datetime_fromisoformat(res['created']), datetime)

            self.assertIn('patient', res)
            self.assertIn('reference', res['patient'])
            self.assertEqual('Patient/', res['patient']['reference'][:len('Patient/')])

            self.assertIn('item', res)
            for item in res['item']:
                self.assertIn('encounter', item)
                for encounter in item['encounter']:
                    self.assertIn('reference', encounter)
                    self.assertEqual('Encounter/', encounter['reference'][:len('Encounter/')])

            if 'diagnosis' in res:
                self.assertIsInstance(res['diagnosis'], list)
                for diag in res['diagnosis']:
                    self.assertIn('diagnosisCodeableConcept', diag)
                    self.assertIn('coding', diag['diagnosisCodeableConcept'])
                    for coding in diag['diagnosisCodeableConcept']['coding']:
                        self.assertIn('system', coding)
                        self.assertIn('code', coding)
                        self.assertIn('display', coding)

                    if 'type' in diag:
                        for typ in diag["type"]:
                            self.assertIn('coding', typ)
                            for coding in typ['coding']:
                                self.assertIn('system', coding)
                                self.assertIn('code', coding)

            if 'procedure' in res:
                self.assertIsInstance(res['procedure'], list)
                for proc in res['procedure']:
                    self.assertIn('procedureCodeableConcept', proc)
                    self.assertIn('coding', proc['procedureCodeableConcept'])
                    for coding in proc['procedureCodeableConcept']['coding']:
                        self.assertIn('system', coding)
                        self.assertIn('code', coding)
                        self.assertIn('display', coding)

    def test_ressource_failure(self):
        # When
        response = self._get_route(f'/patients/test/pmsis')
        self.assertEqual(404, response.status_code)

        response = self._get_route(f'/patients//pmsis')
        self.assertEqual(404, response.status_code)

        response = self._get_route('/encounters/test/pmsis')
        self.assertEqual(404, response.status_code)

        response = self._get_route('/encounters//pmsis')
        self.assertEqual(404, response.status_code)

    # def tearDown(self):
    #     pass