// Create Ingrédient
LOAD CSV WITH HEADERS FROM 'file:///db_generation/ingredient.csv' AS line FIELDTERMINATOR '\t'
MERGE (m:Medicament {label : line.CISLabel, cis : line.CIS})
WITH line, m
MERGE (i:Ingredient {label : line.INlabel, romedi : line.IN, wikidata : line.drugUri})
WITH i, m
MERGE (m)-[:IS_COMPOSED_OF]->(i);