"""
MIT License

Copyright (c) 2020 DashIO-Connect

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
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
