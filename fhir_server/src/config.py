from utils.config_parser import get_local_file, parse_full_config


class Config:
    """
    Loads the config and the eventual environment variables surcharging it

    Format is correct to feed to flask app
    """
    config = parse_full_config(get_local_file('config.yaml'), get_local_file('config_env.yaml'))

    # General Config
    # SECRET_KEY = environ.get('SECRET_KEY')
    # FLASK_APP = environ.get('FLASK_APP')
    # FLASK_ENV = environ.get('FLASK_ENV')

    # Database
    SQLALCHEMY_DATABASE_URI = 'postgresql://' + config['postgres_db']['user'] + ':' + config['postgres_db']['pwd'] \
                              + '@' + config['postgres_db']['host'] + '/' + config['postgres_db']['db_name']
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False