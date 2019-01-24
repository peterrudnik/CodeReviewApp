import os
import yaml

_env_config = 'CODEREVIEW_APP_CONFIG'

if _env_config in os.environ:
    config_file = os.environ.get(_env_config)
else:
    raise ValueError("Environment variable not found: {e}\nPlease specify this variable pointing to a config file in YAML format.".format(e=_env_config))
if os.path.isfile(config_file) == False:
    raise ValueError(
        "Cound not find config file {f} speified by environment variable {e}\nPlease specify this variable pointing to a config file in YAML format.".format(
            f= config_file, e=_env_config))


class Config(object):
    def __init__(self,config_file):
        self._read_config_yaml(config_file)

    def _read_config_yaml(self,f):
        with open(f, 'r') as stream:
            try:
                self.config_yaml = yaml.load(stream)
                #print(config_yaml)
                self.config_syntax_check(f)
            except yaml.YAMLError as exc:
                print(exc)
                raise

    def config_syntax_check(self,config_yaml):
        credentials = "{u}:{p}".format(u=self.config_yaml["mysql"]["username"], p=self.config_yaml["mysql"]["password"])
        return True

    def get_svn_url(self):
        return self.config_yaml.svn["url"]

    def get_mysql_credentials(self):
        credentials = "{u}:{p}".format(u=self.config_yaml["mysql"]["username"], p=self.config_yaml["mysql"]["password"])
        return credentials

    def get_mysql_db(self):
        credentials = "{h}/{db}".format(h=self.config_yaml["mysql"]["host"], db=self.config_yaml["mysql"]["db"])
        return credentials

    def get_file_svn_xml(self):
        return self.config_yaml["import"]["svn_xml"]

    def get_file_csv(self):
        return self.config_yaml["import"]["csv"]

    def get_sqlite_db(self):
        return self.config_yaml["sqllite"]["db"]


config = Config(config_file)

# definitions with capital letters are used by     app.config.from_object(config_module)
#class Config(object):
SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
#SQLALCHEMY_DATABASE_URI = r'sqlite:///' + config.get_sqlite_db()
#SQLALCHEMY_DATABASE_URI = r'mysql+pymysql://{c}@localhost/codereview'.format(c=config.get_mysql_credentials(),db=config.get_mysql_db())
SQLALCHEMY_DATABASE_URI = r'mysql+pymysql://{c}@{db}'.format(c=config.get_mysql_credentials(),db=config.get_mysql_db())


