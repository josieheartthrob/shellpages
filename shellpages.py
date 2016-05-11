import subprocess, time

class ParseError(Exception):
    def __init__(self, message='Invalid input.'):
    Exception.__init__(self, message)

class Menu(object):
    """A database of pages to display pages to the user.

    Public methods:
        push ----- Go to another page
        back ----- Go to the previous page

    Calling the menu calls the last page on the page stack.

    The push and back methods are intended to be used right before
        calling the menu again.
    """

    def __init__(self):
        """Create a Menu object."""
        self._pages = []

    @property
    def pages(self):
        return self._pages[:]

    #-----Public methods-----

    def push(self, page):
        """Push the specified page to the page stack.

        Arguments:
            page ----- page object

        Side Effects:
            Modifies the private pages property.
        """
        if not callable(page):
            raise TypeError('Only callable objects can be ' +
                             'added to the page stack.')
        self._pages.append(page)

    def back(self):
        """Remove the last page from the page stack.

        Side Effects:
            Modifies the private pages property.
        """
        self._pages = self._pages[:-1]

    def home(self):
        """Remove all pages from the page stack except for the first.

        Side Effects:
            Modifies the private pages property."""
        self._pages = self._pages[:1]



    #-----Magic methods-----

    def __call__(self):
        self._pages[-1]()

class Page(object):
    """"""

    def __init__(self, header, body, options, order,
                 parse=lambda x: (x, (), {})):
        """Create a page object.

        Arguments:
            header ----- A string that let's the user know what the
                            page is about.
            body ------- A string that gives the user any information.
            options ---- a dictionary of option objects where each key is
                            the relative item's (option object's) key
            order ------ An ordered container object as the order in which
                            to display the options to the page

        Keyword Arguments:
            parse ------ A callable object that parses the data entered by
                         the user when the page is called.

              It should return an a key to access one of the page's options,
              and arguments and keyword arguments to call the option with.
              It should raise a ParseError if the data entered by the user
              is invalid.
        """
        self._header = header
        self._body = body
        self._options = options
        self._order = order
        self._parse = parse

    #-----Public properties-----

    @property
    def options(self):
        return self._options.copy()

    @property
    def order(self):
        return self._order[:]

    @property
    def header(self):
        return self._header

    @property
    def body(self):
        return self._body


    #-----Public property prescriptors-----

    @options.setter
    def options(self, other):
        if not callable(other):
            raise TypeError(
                '{} must be a callable object'.format(type(other)))
        self._options = options

    @order.setter
    def order(self, other):
        self._order = other

    @body.setter
    def body(self, other):
        if not hasattr(other, '__str__'):
            raise TypeError('{} must be a string'.format(other))
        self._body = other


    #-----Magic methods-----

    def __str__(self):
        s = ''
        if self._header:
            s += '[{}]\n\n'.format(self.header)
        if self._body:
            s += self._body + '\n\n'
        for key in self._order:
            s += self.options[key].__str__() + '\n'
        return s

    def __call__(self):
        key = ''
        i = len(self.body)
        while True:
            subprocess.call('cls', shell=True)
            print self
            if len(self.body) > i:
                self.body = self.body[:i]
            try:
                key, args, kwargs = self._parse(raw_input('> '))
                return self.options[key](*args, **kwargs)
            except ParseError as e:
                self.body += '\n\n'+e.args[0]

class Option(object):
    """An option to display and call.

    Options can be displayed to the user by printing them. They can also be
    called for their functionality.

    Public Properties:
        key ---- the string that should be used as a key to access
                   the option when creating an option dictionary.
        name --- the string display to the user as the option's name."""

    def __init__(self, key, name, function):
        """Create an option object

        Arguments:
            key --------- a string to access the option from a
                            dictionary.
            name -------- a string to display as the option name.
            function ---- a callable object that gives the option
                            functionality.
        """
        # Defensive programming
        try:
            assert type(key) in (str, int, float, long), TypeError(
                'key must be a string or number')
            assert type(name) is str, TypeError('name must be a string')
            assert callable(function), TypeError(
                'function must be a callable object')
        except AssertionError as e:
            raise e.args[0]

        self._key = key
        self._name = name
        self.__function = function

    #-----Public properties-----

    # Immutable
    @property
    def key(self):
        return self._key

    @property
    def name(self):
        return self._name


    #-----Private properties-----

    @property
    def _function(self):
        # The functionality of the option
        return self.__function


    #-----Magic methods-----

    def __str__(self):
        return '> {0.key} - {0.name}'.format(self)

    def __call__(self, *args, **kwargs):
        return self._function(*args, **kwargs)
