
import os, sys
import string


def configuration(parent_package='',top_path=None):
    from numpy.distutils.misc_util import Configuration
    config = Configuration(None,parent_package,top_path)

    return config

if __name__ == '__main__':

    from numpy.distutils.core import setup
    c = configuration(top_path='',
                      ).todict()
    setup(**c)
