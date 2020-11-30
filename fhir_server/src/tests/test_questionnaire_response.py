import sys, os
sys.path.append(os.path.abspath('..'))
import unittest
import fhirclient.models.questionnaireresponse as fhir_quest_mod
import requests
from datetime import datetime
from pprint import pprint

from .utils_test import datetime_fromisoformat
from src import web


class QuestionnaireResponseTest(unittest.TestCase):

    def setUp(self):
        self.app = None
        self.docker_adress = 'localhost:5000'  # os.environ.get('TEST_DOCKER_ADRESS', None)
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
        response = self._get_route(f'/patients/{patient_num}/questionnaireResponses')
        self.assertEqual(200, response.status_code)
        self._check_ressource(response.json)
        
        encounter_num = 22
        response = self._get_route(f'/encounters/{encounter_num}/questionnaireResponses')
        self.assertEqual(200, response.status_code)
        self._check_ressource(response.json)
        
    def _check_ressource(self, json_result):
        if self.verbose:
            pprint(json_result)

        self.assertIsInstance(json_result, list)
        for res in json_result:
            ## fhir_quest_mod.QuestionnaireResponse(jsondict=res)  --> raises an error which is solved in fhirclient==4.0.0, not yet available on pip

            self.assertEqual('QuestionnaireResponse', res['resourceType'])
            self.assertIn('identifier', res)
            for ident in res['identifier']:
                self.assertIn('value', ident)

            self.assertIn('status', res)

            self.assertIn('subject', res)
            self.assertIn('reference', res['subject'])
            self.assertEqual('Patient/', res['subject']['reference'][:len('Patient/')])

            self.assertIn('encounter', res)
            self.assertIn('reference', res['encounter'])
            self.assertEqual('Encounter/', res['encounter']['reference'][:len('Encounter/')])

            self.assertIn('authored', res)
            self.assertIsInstance(datetime_fromisoformat(res['authored']), datetime)

            def _rec_item(current):
                self.assertIn('linkId', current)
                self.assertIn('text', current)

                # self.assertTrue(any(v in current for v in ['item', 'question', 'answer']))
                if 'item' in current:
                    self.assertIsInstance(res['item'], list)
                    ret = all([_rec_item(i) for i in current['item']])
                    self.assertTrue(ret)
                    return ret
                else:
                    if 'answer' in current:
                        for k in current['answer'][0].keys():
                            if k.index('value') == 0:
                                return True
                        if "valueCoding" in current['answer'][0]:
                            self.assertIn('system', current['answer'][0]['valueCoding'])
                            self.assertIn('code', current['answer'][0]['valueCoding'])
                            self.assertIn('display', current['answer'][0]['valueCoding'])
                            return True
                        return False
                    else:
                        self.assertTrue('QUESTION' in current['linkId'])
                        return True

            self.assertIn('item', res)
            self.assertIsInstance(res['item'], list)
            self.assertTrue(all([_rec_item(i) for i in res['item']]))

    def test_ressource_failure(self):
        # When
        response = self._get_route(f'/patients/test/questionnaireResponses')
        self.assertEqual(404, response.status_code)

        response = self._get_route(f'/patients//questionnaireResponses')
        self.assertEqual(404, response.status_code)

        response = self._get_route('/encounters/test/questionnaireResponses')
        self.assertEqual(404, response.status_code)

        response = self._get_route('/encounters//questionnaireResponses')
        self.assertEqual(404, response.status_code)

    # def tearDown(self):
    #     pass