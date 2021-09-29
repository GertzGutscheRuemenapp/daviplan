from django.db import models
from django.contrib.gis.db import models as gis_models


class SymbolForm(models.Model):
    '''
    Map Symbol Forms
    '''
    name = models.TextField()


class MapSymbol(models.Model):
    '''
    MapSymbols
    '''
    symbol = models.ForeignKey(SymbolForm, on_delete=models.RESTRICT)
    fill_color = models.CharField(max_length=9)
    stroke_color = models.CharField(max_length=9)


class LayerGroup(models.Model):
    """a Layer Group"""
    name = models.TextField()
    order = models.IntegerField(unique=True)


class Layer(models.Model):
    """a generic layer"""
    name = models.TextField()
    group = models.ForeignKey(LayerGroup, on_delete=models.RESTRICT)
    layer_name = models.TextField()
    order = models.IntegerField(unique=True)

    class Meta:
        abstract = True


class WMSLayer(Layer):
    """a WMS Layer"""
    url = models.URLField()


class InternalWFSLayer(Layer):
    """an internal WFS Layer"""
    symbol = models.ForeignKey(MapSymbol, on_delete=models.RESTRICT)


class SourceTypes(models.TextChoices):
    """SourceTypes"""
    WFS = 'WFS', 'WFS Source'
    FILE = 'FILE', 'File Source'

class Source(models.Model):
    """a generic source"""
    source_type = models.CharField(max_length=4, choices=SourceTypes.choices)
    date = models.DateField()
    id_field = models.TextField()
    url = models.URLField(null=True, blank=True)
    layer = models.TextField(null=True, blank=True)


class AreaLevel(models.Model):
    """an area level"""
    name = models.TextField()
    order = models.IntegerField(unique=True)
    source = models.ForeignKey(Source, on_delete=models.RESTRICT)
    layer = models.ForeignKey(InternalWFSLayer, on_delete=models.RESTRICT)


class Area(models.Model):
    """an area"""
    area_level = models.ForeignKey(AreaLevel, on_delete=models.RESTRICT)
    geom = gis_models.GeometryField()
    attributes = models.JSONField()
