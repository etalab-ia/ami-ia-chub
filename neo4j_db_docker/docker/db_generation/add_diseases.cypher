// Create Maladie
LOAD CSV WITH HEADERS FROM 'file:///db_generation/diseases.csv' AS line FIELDTERMINATOR '\t'
CREATE (m:Maladie {icd10 : line.ICD10, label : line.diseaseName, pmsi : line.PMSI, wikidata : line.Wikidata, umls : line.UMLS, abbreviations : line.abbreviation, synonyms : line.synonyms});
