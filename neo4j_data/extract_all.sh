#!/bin/bash -e


######
# Récupération des données pour les maladies
######

#Script qui :
#    - va récupérer dans les métadonnées les codes (ICD10, PMSI)
#    - va récupérer dans les métadonnées les noms des maladies par le code ICD10
#    - va récupérer les codes wikidata et UMLS à partir du code ICD10
#    - sauvegarde dans *diseases.csv*
python3 extractDiseasesAttributes.py

#Since some of the medical entities (drugs, symptoms, specialties) are linked to diseases via the wikidata codes,
#and since not all of the diseases nodes have a wikidata code attribute, we are going to scrape wikidata in order to
#enrich the disease nodes (represented by an ICD10 code) with wikidata codes.
#
#PS: The script takes several hours to complete running, so an output file is available in data/graph/output to facilitate
#the reuse of the results obtained.
#
#generates:
#    - mapping_wiki_icd10.csv  -> mappinc code wikidata <-> UCD10
python3 scrapeWikidata.py



#A script that :
#    - looks into this wikipedia page : 'https://fr.wikipedia.org/wiki/Liste_d%27abr%C3%A9viations_en_m%C3%A9decine'
#    in order to extract the abbreviations of medical terms (diseases for now).
#    - gets the wikidata codes associated to these concepts
#    - gets the ICD10 codes associated to these wikidata codes
#    - saves the results to a json file *abbreviations.json*
python3 extractAbbreviations.py


######
# Récupération des données pour les autres concepts
######

#Script qui :
#    - lit *disease_biology23072020.tsv* qui contient les liens Biologie <-> Maladie :
#        - bio : CONCEPT_CD_DXCARENUM
#        - maladie : CONCEPT_CD_PMSI
#        - value : poids du lien
#    - lit le fichier *concept_dimension.csv* qui contient toutes les entités des métadonnées
#    - merge les 2 pour garder, pour chaque lien, le nom de l'examen biologique
#    - récupère le type d'examen bio depuis les métadonnées via CONCEPT_CD_DXCARENUM
#    - sauvegarde dans *biology.csv*
python3 extractDiseaseBiology.py


#Script qui :
#    - va récupérer dans wikidata les spécialités associées au maladies (par code wikidata des maladies)
#        - pas de croisement avec les PMSI connus
#    - sauvegarde vers *specialties.csv*
python3 WikidataExtractDiseaseSpecialty.py


#Script qui :
#    - va récupérer dans wikidata les symptomes associées au maladies (par code wikidata des maladies)
#        - pas de croisement avec les PMSI connus
#    - récupération dans wikidata des codes CUI par code wikidata des symptomes)
#    - lecture du fichier *frenchTerminoUMLS2019AB.csv* qui liste des synonymes pour tous types de concepts, par code CUI
#    - on ne garde que les synonymes des symptômes
#    - sauvegarde dans *symptoms.csv*
python3 WikidataExtractDiseaseSymptoms.py



#Script qui :
#    - va récupérer dans wikidata les liens entre maladies et molécules (par codes wikidata + drugLabel)
#        - pas de croisement avec les PMSI connus
#    - sauvegarde dans *wiki-DiseaseDrugs-21072020.tsv*
#    - récupération via Romedi de RomediUri:
#        - on teste (et donc potentiellement on récupère) Ingrédients, Brand Names, Drug Classes
#    - on sauvegarde dans *wiki-DrugsLabelsMapping.tsv*
#    - on récupère via Romedi (romediURL:
#        - ucd (uri Romedi),
#        - cis
#        - IN, inlabel
#        - bn, bnlabel, ucd13, nimed,
#        - drugclass, drugclasslabel
#    /!\  Pas de différenciation dans les requètes...
#    - sauvegarde dans *drugs.csv*
python3 WikidataExtractDiseaseDrugs.py



######
# consolidation et export neo4j
######

#Ce script:
#    - récupère les données qui ont été scrappées / récupérées auparavant
#        - diseases.csv
#        - symptoms.csv
#        - specialties.csv
#        - drugs.csv
#        - mapping_wiki_icd10.csv
#    - enrichit les diseases avec des codes wikidata scrappés dans mapping_wiki_icd10 (merge sur ICD10)
python3 prepareDiseasesData.py



#This script will process the 'drugs.csv' in order to extract several files for integration into neo4j.
#The reason for not using 'drugs.csv' directly is that neo4j is not able to distinguish if the node already exists or not
#And we have multiple duplicates in our case.
#
#Generates :
#    - medoc.csv
#    - drugclass.csv
#    - ingredient.csv
#    - brand_name.csv
python3 prepareDrugsData.py