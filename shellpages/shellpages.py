from copy import deepcopy
from collections import Sequence
from types import MethodType

import subprocess
import sys
import re

def _get_clear_word():
    if sys.platform == 'win32':
        return 'cls'
    else:
        return 'clear'

_CLEAR = _get_clear_word()

class ParseError(Exception):
    def __init__(self, message='Invalid input.'):
        Exception.__init__(self, message)

class Browser(object):
    """Runs a program made with shellpages.

    Browser keeps a directory of pages as a map of strings to page
    objects. The first page Browser displays is initialized from the
    'home' parameter. The browser always display the last page in it's
    'history' attribute. Any page name can be appended to the list.
    """
    def __init__(self, pages={}, home=None):
        self.pages = {}
        if home is None:
            self.history = []
        else:
            self.history = [home]

    def main(self):
        while True:
            page = self.pages[self.history[-1]]
            self._display(page)
            data = raw_input('> ')
            subprocess.call(_CLEAR, shell=True)
            if data == 'quit':
                sys.exit()
            self._process(page, data)

    def _display(self, page):
        if re.match(r'^<.+>$', page.__str__()):
            raise TypeError('Invalid object being displayed')
        print page

    def _process(self, page, data):
        try:
            key, args, kwargs = page.process(data)
            if key != 'invalid input':
                page.options[key](*args, **kwargs)
        except (TypeError, AttributeError) as e:
            no_process = r".+has no attribute 'process'"
            no_options = r".+has no attribute 'options'"
            not_callable = r".+is not callable"
            errors = filter(
                lambda r: re.match(r, e.args[0]),
                [no_process, no_options, not_callable])
            if errors:
                raise TypeError('Invalid object in the pages dictionary')

class Page(object):
    """Display a page to the user and provide methods for parsing input

    A Page holds data meant to be displayed to the user in a specific
    format. It has a predefined string method wrapper that displays a
    page when printed in the format:

      [Title]

      Body

      [1] Options

    Pages can also process strings meant as user input to create
    arguments meant to call its options with.
    """
    def __init__(self, title='', body='', options={}, order=[],
            parse=lambda self, data: ('input not checked', () ,{})):
        """Create a page object.

        Keyword Arguments:
            title ---- page title (default '')
            body ----- information provided by the page (default '')
            options -- map of keys to option objects (default {})
            order ---- list of keys for option display order (default [])
            parse ---- function meant to parse user input
                (default lambda data: (data, (), {})

        Raises:
            TypeError when options doesn't have an 'iteritems' method
            or parse is not callable
        """
        self.title = title
        self.body = body

        self._options = {}
        if not hasattr(options, 'iteritems'):
            raise TypeError('options must be a dictionary')
        for key, option in options.iteritems():
            self.add_option(key, option)
        self.order = order

        self._messages = []
        if parse is not None:
            self.parse = parse
        else:
            self.parse = _default_parse

    #-----Public methods-----

    def add_option(self, key, option):
        """Add an option to the page's option dictionary.

        Arguments:
            key ----- option's key-binding
            option -- option to be added

        Side Effects:
            Adds or overwrites an option object at the specified key in
            the page's option dictionary.

        Raises:
            TypeError when
                key is not a string
                option isn't callable
                option doesn't have a valid string (can't match the
                    regex r'^<.+>$')

            ValueError when
                key is more than 1 character
                option string is more than 79 characters
        """
        try:
            assert isinstance(key, basestring), TypeError(
                'key must be a string')
            assert len(key) == 1, ValueError('key must be 1 character')
            assert callable(option), TypeError(
                'option must be callable')
            assert not re.match(r'^<.+>$', option.__str__()), TypeError(
                'option must have a valid string method wrapper')
        except AssertionError as e:
            raise e.args[0]
        self._options[key] = option

    def remove_option(self, key):
        """Remove an option from the page's option dictionary.

        Arguments:
            key -- option's key-binding

        Side Effects:
            The key is also removed from the page's key-order list if
            present.

        Raises:
            ValueError if key isn't a key in the page's option
            dictionary.
        """
        try:
            del self._options[key]
        except KeyError:
            raise ValueError("'" + str(key) + "' is not an option")
        if key in self.order:
            self._order.remove(key)

    def add_message(self, message):
        """Add a message to display to the user.

        Arguments:
            message -- message to display

        Raises:
            TypeError if message is not string
        """
        if not isinstance(message, basestring):
            raise TypeError('message must be a string')
        self._messages.append(message)

    def remove_messages(self):
        self._messages = []

    def process(self, data):
        """Parse data into a key and arguments to call wtih an option

        Uses the internal parse method to process data, and return the
        results. If the data throws a ParseError it will add a message
        to the page's string method wrapper to let the user knkow their
        input is invalid.

        Raises
            ValueError if internal parse method doesn't return three values.
                Or if first value of internal parse method is not 1
                character, "invalid input", or "input not checked"
        """
        try:
            self.remove_messages()
            key, args, kwargs = self._parse(data)
            if key == 'input not checked':
                if data not in self.options.iterkeys():
                    raise ParseError(
                        'Invalid input. Please enter an option from ' +
                        str(self.order))
                key, args, kwargs = data, (), {}
            elif len(key) != 1 and key != 'invalid input':
                raise ValueError(
                    'Parse method must return key as 1 character or '+
                    '"invalid input"')
            return key, args, kwargs
        except ParseError as e:
            self.add_message(e.args[0])
            return 'invalid input', (), {}
        except (TypeError, ValueError) as e:
            not_iterable = r"'[\w\.]*\w+' object is not iterable"
            not_enough = r'need more than [12] values* to unpack'
            too_many = r'too many values to unpack'
            for pattern in (not_iterable, not_enough, too_many):
                if re.match(pattern, e.args[0]):
                    raise ValueError('parse method must return 3 values')
            raise e

    #-----Public properties-----

    @property
    def title(self):
        """The title of the page.

        Setting the title Raises:
            TypeError if not a string
            ValueError when
                longer than 1 line
                more than 77 characters
        """
        return self._title

    @title.setter
    def title(self, other):
        if not isinstance(other, basestring):
            raise TypeError('Title must be a string')
        elif other.find('\n') != -1:
            raise ValueError('Title must be no longer than 1 line')
        elif len(other) > 77:
            raise ValueError('Title must be less than 78 characters')
        self._title = other

    @property
    def body(self):
        """The body of the page.

        Setting the body raises:
            TypeError if not a string
            ValueError if any of the lines are more than 77 characters
        """
        return self._body

    @body.setter
    def body(self, other):
        if type(other) is not str:
            raise TypeError('Body must be a string'.format(other))
        for line in other.split('\n'):
            if len(line) > 79:
                raise ValueError(
                    'Each line in the body must be less than 80 characters')
        self._body = other

    @property
    def options(self):
        """A dictionary of the pages options.

        Note that accessing this property only accesses a deep copy of
        the dictionary. If you want to modify the dictionary, use the
        add_option and remove_option methods
        """
        return deepcopy(self._options)

    @property
    def order(self):
        """A list of key-bindings in their preferred display order.

        Because dictionaries have no particular order, the page's
        string method wrapper displays each option in the order they
        appear in this list.

        Setting order Raises:
            TypeError if not an ordered container
            ValueError if any key isn't in options
        """
        return self._order[:]

    @order.setter
    def order(self, other):
        if not isinstance(other, Sequence):
            raise TypeError('order must be an ordered container')
        for key in other:
            if key not in self.options.iterkeys():
                raise ValueError('each key in order must be a key in options')
        self._order = other

    @property
    def parse(self):
        """An internal method that parses data for the process method

        Parse defaults to returning ('input not checked', (), {}), but
        the method can be defined by the user upon initialization or by
        setting the set-only attribute 'parse'

        If the parse method returns 'input not checked' as the first
        value it chekcs to see if data is a key in the page's options.
        If its not, it adds a default error message to the page, and
        the Browser's main method will bypass calling any options.

        If the parse method returns 'invalid input' as the first value,
        no additional messages will be added to the page but the
        Browser will still bypass calling any options.

        Raises:
            AttirbuteError if accessed with get method wrapper
            TypeError if object being set is not callable"""
        raise AttributeError('parse is a set-only attribute')

    @parse.setter
    def parse(self, other):
        if not callable(other):
            raise TypeError('parse must be callable')
        self._parse = MethodType(other, self)

    #-----Method Wrappers-----

    def __str__(self):
        s = ''
        if self.title:
            s += '[{}]\n\n'.format(self.title)
        if self.body:
            s += self.body + '\n\n'
        for key in self.order:
            s += self.options[key].__str__() + '\n'
        for message in self._messages:
            s += '\n' + message + '\n'
        return s

def _default_parse(self, data):
    return 'input not checked', (), {}

class Option(object):
    """An option to display to the user and call for its functionality.

    All properties of an option instance are meant to be immutable.
    """

    def __init__(self, key, text, function):
        """Create an option object

        Arguments:
            key ------- option key-binding
            text ------ option text
            function -- option functionality

        Raises:
            TypeError if key and text args are not strings or function
                is not callable
            ValueError if length of key is not 1 or length of text is
                greater than 72
        """
        # Defensive programming
        try:
            # Check key arg
            assert isinstance(key, basestring), TypeError(
                'key must be a string')
            assert len(key) == 1, ValueError('key must be 1 character')

            # Check text arg
            assert isinstance(text, basestring), TypeError(
                'text must be a string')
            assert len(text) <= 72, ValueError(
                'text cannot be more than 72 characters')

            # Check function arg
            assert callable(function), TypeError(
                'function must be callable')

        # Raise appropriate errors
        except AssertionError as e:
            raise e.args[0]

        # Set attributes
        self._key = key
        self._text = text
        self._function = function

    #-----Public properties-----

    @property
    def key(self):
        """Key-binding for the option.

        The key property is used to inform the user which key needs to
        be pressed to call the option. It's also meant to be the same
        character of the key that maps to the option in a key-option
        map. It cannot be longer than 1 character.
        """
        return self._key

    @property
    def text(self):
        """Display text for the option.

        The text property is meant to breifly inform the user of what
        the option does. It cannot be longer than 72 characters.
        """
        return self._text


    #-----Method Wrappers-----

    def __str__(self):
        return '[{0.key}] {0.text}'.format(self)

    def __call__(self, *args, **kwargs):
        return self._function(*args, **kwargs)
