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
class RingBuffer:
    """ class that implements a not-yet-full buffer """
    def __init__(self, size_max):
        self.max = size_max
        self.data = []

    # pylint: disable=invalid-name
    class __Full:
        """ class that implements a full buffer """
        def append(self, val):
            """ Append an element overwriting the oldest one. """
            # pylint: disable=access-member-before-definition
            self.data[self.cur] = val
            self.cur = (self.cur + 1) % self.max

        def get(self):
            """ return list of elements in correct order """
            return self.data[self.cur:] + self.data[:self.cur]

        def get_latest(self):
            """Get the last item in the buffer
            """
            indx = self.cur - 1
            if indx < 0:
                indx = self.max - 1
            return self.data[indx]

        def empty(self):
            """Returns if empty
            """
            return False

    def append(self, val):
        """append an element at the end of the buffer"""
        self.data.append(val)
        if len(self.data) == self.max:
            self.cur = 0
            # Permanently change self's class from non-full to full
            self.__class__ = self.__Full

    def get_latest(self):
        """Get the last item in the buffer
        """
        return self.data[-1]

    def empty(self) -> bool:
        """
        Returns if empty
        """
        if not self.data:
            return True
        return False

    def get(self):
        """ Return a list of elements from the oldest to the newest. """
        return self.data
