# ../memory/hooks.py

"""Provides memory hooking functionality."""

# =============================================================================
# >> IMPORTS
# =============================================================================
# Source.Python Imports
#   Core
from core import AutoUnload
#   Memory
from _memory import HookType
from memory import Function
#   Filters
from filters.entities import EntityIter
#   Listeners
from listeners import OnEntityCreated
#   Entities
from entities.entity import Entity


# =============================================================================
# >> ALL DECLARATION
# =============================================================================
__all__ = ('HookType',
           'EntityPostHook',
           'EntityPreHook',
           'PostHook',
           'PreHook',
           )


# =============================================================================
# >> CLASSES
# =============================================================================
class _Hook(AutoUnload):

    """Create pre and post hooks that auto unload."""

    def __init__(self, function):
        """Verify the given function is a Function object and store it."""
        # Is the function to be hooked a Function instance?
        if not isinstance(function, Function):

            # Raise an error as we can only hook Function instances
            raise TypeError(
                "'" + type(function).__name__ +
                "' object is not a Function instance.")

        # Store the function
        self.function = function

    def __call__(self, callback):
        """Store the callback and hook it."""
        # Store the callback
        self.callback = callback

        # Hook the callback to the Function
        self.function.add_hook(self.hook_type, self.callback)

        # Return the object
        return self

    @property
    def hook_type(self):
        """Raise an error if the inheriting class does not have their own."""
        raise NotImplementedError('No hook_type defined for class.')

    def _unload_instance(self):
        """Unregister the hook on script unload."""
        self.function.remove_hook(self.hook_type, self.callback)


class PreHook(_Hook):

    """Decorator class used to create pre hooks that auto unload."""

    hook_type = HookType.PRE


class PostHook(_Hook):

    """Decorator class used to create post hooks that auto unload."""

    hook_type = HookType.POST


class _EntityHook(AutoUnload):

    """Create entity pre and post hooks that auto unload."""

    def __init__(self, entity_class_names, function_name):
        """Initialize the hook object.

        @param <entity_class_names>:
        The name of the entity class or a list of entity classes. E.g
        'cs_bot' or ['cs_bot', 'player'].

        @<function_name>:
        The name of the function to hook. The function must be available
        through the Entity class.
        """
        if isinstance(entity_class_names, str):
            entity_class_names = [entity_class_names]

        self.entity_class_names = entity_class_names
        self.function_name = function_name
        self.function = None
        self.callback = None

    def __call__(self, callback):
        """Store the callback and try initializing the hook."""
        self.callback = callback

        # Try initializing the hook...
        for entity in EntityIter(
                self.entity_class_names, return_types='entity'):
            # Yay! There is an entity of the given class name
            self.initialize(entity)
            return self

        # Initialization failed. There is currently no entity with the given
        # class name. So, we need to wait until such an entity has been
        # created.
        _waiting_entity_hooks.append(self)
        return self

    @property
    def hook_type(self):
        """Raise an error if the inheriting class does not have their own."""
        raise NotImplementedError('No hook_type defined for class.')

    def initialize(self, entity):
        """Initialize the hook. Return True if the initialization was
        successful.
        """
        if entity.classname not in self.entity_class_names:
            return False

        self.function = getattr(entity, self.function_name)
        self.function.add_hook(self.hook_type, self.callback)
        return True

    def _unload_instance(self):
        """Unload the hook."""
        if self.function is not None:
            self.function.remove_hook(self.hook_type, self.callback)
        else:
            # If the function is None, the hook wasn't initialized, so it's
            # still in the _waiting_entity_hooks dict
            _waiting_entity_hooks.remove(self)


class EntityPreHook(_EntityHook):

    """Decorator class used to create entity pre hooks that auto unload."""

    hook_type = HookType.PRE


class EntityPostHook(_EntityHook):

    """Decorator class used to create entity post hooks that auto unload."""

    hook_type = HookType.POST


class _WaitingEntityHooks(list):

    """A dictionary to store hooks waiting for intialization."""

    def initialize(self, index):
        """Initialize all hooks waiting for the given entity."""
        # There is nothing to do if no hook is waiting
        if not self:
            return

        entity = Entity(index)
        for hook in tuple(self):
            # Try initializing the hook
            if hook.initialize(entity):
                # If it succeeded, remove the hook from the waiting list
                self.remove(hook)

_waiting_entity_hooks = _WaitingEntityHooks()


# =============================================================================
# >> LISTENERS
# =============================================================================
@OnEntityCreated
def on_entity_created(index, ptr):
    """Called when a new entity has been created."""
    _waiting_entity_hooks.initialize(index)
