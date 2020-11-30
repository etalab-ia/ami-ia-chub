from itertools import cycle
from spacy.matcher import PhraseMatcher
from spacy.scorer import Scorer
from spacy.gold import GoldParse
import spacy
import random


def create_matcher(nlp, ann_dict):
    """
    Create the SpaCy PhraseMatcher to use for tagging the observations

    :param nlp: the model
    :param ann_dict: (dict) the annotation dictionary
    :return: the SpaCy PhraseMatcher
    """

    matcher = PhraseMatcher(nlp.vocab, attr='LOWER')

    for k, v in ann_dict.items():
        if k == 'LIBEL':
            continue
        matcher.add(k, None, *list(nlp.pipe(v)))

    return matcher


def tag_texts(nlp, matcher, texts):
    """
    Tag the observations with the medical tags from the annotation dictionary

    :param nlp: the nlp model
    :param matcher: the SpaCy PhraseMatcher
    :param texts: (list) the texts to annotate
    :return: (list) a list of the tags found in the texts in this format :
        [obs_number, entity, start_pos, end_pos(excluded), tag]
    """

    tags = []

    for i, txt in enumerate(texts):
        doc = nlp(txt)
        matches = matcher(doc)
        for m_id, start, end in matches:
            entity = doc[start: end]
            tags.append([i, entity.text, entity.start_char, entity.end_char, nlp.vocab.strings[m_id]])
    return tags


def fix_tags(tags):
    """
    A function to put the tags in the adequate format for the SpaCy NER modeling

    :param tags: (list) list of tags present in the texts
    :return: (list) list of the tags after fixing some issues
    """

    # Some of the terms appear in more than one category (for example, potassium is considered a BIO and TRAIT)
    # A first solution is to the first list when 2 list are equal except for the tag (the last element of the list)
    new_tags = []
    for i in range(len(tags) - 1):
        t1 = tags[i]
        t2 = tags[i+1]
        if t1[0] == t2[0] and t1[1] == t2[1] and t1[2] == t2[2] and t1[3] == t2[3] and t1[4] != t2[4]:
            continue
        new_tags.append(t1)

    # The second issue is : when there is a non-single tag to detect, PhraseMatcher detects it more than once
    # for example : it gives back (9, 'radio', 146, 147, 'EXAM'), (9, 'radio poignet', 146, 148, 'EXAM')
    # while it should give back only (9, 'radio poignet', 146, 148, 'EXAM')
    # to fix this, we delete the duplicates

    tags1 = []
    for i in range(len(new_tags) - 1):
        if (new_tags[i][1] in new_tags[i+1][1]) and (new_tags[i][2] == new_tags[i+1][2]) and \
                (new_tags[i][0] == new_tags[i + 1][0]):
            continue
        tags1.append(new_tags[i])

    final_tags = []
    for i in range(1, len(tags1)):
        if (tags1[i][1] in tags1[i-1][1]) and (tags1[i][3] == tags1[i-1][3]) and (tags1[i][0] == tags1[i-1][0]):
            continue
        final_tags.append(tags1[i])

    return final_tags


def format_data_4_spacy_ner_modeling(texts, tags):
    """
    A function that put the data into the format required by SpaCy

    :param texts: (list) the observations
    :param tags: (list) the medical tags applied on the observations
    :return: (list) a list of tuples, where the 1st element of the tuple is the observations and the 2nd is a dictionary
            The dictionary has 'entities' as key and a list of tuples as value. Each tuple is in the following format :
            [start_char , end_char , tag]
    """

    # initialize the list that will contain the final result
    data = []

    # initialize the cycle of the tags
    tags_cycle = cycle(tags)
    next_tag = next(tags_cycle)

    for i, obs in enumerate(texts):
        entities_dict = dict()
        entities_dict.setdefault('entities', [])
        while i == next_tag[0]:
            entities_dict['entities'].append((next_tag[2], next_tag[3], next_tag[4]))
            next_tag = next(tags_cycle)
        data.append((obs, entities_dict))

    return data


def filter_data(data):
    """
    A function that removes observations that do not contain tags (according to the annotation model = PhraseMatcher)

    :param data: (list) the spacy-formatted data
    :return: (list) the SpaCy-formatted data with only observations that contain at least one tag
    """

    # the list of observations with no tags
    to_drop_from_data = []

    for d in data:
        if len(d[1]['entities']) == 0:
            to_drop_from_data.append(d)

    new_data = [d for d in data if d not in to_drop_from_data]

    return new_data


def train_spacy(data, iterations, drop_rate):
    """
    Function to train the spacy model

    :param data:
    :param iterations:
    :param drop_rate:
    :return:
    """
    TRAIN_DATA = data

    # create blank Language class
    nlp = spacy.blank('fr')

    # create the built-in pipeline components and add them to the pipeline
    # nlp.create_pipe works for built-ins that are registered with spaCy
    if 'ner' not in nlp.pipe_names:
        ner = nlp.create_pipe('ner')
        nlp.add_pipe(ner, last=True)

    # add labels
    for _, annotations in TRAIN_DATA:
        for ent in annotations.get('entities'):
            ner.add_label(ent[2])

    # get names of other pipes to disable them during training
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe != 'ner']
    with nlp.disable_pipes(*other_pipes):  # only train NER
        optimizer = nlp.begin_training()
        for itn in range(iterations):
            print("Statring iteration " + str(itn))
            random.shuffle(TRAIN_DATA)
            losses = {}
            for text, annotations in TRAIN_DATA:
                nlp.update(
                    [text],  # batch of texts
                    [annotations],  # batch of annotations
                    drop=drop_rate,  # dropout - make it harder to memorise data
                    sgd=optimizer,  # callable to update weights
                    losses=losses)
            print(losses)
    return nlp


def evaluate_model_spacy_scorer(model, data_set):
    """
    A function that returns the SpaCy Scorer containing SpaCy default metrics

    :param model: the SpaCy model
    :param data_set: (list) the SpaCy formatted data set on which the model will be evaluated
    :return: a SpaCy Scorer
    """

    # Initialize the SpaCy scorer
    scorer = Scorer()

    for i in range(len(data_set)):
        sents, ents = data_set[i]
        doc_gold = model.make_doc(sents)
        gold = GoldParse(doc_gold, entities=ents['entities'])
        predicted_value = model(sents)
        scorer.score(predicted_value, gold)

    # Print the results
    print('-- Precision (default SpaCy metric):', round(scorer.ents_p, 2), '%')
    print('-- Recall (default SpaCy metric):', round(scorer.ents_r, 2), '%')
    print('-- F-score (default SpaCy metric):', round(scorer.ents_f, 2), '%')

    return scorer

