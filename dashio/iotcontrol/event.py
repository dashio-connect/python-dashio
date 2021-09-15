"""An Event class that wraps a set
"""
class Event:
    """
    Event class that call multiple functions/methods in a set
    """
    def __init__(self):
        self.handlers = set()

    def handle(self, handler):
        """Add handler to set

        Parameters
        ----------
        handler : function
            A function or method to be added to the set

        Returns
        -------
        Event
            Itself with the added handler
        """
        self.handlers.add(handler)
        return self

    def unhandle(self, handler):
        """Removes the handler from the set

        Parameters
        ----------
        handler : function or method
            A function or method to be removed from the set

        Returns
        -------
        Event
            Itself with the handler removed

        Raises
        ------
        ValueError
            IF the handler isn't in the set
        """
        try:
            self.handlers.remove(handler)
        except KeyError as not_in_set:
            raise ValueError("Handler is not handling this event, so cannot unhandle it.") from not_in_set
        return self

    def fire(self, *args, **kargs):
        """Runs all the handlers
        """
        for handler in self.handlers:
            handler(*args, **kargs)

    def get_handler_count(self):
        """Returns the number of handlers

        Returns
        -------
        int
            The number of handlers
        """
        return len(self.handlers)

    __iadd__ = handle
    __isub__ = unhandle
    __call__ = fire
    __len__ = get_handler_count
