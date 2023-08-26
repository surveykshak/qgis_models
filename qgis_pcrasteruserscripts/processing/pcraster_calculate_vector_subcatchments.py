# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

import gc
import os
from osgeo import gdal, ogr
from pcraster import (
    readmap,
    streamorder,
    ifthen,
    downstream,
    boolean,
    ordinal,
    cover,
    mapmaximum,
    uniqueid,
    cellvalue,
    catchment,
    ifthenelse,
    report,
    nominal
)
from qgis import processing
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterFolderDestination,
    QgsProcessingParameterNumber,
    QgsProcessingParameterCrs,
    QgsProcessingUtils,
    QgsProcessingParameterFeatureSink,
    QgsProcessing,
    QgsFields,
    QgsField,
    QgsWkbTypes,
    QgsProcessingException,
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsMultiPolygon,
    QgsPolygon,
    QgsCoordinateTransform,
    QgsProcessingParameterCrs
)
from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterFolderDestination,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterFeatureSink,
    QgsProcessing
)


class CalculateVectorSubcatchments(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    THRESHOLD = 'THRESHOLD'

    OUTPUT_RIVERS = 'OUTPUT_RIVERS'
    OUTPUT_JUNCTIONS = 'OUTPUT_JUNCTIONS'
    OUTPUT_OUTLETS = 'OUTPUT_OUTLETS'
    DEST_CRS = 'DEST_CRS'

    OUTPUT = 'OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)
        
   # def flags(self):
   #     return QgsProcessingAlgorithm.FlagNoThreading

    def createInstance(self):
        return CalculateVectorSubcatchments()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'vectorsubcatchments'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Calculate subcatchments from stream order (vector)')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('PCRaster User Scripts')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return self.tr('pcrasteruser')

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr(
            """<html><body><p>Calculate Subcatchments From Stream Order (Vector)</p>

            <h2>Parameters</h2>

            <b>Flow direction</b> (required) - PCRaster local drain direction (LDD) map
            <b>Minimum stream order threshold</b> (required) - Minimum Strahler order to determine rivers
            <b>Destination CRS</b> (required) - Projection of the result layer
            <b>Output rivers</b> (optional) - Output river raster layer (boolean)
            <b>Output junctions</b> (optional) - Output junctions raster layer (boolean)
            <b>Subcatchments</b> (optional) - Vector layer with all subcatchments

            Authors: Nyall Dawson, Hans van der Kwast
            </body></html>
            """
        )

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT,
                self.tr('Flow direction')
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.THRESHOLD,
                'Minimum stream order threshold',
                defaultValue=5,
                minValue=1,
            )
        )

        self.addParameter(
            QgsProcessingParameterCrs(self.DEST_CRS,
                                      self.tr('Destination CRS'),
                                      defaultValue='EPSG:28355')
        )

        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT_RIVERS,
                self.tr('Output rivers')
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT_JUNCTIONS,
                self.tr('Output junctions')
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT_OUTLETS,
                self.tr('Output outlets')
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Subcatchments'),
                QgsProcessing.TypeVectorPolygon
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        input_flow_direction = self.parameterAsRasterLayer(parameters, self.INPUT, context)

        if feedback and feedback.isCanceled():
            return {}
        flow_direction = readmap(input_flow_direction.dataProvider().dataSourceUri())
        if feedback and feedback.isCanceled():
            return {}

        threshold = self.parameterAsInt(parameters, self.THRESHOLD, context)

        feedback.pushInfo('Calculating Strahler orders')
        StrahlerOrders = streamorder(flow_direction)
        if feedback and feedback.isCanceled():
            return {}

        StrahlerRivers = ifthen(StrahlerOrders >= threshold, StrahlerOrders)
        if feedback and feedback.isCanceled():
            return {}

        output_rivers = self.parameterAsOutputLayer(parameters, self.OUTPUT_RIVERS, context)
        if output_rivers:
            report(StrahlerRivers, output_rivers)

        feedback.pushInfo('Finding outlets')
        Junctions = ifthen(downstream(flow_direction, StrahlerRivers) != StrahlerRivers, boolean(1))
        if feedback and feedback.isCanceled():
            return {}

        output_junctions = self.parameterAsOutputLayer(parameters, self.OUTPUT_JUNCTIONS, context)
        if output_junctions:
            report(Junctions, output_junctions)

        outlets = ordinal(cover(uniqueid(Junctions), 0))
        if feedback and feedback.isCanceled():
            return {}

        output_outlets = self.parameterAsOutputLayer(parameters, self.OUTPUT_OUTLETS, context)
        if output_outlets:
            report(outlets, output_outlets)

        feedback.pushInfo('Calculate subcatchments')

        MaximumOutlets = mapmaximum(outlets)
        MaximumOutletsTuple = cellvalue(MaximumOutlets, 0, 0)
        MaximumOutletsValue = MaximumOutletsTuple[0]
        feedback.pushInfo('Total subcatchments: {}'.format(MaximumOutletsValue))

        fields = QgsFields()
        fields.append(QgsField('catchment_id', QVariant.LongLong))

        dest_crs = self.parameterAsCrs(parameters, self.DEST_CRS, context)

        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                                               fields, QgsWkbTypes.MultiPolygon, dest_crs)
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        transform = QgsCoordinateTransform(input_flow_direction.crs(), dest_crs, context.transformContext())

        temp_catchment_raster_path = QgsProcessingUtils.generateTempFilename('catchment_raster.map')
        temp_catchment_vector_path = QgsProcessingUtils.generateTempFilename('catchment_vector.shp')

        for idx, outlet in enumerate(range(1, MaximumOutletsValue + 1)):
            feedback.setProgress(idx / MaximumOutletsValue * 100)
            if feedback and feedback.isCanceled():
                break

            gc.collect()
            feedback.pushInfo('Processing subcatchment {}'.format(outlet))
            SubCatchment = catchment(flow_direction, ifthenelse(outlets == outlet, nominal(outlet), nominal(0)))
            if os.path.exists(temp_catchment_raster_path):
                os.unlink(temp_catchment_raster_path)

            report(SubCatchment, temp_catchment_raster_path)
            del SubCatchment
            gc.collect()

            ds_raster = gdal.Open(temp_catchment_raster_path, gdal.GA_ReadOnly)
            src_band = ds_raster.GetRasterBand(1)
            # polygonize the result
            dst_layername = "polygonized"
            if os.path.exists(temp_catchment_vector_path):
                os.unlink(temp_catchment_vector_path)

            drv = ogr.GetDriverByName("ESRI Shapefile")
            catchment_vector_path = temp_catchment_vector_path  # 'c:/temp/catchments/catchment_' + str(outlet) + '.shp'
            dst_ds = drv.CreateDataSource(catchment_vector_path)
            dst_layer = dst_ds.CreateLayer(dst_layername, srs=None)
            field_dn = ogr.FieldDefn("DN", ogr.OFTInteger)
            dst_layer.CreateField(field_dn)

            gdal.Polygonize(src_band, None, dst_layer, 0, [], callback=None)
            del src_band
            del ds_raster
            del dst_layer
            del dst_ds
            gc.collect()

            polygons_layer = QgsVectorLayer(catchment_vector_path)
            parts = []
            for f in polygons_layer.getFeatures():
                if f['DN'] <= 0:
                    continue
                part_geometry = f.geometry().makeValid()
                for part in part_geometry.parts():
                    parts.append(QgsGeometry(part.clone()))
            del polygons_layer
            gc.collect()

            unioned_parts = QgsGeometry.unaryUnion(parts).makeValid()
            mp = QgsMultiPolygon()
            for part in unioned_parts.parts():
                if isinstance(part, QgsPolygon):
                    mp.addGeometry(part.clone())
                elif isinstance(part, QgsMultiPolygon):
                    raise QgsProcessingException('unexpected part type')

            geom = QgsGeometry(mp)
            geom.transform(transform)
            out_feature = QgsFeature(fields)
            out_feature[0] = outlet
            out_feature.setGeometry(geom)
            sink.addFeature(out_feature)

        return {
            self.OUTPUT_RIVERS: output_rivers,
            self.OUTPUT_JUNCTIONS: output_junctions,
            self.OUTPUT_OUTLETS: output_outlets,
            self.OUTPUT: dest_id
        }
