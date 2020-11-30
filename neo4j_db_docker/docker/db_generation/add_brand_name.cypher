// Create Nom commercial
LOAD CSV WITH HEADERS FROM 'file:///db_generation/brand_name.csv' AS line FIELDTERMINATOR '\t'
MERGE (m:Medicament {label : line.CISLabel, cis : line.CIS})
WITH line, m
MERGE (b:Nom_commercial {label : line.BNlabel, romedi : line.BN, nimed : line.NIMED, ucd13 : line.UCD13})
WITH b, m
MERGE (m)-[:IS_SOLD_AS]->(b);