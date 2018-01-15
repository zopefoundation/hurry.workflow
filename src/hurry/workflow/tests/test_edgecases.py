import unittest
from hurry.workflow import interfaces, workflow

from zope import component
from zope.annotation.interfaces import IAttributeAnnotatable
from zope.annotation import attribute
from zope.annotation import interfaces as annotation_interfaces

from zope.interface import implements, Attribute

from hurry.workflow.tests.test_doctest import WorkflowVersions

"""Increase test coverage without polluting doctest."""


class IDocument(IAttributeAnnotatable):
    title = Attribute('Title')


class Document(object):
    implements(IDocument)

    def __init__(self, title):
        self.title = title


class WorkflowTestCase(unittest.TestCase):

    def test_getTransitions_empty(self):
        wf = workflow.Workflow([])
        self.assertEquals([], wf.getTransitions(None))


class WorkflowInfoTestCase(unittest.TestCase):

    def setUp(self):
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

        # self.events = []

        # def transition_handler(event):
        #     self.events.append(event)

        # component.provideHandler(
        #     transition_handler,
        #     [interfaces.IWorkflowTransitionEvent])

        def some_condition(wf, context):
            return True

        def some_action(wf, context):
            return context

        def no_result_action(wf, context):
            return None

        self.to_a = workflow.Transition(
            transition_id='to_a',
            title='None to a',
            source=None,
            destination='a',
            condition=some_condition,
            action=some_action,
            trigger=interfaces.MANUAL)

        self.a_to_b = workflow.Transition(
            transition_id='a_to_b',
            title='A to B',
            source='a',
            destination='b',
            condition=some_condition,
            action=no_result_action,
            trigger=interfaces.MANUAL)

        self.wf = workflow.Workflow([self.to_a, self.a_to_b])
        component.provideUtility(
            self.wf, interfaces.IWorkflow)

        self.document = Document('Foo')
        self.info = interfaces.IWorkflowInfo(self.document)
        self.state = interfaces.IWorkflowState(self.document)

    def test_info(self):
        self.assertEquals(self.info.context,
                          self.info.info(self.document).context)
        self.assertEquals(self.info.wf,
                          self.info.info(self.document).wf)

    def test_state(self):
        self.assertEquals(
            self.state.context,
            self.info.state(self.document).context)
        self.assertEquals(
            self.state._annotations.items(),
            self.info.state(self.document)._annotations.items())

    def test_fireTransition_result_wo__source(self):
        self.assertEquals(None, self.state.getId())
        self.info.fireTransition('to_a')
        self.assertNotEquals(None, self.state.getId())

    def test_fireTransition_wo_result_w_side_effect(self):
        def set_foo(context):
            context.foo = 'foo'

        self.info.fireTransition('to_a')
        self.assertFalse(hasattr(self.document, 'foo'))
        self.info.fireTransition('a_to_b', side_effect=set_foo)
        self.assertEquals('foo', self.document.foo)

    def test_fireTransitionForVersions_version_is_context(self):
        self.info.fireTransition('to_a')
        wf_versions = component.getUtility(interfaces.IWorkflowVersions)
        wf_versions.addVersion(self.document)
        self.info.fireTransitionForVersions(self.state.getState(),
                                            'a_to_b')
        # the implementation specifically does not transition the document
        self.assertEquals('a', self.state.getState())


class WorkflowVersionsTestCase(unittest.TestCase):

    def setUp(self):
        self.versions = workflow.WorkflowVersions()

    def test_getVersions(self):
        with self.assertRaises(NotImplementedError):
            self.versions.getVersions('foo', 'bar')

    def test_getVersionsWithAutomaticTransitions(self):
        with self.assertRaises(NotImplementedError):
            self.versions.getVersionsWithAutomaticTransitions()

    def test_hasVersion(self):
        with self.assertRaises(NotImplementedError):
            self.versions.hasVersion('foo', 'bar')

    def test_hasVersionId(self):
        with self.assertRaises(NotImplementedError):
            self.versions.hasVersionId('bar')
