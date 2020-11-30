from neo4j import GraphDatabase
import json

"""
Exemple de requète neo4j permettant de récupérer pour une maladie données tous les médicaments associés,
puis les ingrédients et les noms commerciaux de ces médicaments.

Le résultat est écrit en json dans result.json

:author: Aymen Dabghi
"""

# connect to noe4j
uri = "bolt://localhost:7687"
driver = GraphDatabase.driver(uri, auth=("neo4j", "test"))


def find_disease_nodes(tx, name):
    # list to store the diseases nodes
    diseases_nodes = []

    # query
    result = tx.run(
        "MATCH (m:Maladie)<-[:IS_TREATMENT_FOR]-(med:Medicament) "
        "WHERE TOUPPER(m.label) CONTAINS TOUPPER($name) "
        "RETURN m, med;"
        , name=name)

    for record in result:
        diseases_nodes.append(record)

    return diseases_nodes


with driver.session() as session:
    """
    Récupération de tous les noeuds de type "Medicament" ayant un lien "is_treatment_for" avec un noeud de type 
    "Maladie" contenant pneumopathie dans son label
    
    les codes CIS sont mise dans :var cis_label:
    """
    diseases = session.read_transaction(find_disease_nodes, "pneumopathie")
    res = dict()
    m = diseases[0]['m']
    res['Maladie'] = {'label': m['label'], 'umls': m['umls'], 'wikidata': m['wikidata'], 'pmsi': m['pmsi'],
                      'icd10': m['icd10'], 'abbreviations': m['abbreviations'], 'synonyms': m['synonyms']}
    res['Médicament'] = []

    # a variable that stocks the cis code and the label in order to look for the ingredient and the brand name
    cis_label = []

    for d in diseases:
        med = d['med']
        cis_label.append((med['cis'], med['label']))
        res['Médicament'].append({'label': med['label'], 'cis': med['cis']})


def find_ingredient_and_brand_name(tx, cis, label):
    nodes = []
    result = tx.run("MATCH (i:Ingredient)<-[:IS_COMPOSED_OF]-(med:Medicament "
                    "{cis:$cis, label:$label})-[:IS_SOLD_AS]->(bn:Nom_commercial) RETURN med,bn,i;",
                    cis=cis, label=label)
    for record in result:
        nodes.append(record)
    return nodes


with driver.session() as session:
    """
    Pour chaque code CIS récupéré à l'étape précédente, on récupère les ingrédients et les noms commerciaux
    """
    for elt in cis_label:
        cis = elt[0]
        label = elt[1]
        treat = session.read_transaction(find_ingredient_and_brand_name, cis, label)

        # find index
        i = res['Médicament'].index({'label': treat[0]['med']['label'], 'cis': treat[0]['med']['cis']})

        res['Médicament'][i]['nom_commercial'] = {'label': treat[0]['bn']['label'], 'romedi': treat[0]['bn']['romedi'],
                                                  'nimed': treat[0]['bn']['nimed'], 'ucd13': treat[0]['bn']['ucd13']}

        res['Médicament'][i]['ingrédient'] = {'label': treat[0]['i']['label'], 'romedi': treat[0]['i']['romedi'],
                                              'wikidata': treat[0]['i']['wikidata']}

with open('result.json', 'w') as fp:
    json.dump(res, fp)