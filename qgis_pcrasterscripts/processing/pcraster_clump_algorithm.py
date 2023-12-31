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

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsDataSourceUri,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterRasterLayer)
from qgis import processing
from pcraster import *


class PCRasterClumpAlgorithm(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT_RASTER = 'INPUT'
    INPUT_DIRECTIONS = 'INPUT1'
    OUTPUT_CLUMP = 'OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return PCRasterClumpAlgorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'clump'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('clump')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('PCRaster')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'pcraster'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it.
        """
        return self.tr(
        """Contiguous groups of cells with the same value (‘clumps’)
            
            <a href="https://pcraster.geo.uu.nl/pcraster/4.3.1/documentation/pcraster_manual/sphinx/op_clump.html">PCRaster documentation</a>
            
            Parameters:
            
             * <b>Input raster layer</b> (required) - Boolean, nominal or ordinal raster layer
             * <b>Input directions</b> (required) - diagonal (D8) or non-diagonal (D4)
             * <b>Output clump raster layer</b> (required) - nominal raster layer with clumps
        """
    )

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT_RASTER,
                self.tr('Input raster layer')
            )
        )

        self.directionoption = [self.tr('Diagonal (8 cell)'),self.tr('Non-diagonal (4 cell)')]
        self.addParameter(
            QgsProcessingParameterEnum(
                self.INPUT_DIRECTIONS,
                self.tr('Clump direction'),
                self.directionoption,
                defaultValue=0
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT_CLUMP,
                self.tr('Clump layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        input_raster = self.parameterAsRasterLayer(parameters, self.INPUT_RASTER, context)
        direction_options = self.parameterAsEnum(parameters, self.INPUT_DIRECTIONS, context)
        if direction_options == 0:
            setglobaloption("diagonal")
        else:
            setglobaloption("nondiagonal")
        output_clump = self.parameterAsRasterLayer(parameters, self.OUTPUT_CLUMP, context)
        setclone(input_raster.dataProvider().dataSourceUri())
        ClassLayer = readmap(input_raster.dataProvider().dataSourceUri())
        ClumpResult = clump(ClassLayer)
        outputFilePath = self.parameterAsOutputLayer(parameters, self.OUTPUT_CLUMP, context)

        report(ClumpResult,outputFilePath)

        results = {}
        results[self.OUTPUT_CLUMP] = outputFilePath
        
        return results
