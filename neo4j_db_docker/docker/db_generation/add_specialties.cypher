// Create Specialité
LOAD CSV WITH HEADERS FROM 'file:///db_generation/specialties.csv' AS line FIELDTERMINATOR '\t'
MERGE (m:Maladie {wikidata : line.diseaseWikidata})
WITH line, m
MERGE (s:Specialite {label : line.label, wikidata : line.wikidata})
WITH s,m
MERGE (m)-[:IS_PROCESSED_IN]->(s);