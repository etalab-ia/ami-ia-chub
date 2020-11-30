import string


def merge(bg_dict, csv_dict):
    """
    A function to merge the 2 annotation dictionaries after cleaning.
    csv_dict is the main annotation dictionary, so the pre-processing will be done one bg_dict.

    :param bg_dict: (dict) annotation dictionary containing data extracted from the blazegraph
    :param csv_dict: (dict) annotation dictionary containing data extracted from the csv files
    :return: (dict) a dictionary containing a global annotation
    """

    # TRAIT & LIBEL

    # add to csv_dict['TRAIT'], the drugs from bg_dict that :
    # - do not already exit in the annotation dict
    # - contain at most 2 words
    # - do not begin with the word 'autres'
    # the rest will be added to csv_dict['LIBEL']
    for drug in bg_dict['MEDOC']:
        if (len(drug.split()) < 3) and ('autres' not in drug.split()[0]) and (drug not in csv_dict['TRAIT']):
            csv_dict['TRAIT'].append(drug)
        elif (drug not in csv_dict['TRAIT']) and (drug not in csv_dict['LIBEL']):
            csv_dict['LIBEL'].append(drug)

    # remove outliers, which are drugs with length < 3
    for d in csv_dict['TRAIT']:
        if len(d) < 3:
            csv_dict['TRAIT'].remove(d)

    # MAL

    # Create a copy of bg_dict['MAL']
    mal = bg_dict['MAL'].copy()

    # A lot of pre-processing is needed to be done here :

    # - Delete the text after the word "si", after ":" and after a parenthesis as its only purpose
    # is to explain the case, the age category, the duration of the disease or the weight
    sep = ['si ', '(', ':']
    for s in sep:
        mal = [d.split(s, 1)[0] for d in mal]

    # - Some of the diseases start with a number ("1.", "2.") or a letter ("a.", "b.") so this needs to be taken care of
    to_be_added = []
    for d in mal:
        if d[1] == '.' or d[2] == '.':
            to_be_added.append(d.split(' ', 1)[1])
            mal = list(filter(d.__ne__, mal))

    # - We will add to this list all the first words already here as well as the first 2 words
    for d in mal:
        l = d.split()
        to_be_added.append(l[0])
        if len(l) > 1:
            to_be_added.append(' '.join(l[:2]))

    # - Delete the duplicates from this list and and add it to the dictionary
    mal = list(set(mal + to_be_added))
    mal = [m for m in mal if len(m) > 2]

    # Finally, concatenate the 2 lists and delete the duplicates
    csv_dict['MAL'] = list(set(csv_dict['MAL'] + mal))

    return csv_dict


def clean(ann_dict):
    """
    A function to put the annotation into lowercase and remove the punctuation

    :param ann_dict: (dict) the annotation dictionary
    :return: (dict) the final annotation dictionary
    """
    for k in ann_dict.keys():
        # lowercase
        ann_dict[k] = [v.lower() for v in ann_dict[k]]
        # remove punctuation
        ann_dict[k] = [v.translate(str.maketrans('', '', string.punctuation)) for v in ann_dict[k]]
        # remove trailing whitespaces
        ann_dict[k] = [' '.join(v.split()) for v in ann_dict[k]]
        # remove duplicates
        ann_dict[k] = list(set(ann_dict[k]))

        return ann_dict
