# Data Directory
This directory contains all the data files used in this project, whether it was for creating the knowledge graph or for 
the IA task (the NER model).

## graph
The `graph` directory has the different data files used for generating the knowledge graph, they are as follows :
- `nodes.csv`, `has_names.csv`, `is_exam_for.csv`, `is_medicine_for.csv`, `is_speciality_of.csv` and `is_symptom_of.csv` 
are all raw data extracted from [Wikidata](https://query.wikidata.org/) and representing the different links or 
relations between the disease and other medical entities (symptoms, treatments,exams..).

The rest of the files were used in order to enrich the above relations between diseases and other medical entities :
- `nom_medicaments.csv` is the result of the scraping of [this website](http://base-donnees-publique.medicaments.gouv.fr/)
and which contains the names of the medicated treatments in order to differentiate between treatments.
- `frenchTerminoUMLS2019AB.csv` and `query_SPARQL_Codes_Wiki.csv` were provided by the CHU so we can assign a UMLS code,
a Wikidata code and synonyms to each symptom.
- `frequence_total_codes_pmsi.csv` and `concatDenombrement` : provided by the CHU as well and contain respectively 
the number of stays where the biology term appears (among 1,564,054 stays) and the enumeration of the PMSI codes 
conditioned on the appearance of the biology term. These 2 files were used to establish a relation between a disease 
(PSMI code) and the biology terms.

Finally, the `output` directory contains the final csv files that will be used for the knowledge graph construction.

## ia
The `ia` directory contains the different files related to the data collection and the modelization :
- `dpi.csv` : a sample of a patient record.
- `exams.csv` and `symptoms.csv` are 2 files extracted from Wikidata to enrich the annotation dictionary.
- `biologie_diabete2.xlsx`, `diabete_concepts.csv` and `frq_terms_biology.csv` are files provided by the CHU and used to
enrich the annotation dictionary.