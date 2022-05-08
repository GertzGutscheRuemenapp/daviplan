import os
import shutil
import tempfile
import numpy as np
import pandas as pd

from io import StringIO
from distutils.util import strtobool

from osgeo import gdal, ogr, osr
from django.contrib.gis.geos import Point, Polygon
from django.db import transaction

from django.conf import settings

from drf_spectacular.utils import (extend_schema,
                                   inline_serializer,
                                   OpenApiResponse,)
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from datentool_backend.utils.views import ProtectCascadeMixin
from datentool_backend.utils.permissions import (
    HasAdminAccessOrReadOnly, CanEditBasedata)
from datentool_backend.population.models import (
    Raster,
    PopulationRaster,
    RasterCell,
    RasterCellPopulation,
    )
from rest_framework.response import Response

from datentool_backend.utils.serializers import (MessageSerializer,
                                                 drop_constraints,
                                                 )

from datentool_backend.population.serializers import (RasterSerializer,
                                                      PopulationRasterSerializer,
                          )
from datentool_backend.site.models import ProjectSetting


class RasterViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = Raster.objects.all()
    serializer_class = RasterSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]


class PopulationRasterViewSet(ProtectCascadeMixin, viewsets.ModelViewSet):
    queryset = PopulationRaster.objects.all()
    serializer_class = PopulationRasterSerializer
    permission_classes = [HasAdminAccessOrReadOnly | CanEditBasedata]

    @extend_schema(description='Intersect Project Area with Census Data',
                   request=inline_serializer(
                       name='IntersectCensusSerializser',
                       fields={'drop_constraints': drop_constraints,
                               }
                   ),
                   responses={
                       202: OpenApiResponse(MessageSerializer, 'success'),
                       406: OpenApiResponse(MessageSerializer, 'failed'),
                   },
                )
    @action(methods=['POST'], detail=True)
    def intersect_census(self, request, pk):
        try:
            popraster = PopulationRaster.objects.get(pk=pk)

            fp = os.path.join(settings.POPRASTER_ROOT, popraster.filename)
            fp_clip = os.path.join(settings.POPRASTER_ROOT, 'clipped.tif')
            raster = gdal.Open(fp)
            srs = raster.GetSpatialRef()
            epsg = srs.GetAttrValue('AUTHORITY',1)

            raster.RasterXSize
            raster.RasterYSize

            # Number of bands
            raster.RasterCount

            # Metadata for the raster dataset
            #raster.GetMetadata(fp, raster)

            projectsettings = ProjectSetting.objects.first()
            project_area = projectsettings.project_area
            project_area.transform(epsg)
            srid = project_area.srid

            gpkgfile = tempfile.mktemp(suffix='.gpkg')
            drv = ogr.GetDriverByName('GPKG')
            ds = drv.CreateDataSource(gpkgfile)
            srs = osr.SpatialReference()
            srs.ImportFromEPSG(srid)
            layer = ds.CreateLayer('region',
                                   srs,
                                   geom_type=ogr.wkbMultiPolygon)
            fldDef = ogr.FieldDefn('id', ogr.OFTInteger)
            layer.CreateField(fldDef)
            featureDefn = layer.GetLayerDefn()
            feature = ogr.Feature(featureDefn)
            geom = ogr.CreateGeometryFromWkb(project_area.wkb)
            feature.SetGeometry(geom)
            feature.SetField('id', 1)
            layer.CreateFeature(feature)
            ds.Destroy()

            ret = gdal.Warp(fp_clip,
                           fp,
                           format='GTiff',
                           cutlineDSName=gpkgfile,
                           cutlineLayer='region',
                           cropToCutline=True,
                           srcNodata=-(2 ** 31),
                           dstNodata=0,
                           )
            assert ret is not None, 'clip raster failed'
            os.remove(gpkgfile)

            r = gdal.Open(fp_clip)
            band = r.GetRasterBand(1)
            (upper_left_x,
             x_size,
             x_rotation,
             upper_left_y,
             y_rotation,
             y_size) = r.GetGeoTransform()

            a = band.ReadAsArray().astype(np.int)
            (y_index, x_index) = np.nonzero((a > 0))
            n_cells = len(x_index)

            # make corners of polygon
            corners = np.empty((2, 5, n_cells))
            corners[0] = x_index * x_size + x_rotation * y_index + upper_left_x
            corners[1] = y_index * y_size + y_rotation * x_index + upper_left_y
            corners[0, [1, 2]] += x_size
            corners[1, [2, 3]] += y_size

            #add half the cell size
            centroids = corners[:, 0] + np.array([[x_size / 2], [y_size /2]])

            target_srs = 3857
            rastercells = []
            rastercellpopulation = []

            popraster_id = popraster.pk
            raster_id = popraster.raster_id
            # Iterate over the Numpy points..

            for i in range(n_cells):
                cellcode = str(i)
                x, y = centroids[:, i]
                pnt = Point(x, y, srid=srid)
                poly = Polygon(corners[:, :, i].T, srid=srid)
                rastercells.append([raster_id,
                                    cellcode,
                                    pnt.transform(target_srs, clone=True),
                                    poly.transform(target_srs, clone=True),
                                    ])
                einwohner = int(a[y_index[i], x_index[i]])
                rastercellpopulation.append([popraster_id, einwohner])



            df_rastercells = pd.DataFrame(rastercells,
                                          columns=['raster_id', 'cellcode',
                                                   'pnt', 'poly'])

            df_rcpopulation = pd.DataFrame(rastercellpopulation,
                                           columns=['popraster_id', 'value'])

            rc_manager = RasterCell.copymanager
            rcp_manager = RasterCellPopulation.copymanager
            drop_constraints = bool(strtobool(
                request.data.get('drop_constraints', 'False')))

            with transaction.atomic():
                if drop_constraints:
                    rc_manager.drop_constraints()
                    rc_manager.drop_indexes()
                    rcp_manager.drop_constraints()
                    rcp_manager.drop_indexes()

                qs_rc = RasterCell.objects.filter(raster=raster_id)
                qs_rc.delete()

                try:
                    if len(df_rastercells):
                        with StringIO() as file:
                            df_rastercells.to_csv(file, index=False)
                            file.seek(0)
                            rc_manager.from_csv(
                                file,
                                drop_constraints=False, drop_indexes=False,
                            )

                    raster_ids = pd.Series(RasterCell.objects.filter(raster=raster_id)\
                                           .values_list('id', flat=True))

                    if len(df_rcpopulation):
                        df_rcpopulation['cell_id'] = raster_ids
                        with StringIO() as file:
                            df_rcpopulation.to_csv(file, index=False)
                            file.seek(0)
                            rcp_manager.from_csv(
                                file,
                                drop_constraints=False, drop_indexes=False,
                            )

                except Exception as e:
                    msg = str(e)
                    return Response({'message': msg,}, status=status.HTTP_406_NOT_ACCEPTABLE)

                finally:
                    # recreate indices
                    if drop_constraints:
                        rc_manager.restore_constraints()
                        rc_manager.restore_indexes()
                        rcp_manager.restore_constraints()
                        rcp_manager.restore_indexes()


        except Exception as e:
            msg = str(e)
            return Response({'message': msg,}, status=status.HTTP_406_NOT_ACCEPTABLE)
        n_inhabitants = df_rcpopulation['value'].sum()
        msg = f'intersected project areas with {n_cells} cells and {n_inhabitants} inhabitants'
        return Response({'message': msg,}, status=status.HTTP_202_ACCEPTED)
