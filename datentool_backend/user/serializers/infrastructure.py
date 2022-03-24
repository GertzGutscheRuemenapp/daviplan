import os
import pandas as pd

from django.conf import settings
from rest_framework import serializers

from openpyxl.worksheet.dimensions import ColumnDimension
from openpyxl.worksheet.datavalidation import DataValidation

from datentool_backend.user.models import (Infrastructure,
                                           InfrastructureAccess,
                                           )

from datentool_backend.area.models import MapSymbol
from datentool_backend.area.serializers import MapSymbolSerializer
from datentool_backend.infrastructure.serializers import PlaceFieldInfraSerializer


class InfrastructureAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = InfrastructureAccess
        fields = ('infrastructure', 'profile', 'allow_sensitive_data')
        read_only_fields = ('id', 'infrastructure', )


class InfrastructureSerializer(serializers.ModelSerializer):
    symbol = MapSymbolSerializer(allow_null=True, required=False)
    accessible_by = InfrastructureAccessSerializer(
        many=True, source='infrastructureaccess_set', required=False)
    place_fields = PlaceFieldInfraSerializer(many=True, source='placefield_set',
                                             required=False, read_only=True)

    class Meta:
        model = Infrastructure
        fields = ('id', 'name', 'description',
                  'editable_by', 'accessible_by',
                  'order', 'symbol', 'place_fields')

    def create(self, validated_data):
        symbol_data = validated_data.pop('symbol', None)
        symbol = MapSymbol.objects.create(**symbol_data) \
            if symbol_data else None

        editable_by = validated_data.pop('editable_by', [])
        accessible_by = validated_data.pop('infrastructureaccess_set', [])
        instance = Infrastructure.objects.create(
            symbol=symbol, **validated_data)
        instance.editable_by.set(editable_by)
        instance.accessible_by.set([a['profile'] for a in accessible_by])
        for profile_access in accessible_by:
            infrastructure_access = InfrastructureAccess.objects.get(
                infrastructure=instance,
                profile=profile_access['profile'])
            infrastructure_access.allow_sensitive_data = profile_access['allow_sensitive_data']
            infrastructure_access.save()

        return instance

    def update(self, instance, validated_data):
        # symbol is nullable
        update_symbol = 'symbol' in validated_data
        symbol_data = validated_data.pop('symbol', None)

        editable_by = validated_data.pop('editable_by', None)
        accessible_by = validated_data.pop('infrastructureaccess_set', None)
        instance = super().update(instance, validated_data)
        if editable_by is not None:
            instance.editable_by.set(editable_by)
        if accessible_by is not None:
            instance.accessible_by.set([a['profile'] for a in accessible_by])
            for profile_access in accessible_by:
                infrastructure_access = InfrastructureAccess.objects.get(
                    infrastructure=instance,
                    profile=profile_access['profile'])
                infrastructure_access.allow_sensitive_data = profile_access[
                    'allow_sensitive_data']
                infrastructure_access.save()

        if update_symbol:
            symbol = instance.symbol
            if symbol_data:
                if not symbol:
                    symbol = MapSymbol.objects.create(**symbol_data)
                    instance.symbol = symbol
                else:
                    for k, v in symbol_data.items():
                        setattr(symbol, k, v)
                    symbol.save()
            # symbol passed but is None -> intention to set it to null
            else:
                symbol.delete()
                instance.symbol = None

        instance.save()
        return instance


class InfrastructureTemplateSerializer(serializers.Serializer):
    """Serializer for uploading InfrastructureTemplate"""
    excel_file = serializers.FileField()
    drop_constraints = serializers.BooleanField(default=True)

    def create_template(self, pk: int) -> bytes:
        """Create a template file for infrastructure with the given pk"""
        excel_filename = 'Standorte_und_Kapazitäten.xlsx'
        columns = {'Name': 'So werden die Einrichtungen auf den Karten beschriftet. '\
                   'Jeder Standort muss einen Namen haben, den kein anderer Standort trägt.',
                  'Straße': 'Postalisch korrekte Schreibweise',
                  'Hausnummer': 'Zahl, ggf. mit Buchstaben (7b) oder 11-15',
                  'PLZ': 'fünfstellig',
                  'Ort': 'Postalisch korrekte Schreibweise',
                  'Lon': 'Längengrad, in WGS84',
                  'Lat': 'Breitengrad, in WGS84',}

        df = pd.DataFrame(columns=pd.Index(columns.items()))
        fn = os.path.join(settings.MEDIA_ROOT, excel_filename)
        sheetname = 'Standorte und Kapazitäten'
        with pd.ExcelWriter(fn, engine='openpyxl') as writer:
            df_meta = pd.DataFrame({'value': [pk]},
                                   index=pd.Index(['infrastructure'], name='key'))
            df_meta.to_excel(writer, sheet_name='meta')
            df.to_excel(writer, sheet_name=sheetname, freeze_panes=(2, 2))
            ws: Worksheet = writer.sheets.get(sheetname)

            dv = DataValidation(type="decimal",
                                operator="between",
                                formula1=0,
                                formula2=90,
                                allow_blank=True)

            dv.error ='Koordinaten müssen in WGS84 angegeben werden und zwischen 0 und 90 liegen'
            dv.errorTitle = 'Ungültige Koordinaten'
            ws.add_data_validation(dv)
            dv.add('G3:H999999')

            ws.column_dimensions['A'] = ColumnDimension(ws, index='A', hidden=True)
            for col in 'BCDEFGH':
                ws.column_dimensions[col] = ColumnDimension(ws, index=col, width=20)

        content = open(fn, 'rb').read()
        return content

    def read_excel_file(self, request) -> pd.DataFrame:
        """read excelfile and return a dataframe"""
        excel_file = request.FILES['excel_file']

        df_meta = pd.read_excel(excel_file.file,
                           sheet_name='meta',
                           skiprows=[1])

        df = pd.read_excel(excel_file.file,
                           sheet_name='Standorte und Kapazitäten',
                           skiprows=[1])


        df.rename(columns={'from_stop': 'from_stop_id',
                           'to_stop': 'to_stop_id',}, inplace=True)

        variant = request.data.get('variant')
        df['variant_id'] = int(variant)
        return df
