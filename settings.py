import os
from dynaconf import Dynaconf

os.environ['ENV_FOR_DYNACONF'] = 'quick_start'

settings = Dynaconf(
    environments=True,
    settings_files=['settings.toml', '.secrets.toml']
)