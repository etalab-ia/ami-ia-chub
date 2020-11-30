from unidecode import unidecode


def get_exams(s):
    q = "SELECT ?l WHERE {   ?s <http://www.w3.org/2004/02/skos/core#broader> ?o . \
                            ?s <http://www.w3.org/2000/01/rdf-schema#label> ?l }"
    exams = s.query(q)
    return exams


def get_drugs(s):
    q = "SELECT ?o WHERE {   ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> \
                            <http://chu-bordeaux.fr/prescription-dxcare#drugCategory> . \
                            ?s <http://www.w3.org/2000/01/rdf-schema#label> ?o }"
    drugs = s.query(q)
    return drugs


def get_diseases(s):
    q = "SELECT ?o WHERE {   ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> \
                            <http://chu-bordeaux.fr/prescription-dxcare#protocol> . \
                            ?s <http://www.w3.org/2000/01/rdf-schema#label> ?o }"
    dis = s.query(q)
    return dis


def get_procedures(s):
    q = "SELECT ?l WHERE {  ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> \
                                <http://chu-bordeaux.fr/pmsi#procedureCode> . \
                                ?s <http://www.w3.org/2000/01/rdf-schema#label> ?l}"
    proc = s.query(q)
    return proc


def get_data(server):
    """
    A function to combine the above queries into a single dictionary

    :param server: the sparql endpoint
    :return: (dict) with the annotation data
    """

    # initialize the dictionary
    ann_dict = dict()
    ann_dict.setdefault("MAL", [])
    ann_dict.setdefault("MEDOC", [])
    ann_dict.setdefault("EXAM", [])
    ann_dict.setdefault("PROC", [])

    # Add the list of exams to the annotation dictionary
    exams = get_exams(server)
    for b in exams['results']['bindings']:
        ann_dict['EXAM'].append(unidecode(b['l']['value'].lower()))

    # Add the list of drugs to the annotation dictionary
    drugs = get_drugs(server)
    for b in drugs['results']['bindings']:
        ann_dict['MEDOC'].append(b['o']['value'].lower())

    # Add the list of diseases to the annotation dictionary
    diseases = get_diseases(server)
    for b in diseases['results']['bindings']:
        d = b['o']['value']
        # delete typos
        if d.lower() not in ['as', 'c', 'ide']:
            ann_dict['MAL'].append(unidecode(d.lower()))

    # Add the list of procedures to the annotation dictionary
    procedures = get_procedures(server)
    for b in procedures['results']['bindings']:
        ann_dict['PROC'].append(unidecode(b['l']['value'].lower()))

    return ann_dict
