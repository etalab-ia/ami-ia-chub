Serveur API FHIR
================

Ce dossier contient le code permettant de builder le service docker d'API FHIR, de le configurer et de le lancer.


Description de l'API
--------------------

L'api permet d'interroger la base de données patient i2b2 et de récupérer les données demandées au format FHIR sérialisé en json 
([API FHIR](https://www.hl7.org/fhir/), voir wiki gitlab du projet)

Elle interroge aussi la base de métadonnées pour enrichir la réponse.


Les points API disponibles sont:

- /patients/<patient_num> - GET 
    -> fhir.Patient
- /encounters/<encounter_num> - GET
    -> fhir.Encounter
- /patients/<patient_num>/labResults - GET
    -> \[fhir.Observation\]
- /encounters/<encounter_num>/labResults - GET
    -> \[fhir.Observation\]
- /patients/<patient_num>/clinicalReports - GET
    -> \[fhir.DiagnosticReport\]
- /encounters/<encounter_num>/clinicalReports - GET
    -> \[fhir.DiagnosticReport\]
- /patients/<patient_num>/medicationAdministrations - GET
    -> \[fhir.MedicationAdministration\]
- /encounters/<encounter_num>/medicationAdministrations - GET
    -> \[fhir.MedicationAdministration\]
- /patients/<patient_num>/procedures - GET
    -> \[fhir.Procedure\]
- /encounters/<encounter_num>/procedures - GET
    -> \[fhir.Procedure\]
- /patients/<patient_num>/pmsis - GET
    -> \[fhir.Claim\]
- /encounters/<encounter_num>/pmsis - GET
    -> \[fhir.Claim\]
- /patients/<patient_num>/questionnaireResponses - GET
    -> \[fhir.QuestionnaireResponse\]
- /encounters/<encounter_num>/questionnaireResponses - GET
    -> \[fhir.QuestionnaireResponse\]
- /patients/<patient_num>/bacteriology - GET
    -> \[fhir.Bundle\]
- /encounters/<encounter_num>/bacteriology - GET
    -> \[fhir.Bundle\]
    
    
Si la ressource n'est pas trouvée, l'API retourne une erreur 404, et en cas d'erreur interne une erreur 500


/!\ IMPORTANT : certainrs ressources FHIR sont bugguées dans fhirclient==3.2.0 (certains champs ne sont pas pris en compte)
Ces bugs ont été corrigés dans le code du serveur pour assurer une sérialisation correcte.
Ces bugs sont aussi corrigés a priori dans fhirclient==4.0.0, qui n'est pour le moment pas déployé sur pip.
Il faudra upgrader dès que la version sera disponible.


Créer l'image
-------------

Pour créer l'image, utilisez le script suivant:

        ./build_docker.sh
        
Il crée l'image *starclay/fhir_api_server:latest*


Lancer l'image
--------------
        
Pour lancer l'image, le script suivant peut être appelé:

        ./run_fhir_api_server.sh
        
Les variables d'environnement suivantes peuvent être configurées dans run_fhir_api_server.sh:

- POSTGRESQL_HOST : adresse de la base i2b2
- POSTGRESQL_DBNAME: nom de la DB postgres i2b2
- POSTGRESQL_USER: user postgres
- POSTGRESQL_PWD: pwd de l'utilisateur
- SPARQL_HOST: point API Sparql de la base de métadonnées

- APP_LOG_LEVEL (defaut : DEBUG) : pour changer le niveau de log
- APP_PRELOAD_METADATA (défaut : True) : pour précharger les métadonnées au lancement.

Les requètes aux métadonnées peuvent être longues. Pour éviter un impact sur les performances, elles ont été implémentées 
de manière à être faites une fois et mises en cache. Cependant, le 1er appel à un point API peut être long. 
Précharger les métadonnées au démarrage ralenti un peu le démarrage du service, mais permet ensuite de ne pas avoir de délai 
lors de la consultation des ressources, même au 1er appel.


Tests
-----
        
Lancer les tests: dans src,

        python3 -m unittest discover .
        
        
Pour lancer les tests sur le service docker démarré (sur localhost:5000): dans src,

        TEST_DOCKER_ADRESS='localhost:5000' python3 -m unittest discover .
        
Pour que les json FHIR en réponse soient imprimés pendant les tests: dans src,

        TEST_VERBOSE=True python3 -m unittest discover . > tests.log
        
(cumulable avec TEST_DOCKER_ADRESS)


Contenu du dossier
-----------------

- fichiers du dossier : création et lancement du docker
- src/*.py :
    - web.py -> app flask gérant l'api
    - autres : création des ressources FHIR
    - utils : parsing de la config + connexions aux bases de données
    - tests : test de l'app via ses différents points API