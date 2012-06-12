
import os, sys
import string


def configuration(parent_package='',top_path=None):
    from numpy.distutils.misc_util import Configuration
    config = Configuration(None,parent_package,top_path)

    config.add_subpackage('utils')
    config.add_subpackage('server')
    config.add_subpackage('converters')

    config.add_data_dir(('workbook/static', 'workbook/server/static'))
    config.add_data_dir(('workbook/templates', 'workbook/server/templates'))
    return config

if __name__ == '__main__':

    from numpy.distutils.core import setup
    c = configuration(top_path='',
                      ).todict()
    setup(**c)
