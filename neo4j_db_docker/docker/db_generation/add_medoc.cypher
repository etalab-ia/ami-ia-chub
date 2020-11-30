// Create Medicament
LOAD CSV WITH HEADERS FROM 'file:///db_generation/medoc.csv' AS line FIELDTERMINATOR '\t'
MERGE (m:Maladie {wikidata : line.diseaseUri})
WITH line, m
MERGE (med:Medicament {label : line.CISLabel, cis : line.CIS})
WITH med, m
MERGE (med)-[:IS_TREATMENT_FOR]->(m);