"""
Model exported as python.
Name : Dangles 3.0
Group : Topology
With QGIS : 30116
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterBoolean
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsExpression
import processing


class Dangles30(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('Selectlayerfordanglecheck', 'Select line for dangle check', types=[QgsProcessing.TypeVectorLine], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('Selectareamask', 'Select polygon mask', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('Tolerance', 'Tolerance', type=QgsProcessingParameterNumber.Double, minValue=0.01, maxValue=100, defaultValue=0.01))
        self.addParameter(QgsProcessingParameterBoolean('VERBOSE_LOG', 'Verbose logging', optional=True, defaultValue=False))
        self.addParameter(QgsProcessingParameterFeatureSink('Overundershootpoints', 'OverUnderShootPoints', type=QgsProcessing.TypeVectorPoint, createByDefault=True, supportsAppend=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(15, model_feedback)
        results = {}
        outputs = {}

        # Polygons to lines
        alg_params = {
            'INPUT': parameters['Selectareamask'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['PolygonsToLines'] = processing.run('native:polygonstolines', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Refactor fields
        alg_params = {
            'FIELDS_MAPPING': [{'expression': ' @row_number','length': 11,'name': 'FID','precision': 0,'type': 4}],
            'INPUT': parameters['Selectlayerfordanglecheck'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RefactorFields'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Create spatial index
        alg_params = {
            'INPUT': outputs['RefactorFields']['OUTPUT']
        }
        outputs['CreateSpatialIndex'] = processing.run('native:createspatialindex', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Buffer
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': 1,
            'END_CAP_STYLE': 0,
            'INPUT': outputs['PolygonsToLines']['OUTPUT'],
            'JOIN_STYLE': 0,
            'MITER_LIMIT': 2,
            'SEGMENTS': 5,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Buffer'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # clip - line with polygon
        alg_params = {
            'INPUT': outputs['CreateSpatialIndex']['OUTPUT'],
            'OVERLAY': parameters['Selectareamask'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ClipLineWithPolygon'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Extract specific vertices - end points
        alg_params = {
            'INPUT': outputs['ClipLineWithPolygon']['OUTPUT'],
            'VERTICES': '0,-1',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtractSpecificVerticesEndPoints'] = processing.run('native:extractspecificvertices', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Line intersections - intersection points
        alg_params = {
            'INPUT': outputs['ClipLineWithPolygon']['OUTPUT'],
            'INPUT_FIELDS': [''],
            'INTERSECT': outputs['ClipLineWithPolygon']['OUTPUT'],
            'INTERSECT_FIELDS': [''],
            'INTERSECT_FIELDS_PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['LineIntersectionsIntersectionPoints'] = processing.run('native:lineintersections', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # SpatialIndex
        alg_params = {
            'INPUT': outputs['ClipLineWithPolygon']['OUTPUT']
        }
        outputs['Spatialindex'] = processing.run('native:createspatialindex', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Dangels by difference
        alg_params = {
            'INPUT': outputs['ExtractSpecificVerticesEndPoints']['OUTPUT'],
            'OVERLAY': outputs['LineIntersectionsIntersectionPoints']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DangelsByDifference'] = processing.run('native:difference', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Difference- remove dangels from border
        alg_params = {
            'INPUT': outputs['DangelsByDifference']['OUTPUT'],
            'OVERLAY': outputs['Buffer']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DifferenceRemoveDangelsFromBorder'] = processing.run('native:difference', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # Refactor fields dangle
        alg_params = {
            'FIELDS_MAPPING': [{'expression': ' @row_number','length': 11,'name': 'buffer_id','precision': 0,'type': 2}],
            'INPUT': outputs['DifferenceRemoveDangelsFromBorder']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RefactorFieldsDangle'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # Buffer dangle
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': parameters['Tolerance'],
            'END_CAP_STYLE': 0,
            'INPUT': outputs['RefactorFieldsDangle']['OUTPUT'],
            'JOIN_STYLE': 0,
            'MITER_LIMIT': 2,
            'SEGMENTS': 5,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['BufferDangle'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}

        # Line count
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'INPUT': outputs['BufferDangle']['OUTPUT'],
            'JOIN': outputs['Spatialindex']['OUTPUT'],
            'JOIN_FIELDS': QgsExpression('').evaluate(),
            'PREDICATE': [0],
            'SUMMARIES': [0],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['LineCount'] = processing.run('qgis:joinbylocationsummary', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(13)
        if feedback.isCanceled():
            return {}

        # Extract by attribute
        alg_params = {
            'FIELD': 'FID_count',
            'INPUT': outputs['LineCount']['OUTPUT'],
            'OPERATOR': 2,
            'VALUE': '1',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtractByAttribute'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(14)
        if feedback.isCanceled():
            return {}

        # Centroids
        alg_params = {
            'ALL_PARTS': True,
            'INPUT': outputs['ExtractByAttribute']['OUTPUT'],
            'OUTPUT': parameters['Overundershootpoints']
        }
        outputs['Centroids'] = processing.run('native:centroids', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Overundershootpoints'] = outputs['Centroids']['OUTPUT']
        return results

    def name(self):
        return 'Dangles 3.0'

    def displayName(self):
        return 'Dangles 3.0'

    def group(self):
        return 'Topology'

    def groupId(self):
        return 'Topology'

    def createInstance(self):
        return Dangles30()
