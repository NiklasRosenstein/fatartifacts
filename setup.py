
from setuptools import setup

setup(
  name = 'fatartifacts',
  version = '1.0.0-dev',
  description = 'General-purpose artifact repository.',
  entry_points = {
    'console_scripts': [
      'fatartifacts-rest-cli=fatartifacts.web.cli:main_and_exit'
    ]
  }
)
