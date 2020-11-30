import pandas as pd
from itertools import cycle


def create(texts, nlp):
    """
    Create data frame containing the words from the observations

    :param texts: (list) a list of the observations
    :param nlp: the model
    :return: (data frame) a data frame with each line containing the number of the observation, the word and its tag
    """

    # create an empty data frame
    df = pd.DataFrame(columns=['Observation', 'Word', 'Tag'])

    for i, txt in enumerate(texts):
        doc = nlp(txt)
        for token in doc:
            entity = token.text
            df = df.append({'Observation': i, 'Word': entity}, ignore_index=True)

    return df


def fill_tags_column(df, tags):
    """
    Fill the tag column of the data frame using the medical tags

    :param df: (data frame) contains the observations
    :param tags: (list) the medical tags applied on the observations
    :return: (data frame)
    """
    # Use cycle on tags in order to go to the next element of the list when we're done with the current one
    tags_cycle = cycle(tags)

    # next_tag is the last tag checked
    next_tag = next(tags_cycle)

    for idx, row in df.iterrows():
        o = row['Observation']
        if o < next_tag[0]:
            continue
        w = row['Word']
        if (w == next_tag[1]) and (o == next_tag[0]):
            row['Tag'] = next_tag[4]
            next_tag = next(tags_cycle)

    return df


def bio_tagging(tags):
    """
    A function to apply BIO tagging on the tags
    BIO stands for BEGINNING, INSIDE and OUTSIDE
    So instead of having [MAL, MAL] as for [fièvre, continue], we will have [B-MAL, I-MAL]
    The model will then know that it is the same entity !

    :param tags: (list) the medical tags from the data frame
    :return: (list) the BIO tags
    """
    prev_tag = tags[0]
    bio_tags = []
    for tag in tags:
        if tag == 'O':
            bio_tags.append(tag)
            prev_tag = tag
            continue
        if tag != 'O' and  prev_tag == 'O':
            bio_tags.append('B-'+tag)
            prev_tag = tag
        elif tag != 'O' and prev_tag == tag:
            bio_tags.append('I-'+tag)
            prev_tag = tag
        elif tag != 'O' and prev_tag != tag:
            bio_tags.append('B-'+tag)
            prev_tag = tag
    return bio_tags

