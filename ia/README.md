IA in the project
==================

Context
-------
Since the Starclay's annotation solution was not used due to lack of time on the part of the CHU staff, we had to find 
another solution to overcome this problem, as the annotation phase is crucial to any IA task.

Methodology
-----------

Building the annotation dictionary
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The first step is to build the annotation dictionary, which contains the different medical terms (diseases, treatments, 
symptoms, biology, exams). To do so, different sources were used :

- Metadata sent by the CHU, the *get_data_from_bg.py* script allows to to query the graph database and get the data from it.
- Data from another Starclay project with a hospital organization.
- Data from [Wikidata](https://query.wikidata.org/), which allows to get structured data from Wikipedia.
- Data from csv files sent by the CHU, the *get_data_from_csv.py* script allows to pre-process data and put it in the right format.

Finally, the *final_ann_dict.py* script allows to merge the 2 annotation dictionaries and delete all duplicates.


Annotation
~~~~~~~~~~
The search in the dxcare app is conducted on 2 columns of the patient record (DPI), which are **OBSERVATION_BLOB** and 
**TVAL_CHAR**. Once those 2 columns are extracted and preprocessed (*preprocess_obs.py*), the annotation can be done on 
2 phases :

- Annotate the texts from the columns mentioned above using **PhraseMatcher** of SpaCy (*annotation.py*).
- Divide the texts into words and build a data frame which contains each word with its associated tag (*dataframe.py*).

In order to facilitate the prediction of the medical terms for the NER model, a method called BIO (**B** eginning **I** nside **O** utside) 
is used. It indicated whether the word is the first of the medical term (**B**) or not (**I**), or if it is out of the vocabulary (**O**).

For example : [fièvre, continue] will have this tag : [B-SYM, I-SYM]

Modelization
~~~~~~~~~~~~
TO DO