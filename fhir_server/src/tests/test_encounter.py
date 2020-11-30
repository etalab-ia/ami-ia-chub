import sys, os
sys.path.append(os.path.abspath('..'))
import unittest
import fhirclient.models.encounter as fhir_encounter_mod
import requests
from datetime import datetime
from pprint import pprint

from .utils_test import datetime_fromisoformat
from src import web


class EncounterTest(unittest.TestCase):

    def setUp(self):
        self.end_point = '/encounters/{encounter_num}'
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
        encounter_num = 22
        response = self._get_route(self.end_point.format(encounter_num=22))

        # Then
        if self.verbose:
            pprint(response.json)

        self.assertEqual(200, response.status_code)
        self.assertIsInstance(response.json, dict)

        fhir_encounter_mod.Encounter(jsondict=response.json)

        self.assertEqual('Encounter', response.json['resourceType'])
        self.assertEqual(str(encounter_num), response.json['id'])
        self.assertIn('identifier', response.json)
        for ident in response.json['identifier']:
            self.assertIn('system', ident)
            self.assertIn('value', ident)

        self.assertIn('status', response.json)
        self.assertIn('period', response.json)
        self.assertIn('start', response.json['period'])
        self.assertIsInstance(datetime_fromisoformat(response.json['period']['start']), datetime)
        self.assertIn('end', response.json['period'])
        self.assertIsInstance(datetime_fromisoformat(response.json['period']['end']), datetime)

        self.assertIn('type', response.json)
        self.assertIsInstance(response.json['type'], list)
        [self.assertIn('text', l) for l in response.json['type']]

        self.assertIn('subject', response.json)
        self.assertIn('reference', response.json['subject'])
        self.assertEqual('Patient/', response.json['subject']['reference'][:len('Patient/')])

        self.assertIn('location', response.json)
        self.assertGreaterEqual(len(response.json['location']), 1)
        for location in response.json['location']:
            self.assertIn('location', location)
            self.assertIn('reference', location['location'])
            self.assertIn('period', location)
            self.assertIn('start', location['period'])
            self.assertIsInstance(datetime_fromisoformat(location['period']['start']), datetime)
            self.assertIn('end', location['period'])
            self.assertIsInstance(datetime_fromisoformat(location['period']['end']), datetime)

    def test_ressource_failure(self):
        # When
        response = self._get_route(self.end_point.format(encounter_num="test"))
        self.assertEqual(404, response.status_code)

        response = self._get_route(self.end_point.format(encounter_num=''))
        self.assertEqual(404, response.status_code)

    # def tearDown(self):
    #     pass