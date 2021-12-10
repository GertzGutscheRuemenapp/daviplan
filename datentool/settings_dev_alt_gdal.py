from datentool.settings_dev import *

# GDAL
if os.name == 'nt':
    # alternate install via conda
    os.environ['GDAL_DATA'] = os.path.join(sys.prefix, 'Library',
                                           'share', 'gdal')
    os.environ['PROJ_LIB'] = os.path.join(sys.prefix, 'Library',
                                          'share', 'proj')
    os.environ['PATH'] = ';'.join([os.environ['PATH'],
                                   os.path.join(sys.prefix, 'Library', 'bin')])