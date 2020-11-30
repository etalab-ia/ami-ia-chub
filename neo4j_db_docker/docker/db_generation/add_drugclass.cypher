// Create Classe thérapeutique
LOAD CSV WITH HEADERS FROM 'file:///db_generation/drugclass.csv' AS line FIELDTERMINATOR '\t'
MERGE (m:Medicament {label : line.CISLabel, cis : line.CIS})
WITH line, m
MERGE (c:Classe_therapeutique {label : line.drugClassLabel, romedi : line.drugClass})
WITH c, m
MERGE (m)-[:IS_IN]->(c);
