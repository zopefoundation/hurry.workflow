import random, sys

from zope.interface import implements
from zope.event import notify
from zope.security.checker import CheckerPublic
from zope.security.interfaces import NoInteraction, Unauthorized
from zope.security.management import getInteraction
from zope import component

from zope.annotation.interfaces import IAnnotations
from zope.lifecycleevent import ObjectModifiedEvent
from zope.component.interfaces import ObjectEvent

from hurry.workflow import interfaces
from hurry.workflow.interfaces import MANUAL, AUTOMATIC, SYSTEM
from hurry.workflow.interfaces import\
     IWorkflow, IWorkflowState, IWorkflowInfo, IWorkflowVersions
from hurry.workflow.interfaces import\
     InvalidTransitionError, ConditionFailedError

def NullCondition(wf, context):
    return True

def NullAction(wf, context):
    pass

# XXX this is needed to make the tests pass in the absence of
# interactions..
def nullCheckPermission(permission, principal_id):
    return True

class Transition(object):

    def __init__(self, transition_id, title, source, destination,
                 condition=NullCondition,
                 action=NullAction,
                 trigger=MANUAL,
                 permission=CheckerPublic,
                 order=0,
                 **user_data):
        self.transition_id = transition_id
        self.title = title
        self.source = source
        self.destination = destination
        self.condition = condition
        self.action = action
        self.trigger = trigger
        self.permission = permission
        self.order = order
        self.user_data = user_data

    def __cmp__(self, other):
        return cmp(self.order, other.order)

# in the past this subclassed from zope.container.Contained and
# persistent.Persistent.
# to reduce dependencies these base classes have been removed.
# You can choose to create a subclass in your own code that
# mixes these in if you need persistent workflow
class Workflow(object):
    implements(IWorkflow)

    def __init__(self, transitions):
        self.refresh(transitions)

    def _register(self, transition):
        transitions = self._sources.setdefault(transition.source, {})
        transitions[transition.transition_id] = transition
        self._id_transitions[transition.transition_id] = transition

    def refresh(self, transitions):
        self._sources = {}
        self._id_transitions = {}
        for transition in transitions:
            self._register(transition)
        self._p_changed = True

    def getTransitions(self, source):
        try:
            return self._sources[source].values()
        except KeyError:
            return []

    def getTransition(self, source, transition_id):
        transition = self._id_transitions[transition_id]
        if transition.source != source:
            raise InvalidTransitionError
        return transition

    def getTransitionById(self, transition_id):
        return self._id_transitions[transition_id]

class WorkflowState(object):
    implements(IWorkflowState)
    state_key = "hurry.workflow.state"
    id_key  = "hurry.workflow.id"

    def __init__(self, context):
        # XXX okay, I'm tired of it not being able to set annotations, so
        # we'll do this. Ugh.
        from zope.security.proxy import removeSecurityProxy
        self.context = removeSecurityProxy(context)
        self._annotations = IAnnotations(self.context)

    def initialize(self):
        wf_versions = component.queryUtility(IWorkflowVersions)
        if wf_versions is not None:
            self.setId(wf_versions.createVersionId())

    def setState(self, state):
        if state != self.getState():
            self._annotations[self.state_key] = state

    def setId(self, id):
        # XXX catalog should be informed (or should it?)
        self._annotations[self.id_key] = id

    def getState(self):
        return self._annotations.get(self.state_key, None)

    def getId(self):
        return self._annotations.get(self.id_key, None)

class WorkflowInfo(object):
    implements(IWorkflowInfo)
    name = u''

    def __init__(self, context):
        self.context = context
        self.wf = component.getUtility(IWorkflow, name=self.name)

    @classmethod
    def info(cls, obj):
        return component.getAdapter(obj, IWorkflowInfo, name=cls.name)

    @classmethod
    def state(cls, obj):
        return component.getAdapter(obj, IWorkflowState, name=cls.name)

    def fireTransition(self, transition_id, comment=None, side_effect=None,
                       check_security=True):
        state = self.state(self.context)
        # this raises InvalidTransitionError if id is invalid for current state
        transition = self.wf.getTransition(state.getState(), transition_id)
        # check whether we may execute this workflow transition
        try:
            interaction = getInteraction()
        except NoInteraction:
            checkPermission = nullCheckPermission
        else:
            if check_security:
                checkPermission = interaction.checkPermission
            else:
                checkPermission = nullCheckPermission
        if not checkPermission(
            transition.permission, self.context):
            raise Unauthorized(self.context,
                               'transition: %s' % transition_id,
                               transition.permission)
        # now make sure transition can still work in this context
        if not transition.condition(self, self.context):
            raise ConditionFailedError
        # perform action, return any result as new version
        result = transition.action(self, self.context)
        if result is not None:
            if transition.source is None:
                self.state(result).initialize()
            # stamp it with version
            state = self.state(result)
            state.setId(self.state(self.context).getId())
            # execute any side effect:
            if side_effect is not None:
                side_effect(result)
            event = WorkflowVersionTransitionEvent(result, self.context,
                                                   transition.source,
                                                   transition.destination,
                                                   transition, comment)
        else:
            if transition.source is None:
                self.state(self.context).initialize()
            # execute any side effect
            if side_effect is not None:
                side_effect(self.context)
            event = WorkflowTransitionEvent(self.context,
                                            transition.source,
                                            transition.destination,
                                            transition, comment)
        # change state of context or new object
        state.setState(transition.destination)
        notify(event)
        # send modified event for original or new object
        if result is None:
            notify(ObjectModifiedEvent(self.context))
        else:
            notify(ObjectModifiedEvent(result))
        return result

    def fireTransitionToward(self, state, comment=None, side_effect=None,
                             check_security=True):
        transition_ids = self.getFireableTransitionIdsToward(state,
                                                             check_security)
        if not transition_ids:
            raise interfaces.NoTransitionAvailableError
        if len(transition_ids) != 1:
            raise interfaces.AmbiguousTransitionError
        return self.fireTransition(transition_ids[0],
                                   comment, side_effect, check_security)

    def fireTransitionForVersions(self, state, transition_id):
        id = self.state(self.context).getId()
        wf_versions = component.getUtility(IWorkflowVersions)
        for version in wf_versions.getVersions(state, id):
            if version is self.context:
                continue
            self.info(version).fireTransition(transition_id)

    def fireAutomatic(self):
        for transition_id in self.getAutomaticTransitionIds():
            try:
                self.fireTransition(transition_id)
            except ConditionFailedError:
                # if condition failed, that's fine, then we weren't
                # ready to fire yet
                pass
            else:
                # if we actually managed to fire a transition,
                # we're done with this one now.
                return

    def hasVersion(self, state):
        wf_versions = component.getUtility(IWorkflowVersions)
        id = self.state(self.context).getId()
        return wf_versions.hasVersion(state, id)

    def getManualTransitionIds(self, check_security=True):
        try:
            checkPermission = getInteraction().checkPermission
        except NoInteraction:
            checkPermission = nullCheckPermission
        if not check_security:
            checkPermission = nullCheckPermission
        return [transition.transition_id for transition in
                sorted(self._getTransitions(MANUAL)) if
                transition.condition(self, self.context) and
                checkPermission(transition.permission, self.context)]

    def getSystemTransitionIds(self):
        # ignore permission checks
        return [transition.transition_id for transition in
                sorted(self._getTransitions(SYSTEM)) if
                transition.condition(self, self.context)]

    def getFireableTransitionIds(self, check_security=True):
        return (self.getManualTransitionIds(check_security) +
                self.getSystemTransitionIds())

    def getFireableTransitionIdsToward(self, state, check_security=True):
        result = []
        for transition_id in self.getFireableTransitionIds(check_security):
            transition = self.wf.getTransitionById(transition_id)
            if transition.destination == state:
                result.append(transition_id)
        return result

    def getAutomaticTransitionIds(self):
        return [transition.transition_id for transition in
                self._getTransitions(AUTOMATIC)]

    def hasAutomaticTransitions(self):
        # XXX could be faster
        return bool(self.getAutomaticTransitionIds())

    def _getTransitions(self, trigger):
        # retrieve all possible transitions from workflow utility
        transitions = self.wf.getTransitions(
            self.state(self.context).getState())
        # now filter these transitions to retrieve all possible
        # transitions in this context, and return their ids
        return [transition for transition in transitions if
                transition.trigger == trigger]

class WorkflowVersions(object):
    implements(IWorkflowVersions)

    def getVersions(self, state, id):
        raise NotImplementedError

    def getVersionsWithAutomaticTransitions(self):
        raise NotImplementedError

    def createVersionId(self):
        while True:
            id = random.randrange(sys.maxint)
            if not self.hasVersionId(id):
                return id
        assert False, "Shouldn't ever reach here"

    def hasVersion(self, state, id):
        raise NotImplementedError

    def hasVersionId(self, id):
        raise NotImplementedError

    def fireAutomatic(self):
        for version in self.getVersionsWithAutomaticTransitions():
            IWorkflowInfo(version).fireAutomatic()

class WorkflowTransitionEvent(ObjectEvent):
    implements(interfaces.IWorkflowTransitionEvent)

    def __init__(self, object, source, destination, transition, comment):
        super(WorkflowTransitionEvent, self).__init__(object)
        self.source = source
        self.destination = destination
        self.transition = transition
        self.comment = comment

class WorkflowVersionTransitionEvent(WorkflowTransitionEvent):
    implements(interfaces.IWorkflowVersionTransitionEvent)

    def __init__(self, object, old_object, source, destination,
                 transition, comment):
        super(WorkflowVersionTransitionEvent, self).__init__(
            object, source, destination, transition, comment)
        self.old_object = old_object
