from unidecode import unidecode
import string


def preprocess(obs):
    """
    A function that pre-processes the observations :

    - deletes observations with NaN values,
    - deletes observations that contain numbers only,
    - deletes observations with 1 or 2 words
    - deletes line breaks from each remaining observation
    - converts observations to lowercase
    - deletes punctuation
    - deletes trailing whitespaces

    :param obs: (list) the 'OBSERVATION_BLOB' column from the data frame
    :return: (list) the pre-processed observations
    """

    # delete observations with nan values
    obs = [o for o in obs if str(o) != 'nan']

    # delete observations that contain only numbers
    obs = [o for o in obs if not o.isnumeric()]

    # delete observations that have one or two words
    obs = [o for o in obs if len(o.split()) > 2]

    # remove line breaks
    obs = [o.replace("\r", '').replace('\n', ' ') for o in obs]

    # lowercase
    obs = [o.lower() for o in obs]

    # unidecode
    obs = [unidecode(o) for o in obs]

    # remove punctuation
    obs = [o.translate(str.maketrans('', '', string.punctuation)) for o in obs]

    # remove trailing whitespaces
    obs = [' '.join(o.split()) for o in obs]

    return obs
