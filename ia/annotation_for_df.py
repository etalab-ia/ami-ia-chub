from spacy.matcher import PhraseMatcher


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
            tags.append([i, entity.text, entity.start, entity.end, nlp.vocab.strings[m_id]])
    return tags


def fix_tags(tags):
    """
    A function to put the tags in the adequate format to complete the data frame

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

    tags2 = []
    for i in range(1, len(tags1)):
        if (tags1[i][1] in tags1[i-1][1]) and (tags1[i][3] == tags1[i-1][3]) and (tags1[i][0] == tags1[i-1][0]):
            continue
        tags2.append(tags1[i])

    # The final fix is to separate non-single tags ('epanchement pleural' to 'epanchement' and 'pleural'), in order
    # to be able to fill the tag column in the data frame
    final_tags = []
    for t in tags2:
        ts = t[1].split()
        if len(ts) > 1:
            for i, elt in enumerate(ts):
                to_add = t.copy()
                to_add[1] = elt
                to_add[2] += i
                to_add[3] = to_add[2] + 1
                final_tags.append(to_add)
        else:
            final_tags.append(t)

    return final_tags
