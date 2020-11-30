#!/usr/bin/python
# coding: utf8
import fhirclient.models.fhirreference as fhir_ref_mod
import fhirclient.models.identifier as fhir_id_mod
import fhirclient.models.fhirdate as fhir_date_mod
import fhirclient.models.bundle as fhir_bundle_mod
import fhirclient.models.codeableconcept as fhir_cod_concept_mod
import fhirclient.models.coding as fhir_coding_mod
import fhirclient.models.diagnosticreport as fhir_diag_mod
import fhirclient.models.observation as fhir_obs_mod
from functools import lru_cache
from utils.db_connect import PostgresqlDB, SparqlDB
from utils.utils import date_to_datetime, patient_num_to_ref, instance_num_to_ref
import fhirclient.models.quantity as fhir_qty_mod


@lru_cache()
def _get_request_1():
    """
    Get and cache metadata search linking bacteriologicalSearch and its target

    :return: pd.Frame
    """
    server = SparqlDB()
    search = 'SELECT * WHERE {  ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://chu-bordeaux.fr/bacteriologie-synergy#bacteriologicalSearch> .\
                        ?s <http://www.w3.org/2004/02/skos/core#prefLabel> ?label .\
                        ?s <http://chu-bordeaux.fr/m2sitis/iso11179-3/mdr.owl#hasTarget> ?search .\
                        ?search <http://www.w3.org/2004/02/skos/core#prefLabel> ?sLabel }'
    res = server.load_data(search)
    hashed_map = {}
    for b in res['results']['bindings']:
        hashed_map[b['sLabel']['value']] = b['s']['value']
    return hashed_map


def get_bacterio_search_value(bacterio_search_label, default_value=""):
    """
    look for a bacteriologicalSearch by its label via _get_request_1()

    :param bacterio_search_label: str
    :param default_value: value to return if not found
    :return: str
    """
    res = _get_request_1()
    if bacterio_search_label in res:
        return res[bacterio_search_label]
    return default_value


# def get_bacterio_sensibility_label(code):
#     server = SparqlDB()
#     sen = 'SELECT * WHERE {  ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://chu-bordeaux.fr/bacteriologie-synergy#sensibilitySearch> .\
#                                 ?s <http://www.w3.org/2004/02/skos/core#prefLabel> ?label .\
#                                 ?s <http://chu-bordeaux.fr/m2sitis/iso11179-3/mdr.owl#isComponentOf> ?n .\
#                                 ?n <http://chu-bordeaux.fr/m2sitis/iso11179-3/mdr.owl#hasTarget> ?sen .\
#                                 ?sen <http://www.w3.org/2004/02/skos/core#prefLabel> ?senLabel .\
#                                 FILTER (regex(str(?senLabel), "' + code + '"))}'
#     res = server.load_data(sen)
#     if res is None:
#         return " "
#     for b in res['results']['bindings']:
#         return b['label']['value'] if b['label']['value'] else ""
#     return ""


# @lru_cache()
# def _get_request_3():
#     server = SparqlDB()
#     search = 'SELECT * WHERE {  ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://chu-bordeaux.fr/bacteriologie-synergy#organism> .\
#                                 ?s <http://www.w3.org/2004/02/skos/core#prefLabel> ?label .\
#                                 ?s <http://chu-bordeaux.fr/m2sitis/iso11179-3/mdr.owl#isComponentOf> ?n .\
#                                 ?n <http://chu-bordeaux.fr/m2sitis/iso11179-3/mdr.owl#hasTarget> ?id .\
#                                 ?id <http://www.w3.org/2004/02/skos/core#prefLabel> ?idLabel }'
#     return server.load_data(search)
#
#
# def get_display_identification(id_label, default_value=""):
#     res = _get_request_3()
#     if res is None:
#         return default_value
#     for b in res['results']['bindings']:
#         if id_label in b['idLabel']['value'] and b['label']['value']:
#             return b['label']['value']
#     return default_value


@lru_cache()
def _get_request_2():
    """
    Get and cache metadata search linking antibiotic and its prefLabel

    :return: pd.Frame
    """
    server = SparqlDB()
    ident = 'SELECT * WHERE {  ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://chu-bordeaux.fr/bacteriologie-synergy#antibiotic> .\
                                ?s <http://www.w3.org/2004/02/skos/core#prefLabel> ?prefLabel }'
    res = server.load_data(ident)
    hashed_map = {}
    for b in res['results']['bindings']:
        hashed_map[b['s']['value']] = b['prefLabel']['value']
    return hashed_map


def get_bacterio_antibiotic_label(antibiotic_code, default_value=""):
    """
    look for an antibitic label by its code, using _get_request_2():

    :param antibiotic_code: str, code of the antibiotic
    :param default_value: value to return if not found
    :return: str
    """
    res = _get_request_2()
    key = f"http://chu-bordeaux.fr/bacteriologie-synergy#antibiotic-{antibiotic_code}"
    if key in res:
        return res[key]
    return default_value


# def get_display_material(code):
#     server = SparqlDB()
#     materiel = "SELECT * WHERE {  ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://chu-bordeaux.fr/bacteriologie-synergy#material> .\
#                                 ?s <http://www.w3.org/2004/02/skos/core#prefLabel> ?label .\
#                                 ?s <http://chu-bordeaux.fr/m2sitis/iso11179-3/mdr.owl#isComponentOf> ?n .\
#                                 ?n <http://chu-bordeaux.fr/m2sitis/iso11179-3/mdr.owl#hasTarget> ?mat .\
#                                 ?mat <http://www.w3.org/2004/02/skos/core#prefLabel> ?matLabel }"
#     res = server.load_data(materiel)
#     if res is None:
#         return " "
#     for b in res['results']['bindings']:
#         if code in b['matLabel']['value']:
#             return b['label']['value'] if b['label']['value'] else ""
#     return ""


def get_synergy_for_patient(patient_num):
    """
    searches bacteriology for a given patient

    :param patient_num: str
    :return: [fhirclient.models.bundle.Bundle() as json]
    """
    return _process_synergy_request(
        """SELECT * FROM observation_fact WHERE "SOURCESYSTEM_CD" = 'SYNERGIE' AND "PATIENT_NUM" = """ + patient_num)


def get_synergy_for_encounter(encounter_num):
    """
    searches bacteriology for a given encounter

    :param encounter_num: str
    :return: [fhirclient.models.bundle.Bundle() as json]
    """
    return _process_synergy_request(
        """
        SELECT * FROM observation_fact WHERE "SOURCESYSTEM_CD" = 'SYNERGIE' AND "ENCOUNTER_NUM" = 
        """ + encounter_num)


def _process_synergy_request(sql_statement):
    """
    processes bacteriology for a sql_statement

    :param sql_statement: search statement
    :return: [fhirclient.models.bundle.Bundle() as json]
    """
    connect_to_db = PostgresqlDB()
    data_prelevements = connect_to_db.load_data(sql_statement)

    # get research identifiers
    bool_recherche = data_prelevements["CONCEPT_CD"].str.contains("^SYN|BACT:RECHERCHE_")
    instances_nums_recherche = data_prelevements[bool_recherche].INSTANCE_NUM.unique()

    # get results identifiers by research id
    instances_nums_results = {}
    for instance_num_rec in instances_nums_recherche:
        instances_nums_results[instance_num_rec] = data_prelevements.loc[(data_prelevements["TVAL_CHAR"] == str(instance_num_rec).replace(".0",""))
                                                      & (data_prelevements["MODIFIER_CD"] == "SYN|BACT:PRELEVEMENT_INSTANCE_NUM"), 'INSTANCE_NUM']

    # get results data by results id
    results_observations_data = {}
    for instance_num_rec in instances_nums_recherche:
        for instance_num_res in instances_nums_results[instance_num_rec]:
            results_observations_data[instance_num_res] = connect_to_db.load_data("""SELECT * FROM observation_fact WHERE "INSTANCE_NUM" = """ + str(instance_num_res))

    # create bundles
    data_by_instance = data_prelevements.groupby(["INSTANCE_NUM"])
    list_of_bundles = []
    for instance_num_rec, instance_num_rec_data in data_by_instance:
        # for each research
        encounter_num_str = str(instance_num_rec_data.iloc[0]["ENCOUNTER_NUM"]).replace(".0","")
        # create bundle
        bundle = fhir_bundle_mod.Bundle()
        # identifier attribute
        ident = fhir_id_mod.Identifier()
        ident.value = encounter_num_str + "_SYNERGY"
        # ident.value = str(row["ENCOUNTER_NUM"]).replace(".0", "")[0] + "_SYNERGY"
        bundle.identifier = ident
        # type attribute
        bundle.type = "collection"
        bundle.entry = []
        # print(group_data)

        # entry attribute
        diagnostic_entry = fhir_bundle_mod.BundleEntry()
        diagnostic_entry.fullUrl = "https://eds.chu-bordeaux.fr/fhir/DiagnosticReport/" + ident.value

        # diag report
        diagnosticReport = fhir_diag_mod.DiagnosticReport()
        diagnosticReport.identifier = [ident]
        # status attribute
        diagnosticReport.status = "final"
        # subject attribute
        ref_subject = fhir_ref_mod.FHIRReference()
        ref_subject.reference = patient_num_to_ref(str(instance_num_rec_data.iloc[0]["PATIENT_NUM"]).replace(".0",""))
        # ref_subject.reference = patient_num_to_ref(str(row["PATIENT_NUM"]).replace(".0", ""))
        diagnosticReport.subject = ref_subject
        # issued attribute
        issued = fhir_date_mod.FHIRDate()
        issued.date = date_to_datetime(instance_num_rec_data.iloc[0]["START_DATE"])
        diagnosticReport.issued = issued

        category_codings = []
        # get code and catgeory codings by analysing rows
        for index, row in instance_num_rec_data.iterrows():
            if "@" in row["MODIFIER_CD"]:
                codeableconcept = fhir_cod_concept_mod.CodeableConcept()
                codeableconcept.coding = []
                coding = fhir_coding_mod.Coding()
                coding.system = "https://eds.chu-bordeaux.fr/SynergyBacteriology"
                coding.code = row["CONCEPT_CD"]
                coding.display = get_bacterio_search_value(coding.code)
                codeableconcept.coding = [coding]
                diagnosticReport.code = codeableconcept
            else:
                coding_categ = fhir_coding_mod.Coding()
                coding_categ.system = "https://eds.chu-bordeaux.fr/SynergyBacteriology"
                coding_categ.code = row["MODIFIER_CD"]
                coding_categ.display = row["TVAL_CHAR"] if row["TVAL_CHAR"] else ""
                category_codings.append(coding_categ)

        if diagnosticReport.code is None:
            # rare cases...
            codeableconcept = fhir_cod_concept_mod.CodeableConcept()
            codeableconcept.coding = []
            coding = fhir_coding_mod.Coding()
            coding.system = "https://eds.chu-bordeaux.fr/SynergyBacteriology"
            coding.code = "null"
            coding.display = ""
            codeableconcept.coding = [coding]
            diagnosticReport.code = codeableconcept

        category_coding = fhir_cod_concept_mod.CodeableConcept()
        category_coding.coding = category_codings
        diagnosticReport.category = category_coding

        diag_results = []
        # 1 result by line of results_observations_data
        for instance_num_res in instances_nums_results[instance_num_rec]:
            ref_result = fhir_ref_mod.FHIRReference()
            ref_result.reference = instance_num_to_ref(str(instance_num_res).replace('.0', ""))
            observation_data = results_observations_data[instance_num_res]
            for index, row in observation_data.iterrows():
                if "@" in row["MODIFIER_CD"]:
                    ref_result.display = row["TVAL_CHAR"] if row["TVAL_CHAR"] else ""
            diag_results.append(ref_result)

        diagnosticReport.result = diag_results
        diagnostic_entry.resource = diagnosticReport
        bundle.entry.append(diagnostic_entry)

        # get observations members (results for the current research)
        for instance_num_res in instances_nums_results[instance_num_rec]:
            # for each result
            instance_num_str = str(instance_num_res).replace(".0","")
            observation_entry = fhir_bundle_mod.BundleEntry()
            observation_entry.fullUrl = "https://eds.chu-bordeaux.fr/fhir/Observation/" + instance_num_str

            observation = fhir_obs_mod.Observation()
            observation_data = results_observations_data[instance_num_res]
            # identifier attribute
            ident_obs = fhir_id_mod.Identifier()
            ident_obs.value = encounter_num_str + "_" + instance_num_str
            observation.identifier = [ident_obs]
            # status attribute
            observation.status = "final"
            # subject attribute
            observation.subject = ref_subject
            # issued attribute
            issued = fhir_date_mod.FHIRDate()
            issued.date = date_to_datetime(observation_data.iloc[0]["START_DATE"])
            observation.issued = issued

            observation.hasMember = []

            for i, row in observation_data.iterrows():
                if "@" in row["MODIFIER_CD"]:
                    codeableconcept = fhir_cod_concept_mod.CodeableConcept()
                    codeableconcept.coding = []
                    coding = fhir_coding_mod.Coding()
                    coding.system = "https://eds.chu-bordeaux.fr/SynergyBacteriology"
                    coding.code = row["CONCEPT_CD"]
                    coding.display = row["TVAL_CHAR"] if row["TVAL_CHAR"] else ""
                    codeableconcept.coding = [coding]
                    observation.code = codeableconcept

                if 'SENSIBILITE' in row["MODIFIER_CD"]:
                    hasmember_ref = fhir_ref_mod.FHIRReference()
                    if "SYN|BACT:SENSIBILITE_" not in row["MODIFIER_CD"]:
                        continue
                    id_val = row["MODIFIER_CD"][len("SYN|BACT:SENSIBILITE_"):]
                    id_val = id_val.split('-')[0]
                    id_ref = encounter_num_str + "_" + instance_num_str + "_" + id_val
                    hasmember_ref.reference = instance_num_to_ref(id_ref)
                    observation.hasMember.append(hasmember_ref)

                if 'COMMENTAIRE' in row["MODIFIER_CD"]:
                    hasmember_ref = fhir_ref_mod.FHIRReference()
                    id_ref = encounter_num_str + "_" + instance_num_str + "_commentaires"
                    hasmember_ref.reference = instance_num_to_ref(id_ref)
                    observation.hasMember.append(hasmember_ref)

            observation_entry.resource = observation
            bundle.entry.append(observation_entry)

            # get observations quantities/interpretations or comments
            for instance_num_res in instances_nums_results[instance_num_rec]:
                instance_num_str = str(instance_num_res).replace(".0", "")
                observation_data = results_observations_data[instance_num_res]
                for i, row in observation_data.iterrows():
                    if 'SENSIBILITE' in row["MODIFIER_CD"]:
                        id_val = row["MODIFIER_CD"][len("SYN|BACT:SENSIBILITE_"):]
                        id_val = id_val.split('-')[0]
                        id_ref = encounter_num_str + "_" + instance_num_str + "_" + id_val

                        observation_quantity_entry = fhir_bundle_mod.BundleEntry()
                        observation_quantity_entry.fullUrl = "https://eds.chu-bordeaux.fr/fhir/Observation/" + id_ref

                        observation_quantity = fhir_obs_mod.Observation()
                        # identifier attribute
                        ident_obs = fhir_id_mod.Identifier()
                        ident_obs.value = id_ref
                        observation_quantity.identifier = [ident_obs]
                        # status attribute
                        observation_quantity.status = "final"
                        # subject attribute
                        observation_quantity.subject = ref_subject

                        codeableconcept = fhir_cod_concept_mod.CodeableConcept()
                        codeableconcept.coding = []
                        coding = fhir_coding_mod.Coding()
                        coding.system = "https://eds.chu-bordeaux.fr/SynergyBacteriology/Antibiotic"
                        coding.code = id_val
                        coding.display = get_bacterio_antibiotic_label(id_val)
                        codeableconcept.coding = [coding]
                        observation_quantity.code = codeableconcept

                        # valueQuantity attribute
                        quantity = fhir_qty_mod.Quantity()
                        quantity.value = row["NVAL_NUM"]
                        quantity.unit = row["UNITS_CD"] if row["UNITS_CD"] else ""
                        observation_quantity.valueQuantity = quantity
                        # interpretation attribute
                        codeableconcept_interpretation = fhir_cod_concept_mod.CodeableConcept()
                        codinginterpretation = fhir_coding_mod.Coding()
                        codinginterpretation.system = "https://eds.chu-bordeaux.fr/fhir/SynergyBacteriology"
                        codinginterpretation.code = row["MODIFIER_CD"]
                        codinginterpretation.display = row["TVAL_CHAR"] if row["TVAL_CHAR"] else None
                        codeableconcept_interpretation.coding = [codinginterpretation]
                        observation_quantity.interpretation = codeableconcept_interpretation

                        observation_quantity_entry.resource = observation_quantity
                        bundle.entry.append(observation_quantity_entry)

                    if 'COMMENTAIRE' in row["MODIFIER_CD"]:
                        id_ref = encounter_num_str + "_" + instance_num_str + "_commentaires"

                        observation_comment_entry = fhir_bundle_mod.BundleEntry()
                        observation_comment_entry.fullUrl = "https://eds.chu-bordeaux.fr/fhir/Observation/" + id_ref

                        observation_comment = fhir_obs_mod.Observation()
                        # identifier attribute
                        ident_obs = fhir_id_mod.Identifier()
                        ident_obs.value = id_ref
                        observation_comment.identifier = [ident_obs]
                        # status attribute
                        observation_comment.status = "final"
                        # subject attribute
                        observation_comment.subject = ref_subject

                        codeableconcept = fhir_cod_concept_mod.CodeableConcept()
                        codeableconcept.coding = []
                        coding = fhir_coding_mod.Coding()
                        coding.system = "https://eds.chu-bordeaux.fr/SynergyBacteriology"
                        coding.code = "TO_DO"
                        coding.display = "Commentaires"
                        codeableconcept.coding = [coding]
                        observation_comment.code = codeableconcept

                        # component
                        component = fhir_obs_mod.ObservationComponent()
                        valueCodeableConcept = fhir_cod_concept_mod.CodeableConcept()
                        codingcomponent = fhir_coding_mod.Coding()
                        codingcomponent.system = "https://eds.chu-bordeaux.fr/fhir/SynergyBacteriology"
                        codingcomponent.code = row["MODIFIER_CD"]
                        codingcomponent.display = row["TVAL_CHAR"] if row["TVAL_CHAR"] else None
                        valueCodeableConcept.coding = [codingcomponent]
                        component.valueCodeableConcept = valueCodeableConcept
                        component.valueString = row["TVAL_CHAR"] if row["TVAL_CHAR"] else None
                        component.code = component.valueCodeableConcept
                        observation_comment.component = [component]

                        observation_comment_entry.resource = observation_comment
                        bundle.entry.append(observation_comment_entry)

        # bug trouvé en testant   --> solved in fhirclient==4.0.0, not yet available on pip
        bundle_json = bundle.as_json()
        for i, entry in enumerate(bundle_json['entry']):
            if entry['resource']['resourceType'] == 'Observation':
                if 'hasMember' not in entry['resource'] \
                        and hasattr(bundle.entry[i].resource, "hasMember") and len(bundle.entry[i].resource.hasMember):
                    bundle_json['entry'][i]['resource']['hasMember'] = [m.as_json() for m in bundle.entry[i].resource.hasMember]
        list_of_bundles.append(bundle_json)
    return list_of_bundles


# entry point for PySpark application
if __name__ == '__main__':
    import yaml
    # init postgres DB
    with open('config.yaml') as f:
        config = yaml.safe_load(f)

    # postgres_db = PostgresqlDB(None, **config['postgres_db'])
    sparql_db = SparqlDB(**config['sparql_db'])
    #
    # import pprint
    # pprint.pprint(get_synergy_for_encounter('23'))
    # print(get_display_identification("803"))
    print(get_bacterio_antibiotic_label("803"))