import unittest

from zope.testing import doctest
from zope import component
from zope.component import testing
from zope.annotation import interfaces as annotation_interfaces
from zope.annotation import attribute
from hurry.workflow import interfaces, workflow

class WorkflowVersions(workflow.WorkflowVersions):
    """Simplistic implementation that keeps track of versions.

    A real implementation would use something like the catalog.
    """
    def __init__(self):
        self.versions = []
        
    def addVersion(self, obj):
        self.versions.append(obj)
        
    def getVersions(self, state, id):
        result = []
        for version in self.versions:
            state_adapter = interfaces.IWorkflowState(version)
            if state_adapter.getId() == id and state_adapter.getState() == state:
                result.append(version)
        return result

    def getVersionsWithAutomaticTransitions(self):
        result = []
        for version in self.versions:
            if interfaces.IWorkflowInfo(version).hasAutomaticTransitions():
                result.append(version)
        return result
    
    def hasVersion(self, state, id):
        return bool(self.getVersions(state, id))

    def hasVersionId(self, id):
        for version in self.versions:
            state_adapter = interfaces.IWorkflowState(version)
            if state_adapter.getId() == id:
                return True
        return False
    
    def clear(self):
        self.versions = []
        
def workflowSetUp(doctest):
    testing.setUp(doctest)
    component.provideAdapter(
        workflow.WorkflowState,
        (annotation_interfaces.IAnnotatable,),
        interfaces.IWorkflowState)
    component.provideAdapter(
        workflow.WorkflowInfo,
        (annotation_interfaces.IAnnotatable,),
        interfaces.IWorkflowInfo)
    component.provideAdapter(
        attribute.AttributeAnnotations,
        (annotation_interfaces.IAttributeAnnotatable,),
        annotation_interfaces.IAnnotations)
    component.provideUtility(
        WorkflowVersions(),
        interfaces.IWorkflowVersions)
    
def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite(
            'workflow.txt',
            setUp=workflowSetUp, tearDown=testing.tearDown,
            ),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

