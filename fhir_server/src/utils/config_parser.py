import os
import yaml
import re
import inspect


def get_local_file(filename):
    """
    return path to file relative to call function

    :param filename: file to locate
    :return: abs path to file
    """
    context_string = "get_local_file("
    for st in inspect.stack():
        if any(context_string in cs for cs in st.code_context):
            current_dir = os.path.dirname(os.path.abspath(st.filename))  # script directory
            return os.path.join(current_dir, filename)
    return filename


def parse_env_config(path=None, data=None, tag='!ENV'):
    """
    Load a yaml configuration file and resolve any environment variables
    The environment variables must have !ENV before them and be in this format
    to be parsed: ${VAR_NAME}.
    E.g.:

    database:
        host: !ENV ${HOST}
        port: !ENV ${PORT}
    app:
        log_path: !ENV '/var/${LOG_PATH}'
        something_else: !ENV '${AWESOME_ENV_VAR}/var/${A_SECOND_AWESOME_VAR}'

    :param str path: the path to the yaml file
    :param str data: the yaml data itself as a stream
    :param str tag: the tag to look for
    :return: the dict configuration
    :rtype: dict[str, T]
    """
    # pattern for global vars: look for ${word}
    pattern = re.compile('.*?\${(\w+)}.*?')
    loader = yaml.SafeLoader

    # the tag will be used to mark where to start searching for the pattern
    # e.g. somekey: !ENV somestring${MYENVVAR}blah blah blah
    loader.add_implicit_resolver(tag, pattern, None)

    def constructor_env_variables(loader, node):
        """
        Extracts the environment variable from the node's value

        :param yaml.Loader loader: the yaml loader
        :param node: the current node in the yaml
        :return: the parsed string that contains the value of the environment variable
        """
        value = loader.construct_scalar(node)
        match = pattern.findall(value)  # to find all env variables in line
        if match:
            full_value = value
            for g in match:
                env_value = os.environ.get(g)
                if env_value:
                    full_value = full_value.replace(f'${{{g}}}', env_value)
                else:
                    full_value = None
            return full_value
        return value

    loader.add_constructor(tag, constructor_env_variables)

    if path:
        with open(path) as conf_data:
            return yaml.load(conf_data, Loader=loader)
    elif data:
        return yaml.load(data, Loader=loader)
    else:
        raise ValueError('Either a path or data should be defined as input')


def parse_full_config(base_config_path, env_config_path, tag='!ENV', logger=None, stop_on_error=False, silent=False):
    """
    Tries to load both config files and merge them (env_config values overloading base_config)
    if any of the 2 is None, returns the other one

    Both can use environment value if needed

    :param base_config_path: path to base config
    :param env_config_path: path to configurable config
    :param tag: tag to detect to find env variables
    :return: dict
    :raise: ValueError
    """
    errors = {}
    try:
        env_conf = parse_env_config(env_config_path, tag=tag)
    except ValueError as e:
        env_conf = None
        errors['env_config'] = e

    try:
        base_conf = parse_env_config(base_config_path, tag=tag)
    except ValueError as e:
        base_conf = None
        errors['base_config'] = e

    if len(errors):
        if not silent:
            if logger:
                logger.error(errors)
            else:
                print(errors)
        if stop_on_error:
            raise ValueError('Errors loading files: {}'.format(errors))

    if env_conf is None and base_conf is None:
        raise ValueError('Either a path or data should be defined as input')

    if env_conf is None:
        return base_conf

    if base_conf is None:
        return env_conf

    def rec_complete(dict1, dict2):
        for k1 in dict1:
            if k1 in dict2 and isinstance(dict1[k1], dict) and isinstance(dict2[k1], dict):
                dict1[k1] = rec_complete(dict1[k1], dict2[k1])
            else:
                if not dict1[k1]:
                    dict1[k1] = dict2[k1]

        for k2 in dict2:
            if k2 not in dict1:
                dict1[k2] = dict2[k2]

        return dict1

    return rec_complete(env_conf, base_conf)
