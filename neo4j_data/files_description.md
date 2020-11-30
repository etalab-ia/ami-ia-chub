Description des fichiers input et output 
----------------------------------------

Fichiers input
~~~~~~~~~~~~~~

* **disease_biology23072020.tsv** : contient les liens maladie/biologie envoyés par le CHU :
    * CONCEPT_CD_DXCARENUM : code interne au CHU
    * CONCEPT_CD_PMSI : code interne au CHU
    * value : poids du lien entre la maladie et l'examen
    
* **concept_dimension.csv** : contient le mapping des concepts :
    * CONCEPT_PATH : chemin du concept
    * CONCEPT_CD : code du concept
    * NAME_CHAR : libellé du concept
    * CONCEPT_BLOB : 
    * UPLOAD_DATE : date de l'upload
    * DOWNLOAD_DATE : date du download
    * IMPORT_DATE : date de l'import
    * SOURCESYSTEM_CD :
    * UPLOAD_ID
    
* **frenchTerminoUMLS2019AB.csv** contient le mapping des codes UMLS :
    * CUI : code CUI (UMLS)
    * termino :
    * termeType :
    * code :
    * libelle : libellé de l'entité associée au code UMLS



Fichiers output
~~~~~~~~~~~~~~~

* **diseases_intermediate.csv** : contient les noeuds maladies, a comme attributs :
    * ICD10 : International Classification for Diseases V10
    * PMSI : code interne au CHU
    * diseaseName : nom de la maladie
    * Wikidata : code wikidata
    * UMLS : code UMLS (Unified Medical Language System)
    
* **diseases.csv** : contient les noeuds maladies, a exactement les mêmes attributs que diseases.csv, sauf qu'il contient plus de code wikidata.
    
* **biology.csv** : contient les noeuds examens biologiques :
    * CONCEPT_CD_PMSI : clé du lien vers maladie (code interne au CHU)
    * CONCEPT_CD_DXCARENUM : code interne au CHU
    * value : poids du lien entre la maladie et l'examen
    * NAME_CHAR : nom de l'examen biologique
    * type : type de l'examen biologique
    
* **specialties.csv** : contient les noeuds spécialités des maladies :
    * diseaseWikidata : clé du lien vers code wikidata de la maladie
    * label : nom de la spécialité médicale
    * wikidata : code wikidata de la spécialité
    
* **symptoms.csv** : contient les noeuds symptômes :
    * diseaseWikidata : clé du lien vers code wikidata de la maladie
    * prefLabel : libellé préféré du symptôme
    * wikidata : code wikidata du symptôme
    * CUI : Concept Unique Identifier
    * synonyms : les synonymes du symptôme s'il en existe
    * weight : poids du lien entre la maladie et le symptôme
    
* **wiki-DiseaseDrugs-21072020.tsv** : c'est le résultat de la requête sparql pour les liens maladie-traitement :
    * diseaseUri : code wikidata de la maladie
    * drugUri : code wikidata pour le traitement
    * drugLabel : libellé du traitement
    
* **wiki-DrugsLabelsMapping.tsv** : contient le mapping entre les libellés des traitements et leurs URI ROMEDI
    * DrugsLabels : libellé du traitement
    * RomediURI : URI ROMEDI du traitement
        
* **drugs.csv**: contient les attributs des noeuds médicaments :
    * diseaseUri : clé pour lien vers code wikidata de la maladie
    * drugUri : code wikidata pour le traitement
    * drugLabel : libellé du traitement
    * RomediURI : URI ROMEDI du traitement
    * UCD : URI ROMEDI de l'UCD13
    * UCD13 : code UCD13
    * NIMED : code NIMED (relatif au produit commercial)
    * CIS : code CIS (relatif au médicament)
    * CISLabel : nom du médicament
    * IN : URI ROMEDI de l'ingrédient
    * INlabel : libellé de l'ingrédient
    * BN : URI ROMEDI du nom commercial (Brand Name)
    * BNlabel : libellé du nom commercial
    * drugClass : URI ROMEDI de la classe thérapeutique
    * drugClassLabel : libellé de la classe thérapeutique
    
    Fichiers dérivés:

    - **medoc.csv** : contient les noeuds "médicaments" :
        * diseaseUri : clé pour lien vers maladie
        * CIS : code CIS (relatif au médicament)
        * CISLabel : nom du médicament
    
    - **brand_name.csv** : contient les noeuds "produit commercial" :
        * CIS : clé 1/2 pour lien vers médicament
        * CISLabel : clé 2/2 pour lien vers médicament         
        * UCD13 : code UCD13
        * NIMED : code NIMED (relatif au produit commercial)
        * BN : URI ROMEDI du nom commercial (Brand Name)
        * BNlabel : libellé du nom commercial
        
    - **drugclass.csv** : contient les noeuds "classe thérapeutique" :
        * CIS : clé 1/2 pour lien vers médicament
        * CISLabel : clé 2/2 pour lien vers médicament   
        * drugClass : URI ROMEDI de la classe thérapeutique
        * drugClassLabel : libellé de la classe thérapeutique
        
    - **ingredient.csv** : contient les noeuds "ingrédient" :
        * CIS : clé 1/2 pour lien vers médicament
        * CISLabel : clé 2/2 pour lien vers médicament   
        * IN : URI ROMEDI de l'ingrédient
        * INlabel : libellé de l'ingrédient
            