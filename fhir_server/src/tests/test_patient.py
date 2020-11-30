import sys, os
sys.path.append(os.path.abspath('..'))
import unittest
import fhirclient.models.patient as fhir_patient_mod
import requests
from datetime import datetime
from pprint import pprint

from .utils_test import datetime_fromisoformat
from src import web


class PatientTest(unittest.TestCase):

    def setUp(self):
        self.end_point = '/patients/{patient_num}'
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
        response = self._get_route(self.end_point.format(patient_num=patient_num))

        # Then
        if self.verbose:
            pprint(response.json)

        self.assertEqual(200, response.status_code)
        self.assertIsInstance(response.json, dict)

        fhir_patient_mod.Patient(jsondict=response.json)

        self.assertEqual('Patient', response.json['resourceType'])
        self.assertEqual(str(patient_num), response.json['id'])
        self.assertIn('birthDate', response.json)
        self.assertIsInstance(datetime_fromisoformat(response.json['birthDate']), datetime)
        self.assertIn('deceasedDateTime', response.json)
        self.assertIsInstance(datetime_fromisoformat(response.json['deceasedDateTime']), datetime)
        self.assertIn('gender', response.json)
        self.assertIn('identifier', response.json)
        self.assertIn('system', response.json['identifier'][0])
        self.assertIn('value', response.json['identifier'][0])

        # not implemented because not in FHIR standard
        # self.assertIn('text', response.json)
        # self.assertIn('status', response.json['text'])
        # self.assertIn('div', response.json['text'])

    def test_ressource_failure(self):
        # When
        response = self._get_route(self.end_point.format(patient_num="test"))
        self.assertEqual(404, response.status_code)

        response = self._get_route(self.end_point.format(patient_num=''))
        self.assertEqual(404, response.status_code)

    # def tearDown(self):
    #     pass
