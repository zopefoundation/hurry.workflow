from zope.interface import Interface, Attribute
from zope.component.interfaces import IObjectEvent

MANUAL = 0
AUTOMATIC = 1
SYSTEM = 2

class InvalidTransitionError(Exception):
    pass

class NoTransitionAvailableError(InvalidTransitionError):
    pass

class AmbiguousTransitionError(InvalidTransitionError):
    pass

class ConditionFailedError(Exception):
    pass

class IWorkflow(Interface):
    """Defines workflow in the form of transition objects.

    Defined as a utility.
    """
    def initialize():
        """Do any needed initialization.

        Such as initialization with the workflow versions system.
        """

    def refresh(transitions):
        """Refresh workflow completely with new transitions.
        """
        
    def getTransitions(source):
        """Get all transitions from source.
        """

    def getTransition(source, transition_id):
        """Get transition with transition_id given source state.

        If the transition is invalid from this source state,
        an InvalidTransitionError is raised.
        """

    def getTransitionById(transition_id):
        """Get transition with transition_id.
        """

class IWorkflowState(Interface):
    """Store state on workflowed objects.

    Defined as an adapter.
    """
    
    def setState(state):
        """Set workflow state for this object.
        """
        
    def setId(id):
        """Set workflow version id for this object.

        This is used to mark all versions of an object with the
        same id.
        """
        
    def getState():
        """Return workflow state of this object.
        """

    def getId():
        """Get workflow version id for this object.

        This is used to mark all versions of an object with the same id.
        """
        
class IWorkflowInfo(Interface):
    """Get workflow info about workflowed object, and drive workflow.

    Defined as an adapter.
    """

    def setInitialState(state, comment=None):
        """Set initial state for the context object.

        Will also set a unique id for this new workflow.
        
        Fires a transition event.
        """
        
    def fireTransition(transition_id, comment=None, side_effect=None,
                       check_security=True):
        """Fire a transition for the context object.

        There's an optional comment parameter that contains some
        opaque object that offers a comment about the transition.
        This is useful for manual transitions where users can motivate
        their actions.

        There's also an optional side effect parameter which should
        be a callable which receives the object undergoing the transition
        as the parameter. This could do an editing action of the newly
        transitioned workflow object before an actual transition event is
        fired.

        If check_security is set to False, security is not checked
        and an application can fire a transition no matter what the
        user's permission is.
        """

    def fireTransitionToward(state, comment=None, side_effect=None,
                             check_security=True):
        """Fire transition toward state.

        Looks up a manual transition that will get to the indicated
        state.

        If no such transition is possible, NoTransitionAvailableError will
        be raised.

        If more than one manual transitions are possible,
        AmbiguousTransitionError will be raised.
        """
        
    def fireTransitionForVersions(state, transition_id):
        """Fire a transition for all versions in a state.
        """

    def fireAutomatic():
        """Fire automatic transitions if possible by condition.
        """
        
    def hasVersion(state):
        """Return true if a version exists in state.
        """
        
    def getManualTransitionIds():
        """Returns list of valid manual transitions.

        These transitions have to have a condition that's True.
        """

    def getManualTransitionIdsToward(state):
        """Returns list of manual transitions towards state.
        """
        
    def getAutomaticTransitionIds():
        """Returns list of possible automatic transitions.

        Condition is not checked.
        """
        
    def hasAutomaticTransitions():
        """Return true if there are possible automatic outgoing transitions.

        Condition is not checked.
        """

class IReadWorkflowVersions(Interface):
    
    def getVersions(state, id):
        """Get all versions of object known for this id and state.
        """

    def getVersionsWithAutomaticTransitions():
        """Get all versions that have outgoing transitions that are automatic.
        """

    def createVersionId():
        """Return new unique version id.
        """
        
    def hasVersion(id, state):
        """Return true if a version exists with the specific workflow state.
        """

    def hasVersionId(id):
        """Return True if version id is already in use.
        """

class IWriteWorkflowVersions(Interface):
    def fireAutomatic():
        """Fire all automatic transitions in the workflow (for all versions).
        """
    
class IWorkflowVersions(IReadWorkflowVersions, IWriteWorkflowVersions):
    """Interface to get information about versions of content in workflow.

    This can be implemented on top of the Zope catalog, for instance.

    Defined as a utility
    """

class IWorkflowTransitionEvent(IObjectEvent):
    source = Attribute('Original state or None if initial state')
    destination = Attribute('New state') 
    transition = Attribute('Transition that was fired or None if initial state')
    comment = Attribute('Comment that went with state transition')

class IWorkflowVersionTransitionEvent(IWorkflowTransitionEvent):
    old_object = Attribute('Old version of object')
