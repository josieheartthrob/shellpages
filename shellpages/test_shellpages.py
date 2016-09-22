from shellpages import *

from copy import deepcopy
from collections import Sequence

from unittest import TestCase
from test.test_support import run_unittest

class BrowserTest(TestCase):
    def setUp(self):
        self.browser = Browser()

    def tearDown(self):
        del self.browser
        self.browser = None

    def test_display(self):
        self.assertRaisesRegexp(
            TypeError, "Invalid object being displayed",
            self.browser._display, lambda: "Invalid")

    def test_process(self):
        self.assertRaisesRegexp(
            TypeError, "Invalid object in the pages dictionary",
            self.broeser._process, "[1] Option 1", "1")

class PageTest(TestCase):
    def setUp(self):
        self.page = Page(
            title='Test Page', body='This is the body of\nthe test page',
            options = {
                '1': Option('1', 'Option 1', lambda: 'This is option 1'),
                '2': Option('2', 'Option 2', lambda: 'This is option 2')},
            order=['1', '2'])

    def tearDown(self):
        del self.page
        self.page = None

    def test_title(self):
        page = deepcopy(self.page)
        title = page.title
        self.assertEqual('Test Page', title)
        title = 'Not Test Page'
        self.assertNotEqual(title, page.title)

        with self.assertRaisesRegexp(TypeError, r'Title must be a string'):
            page.title = 1
        with self.assertRaisesRegexp(
                ValueError, r'Title must be no longer than 1 line'):
            page.title = 'A multi-line\ntitle'
        with self.assertRaisesRegexp(
                ValueError, r'Title must be less than 78 characters'):
            page.title = ('This title is very very very very very very very ' +
                          'very very very very very long')
        page.title = 'A Valid Title'
        self.assertEqual('A Valid Title', page.title)

    def test_body(self):
        page = deepcopy(self.page)
        body = page.body
        self.assertEqual('This is the body of\nthe test page', body)
        body = 'Not the body'
        self.assertNotEqual(body, page.body)
        page.body = 'A valid body'
        self.assertEqual('A valid body', page.body)

        with self.assertRaisesRegexp(TypeError, r'Body must be a string'):
            page.body = 664.3
        with self.assertRaisesRegexp(
                ValueError,
                r'Each line in the body must be less than 80 characters'):
            page.body = ("A page body with\n" +
                         "one line that's very very very very very very " +
                         "very very very very very very long")

    def test_add_option(self):
        page = deepcopy(self.page)
        self.assertFalse('3' in page._options.keys())
        self.assertFalse('3' in page._order)
        page.add_option(
            '3', Option('3', 'Option 3', lambda: 'This is option 3'))
        self.assertTrue('3' in page._options.keys())
        self.assertFalse('3' in page.order)

        self.assertRaisesRegexp(
            TypeError, r'key must be a string', page.add_option,
            4, Option('4', 'Option 4', lambda: 'This is option 4'))
        self.assertRaisesRegexp(
            ValueError, r'key must be 1 character', page.add_option,
            '[4]', Option('4', 'Option 4', lambda: 'This is option 4'))
        self.assertRaisesRegexp(
            TypeError, r'option must be callable', page.add_option,
            '4', 'Option 4')
        self.assertRaisesRegexp(
            TypeError, r'option must have a valid string method wrapper',
            page.add_option, '4', round)

    def test_remove_option(self):
        page = deepcopy(self.page)
        self.assertTrue('2' in page._order)
        page.remove_option('2')
        self.assertFalse('2' in page._options.keys())
        self.assertFalse('2' in page._order)
        self.assertRaisesRegexp(
            ValueError, r"'3' is not an option", page.remove_option, '3')

    def test_order(self):
        page = deepcopy(self.page)
        order = page.order
        self.assertEqual(['1', '2'], order)
        order.append('3')
        self.assertNotEqual(order, page.order)
        with self.assertRaisesRegexp(
                ValueError, 'each key in order must be a key in options'):
            page.order = order

        with self.assertRaisesRegexp(
                TypeError, 'order must be an ordered container'):
            page.order = {'1', '2'}

        page.order = ['1']
        self.assertEqual(['1'], page.order)

    def test_messages(self):
        page = deepcopy(self.page)
        page.add_message('This is a test message')
        self.assertEqual(['This is a test message'], page._messages)
        self.assertRaisesRegexp(
            TypeError, 'message must be a string', page.add_message, True)
        page.remove_messages()
        self.assertEqual([], page._messages)

    def test_parse(self):
        page = deepcopy(self.page)
        with self.assertRaisesRegexp(
                AttributeError, 'parse is a set-only attribute'):
            parse = page.parse

        def parse(self, data):
            return 'Hello, world!', (), {}
        page.parse = parse
        with self.assertRaisesRegexp(TypeError, 'parse must be callable'):
            page.parse = 'Not a valid parse method'
        self.assertEqual(('Hello, world!', (), {}), page._parse('1'))

    def test_process(self):
        page = deepcopy(self.page)
        self.assertEqual(('invalid input', (), {}), page.process('3'))
        self.assertEqual(
            ["Invalid input. Please enter an option from ['1', '2']"],
            page._messages)
        self.assertEqual(('1', (), {}), page.process('1'))
        self.assertEqual([], page._messages)

        def parse(self, data):
            key, args, kwargs = data, (), {}
            if data == '1':
                self.add_message('You chose Option 1')
            elif data[0] == '2':
                key = data[0]
                self.add_message('You chose Option 2')
                if len(data) == 1:
                    raise ParseError('Option 2 must be called with arguments')
                self.add_message('Your arguments were: "' + data[1:] + '"')
            elif data[0] == '3':
                key = 'not a valid key'
            else:
                return 'invalid input', (), {}
            return key, (), {}
        page.parse = parse

        page.process('1')
        self.assertEqual(['You chose Option 1'], page._messages)

        page.process('2')
        self.assertEqual(
            ['You chose Option 2', 'Option 2 must be called with arguments'],
            page._messages)

        page.process('2 Hello, world!')
        self.assertEqual(
            ['You chose Option 2', 'Your arguments were: " Hello, world!"'],
            page._messages)

        self.assertRaisesRegexp(
            ValueError,
            r'Parse method must return key as 1 character or "invalid input"',
            page.process, '3')

        invalid_parsers = [
            lambda self, data: 15.3,
            lambda self, data: [data, ()],
            lambda self, data: [data, (), {}, True]]
        for parse in invalid_parsers:
            page.parse = parse
            self.assertRaisesRegexp(
                ValueError, 'parse method must return 3 values',
                page.process, '1')

    def test_str(self):
        page = deepcopy(self.page)
        expected = (
            '[Test Page]\n' +
            '\n' +
            'This is the body of\n' +
            'the test page\n' +
            '\n' +
            '[1] Option 1\n' +
            '[2] Option 2\n')
        self.assertEqual(expected, page.__str__())

        page.title = 'A Different Title'
        expected = (
            '[A Different Title]\n' +
            '\n' +
            'This is the body of\n' +
            'the test page\n' +
            '\n' +
            '[1] Option 1\n' +
            '[2] Option 2\n')
        self.assertEqual(expected, page.__str__())

        page.body = 'The altered body of the test page'
        expected = (
            '[A Different Title]\n' +
            '\n' +
            'The altered body of the test page\n' +
            '\n' +
            '[1] Option 1\n' +
            '[2] Option 2\n')

        page.add_option(
            '3', Option('3', 'Option 3', lambda: 'This is option 3'))
        self.assertEqual(expected, page.__str__())

        order = page.order
        order.append('3')
        page.order = order
        expected = (
            '[A Different Title]\n' +
            '\n' +
            'The altered body of the test page\n' +
            '\n' +
            '[1] Option 1\n' +
            '[2] Option 2\n' +
            '[3] Option 3\n')
        self.assertEqual(expected, page.__str__())

        page.remove_option('2')
        expected = (
            '[A Different Title]\n' +
            '\n' +
            'The altered body of the test page\n' +
            '\n' +
            '[1] Option 1\n' +
            '[3] Option 3\n')
        self.assertEqual(expected, page.__str__())

        page.order = ['3', '1']
        expected = (
            '[A Different Title]\n' +
            '\n' +
            'The altered body of the test page\n' +
            '\n' +
            '[3] Option 3\n' +
            '[1] Option 1\n')
        self.assertEqual(expected, page.__str__())

        page.add_message('message 1')
        page.add_message('message 2')
        expected = (
            '[A Different Title]\n' +
            '\n' +
            'The altered body of the test page\n' +
            '\n' +
            '[3] Option 3\n' +
            '[1] Option 1\n' +
            '\n' +
            'message 1\n' +
            '\n' +
            'message 2\n')
        self.assertEqual(expected, page.__str__())

        page.remove_messages()
        expected = (
            '[A Different Title]\n' +
            '\n' +
            'The altered body of the test page\n' +
            '\n' +
            '[3] Option 3\n' +
            '[1] Option 1\n')
        self.assertEqual(expected, page.__str__())

class OptionTest(TestCase):
    def setUp(self):
        self.option = Option('1', 'Test', lambda: 'This is a test.')

    def tearDown(self):
        del self.option
        self.option = None

    def test_key(self):
        self.assertEqual(self.option.key, '1')
        with self.assertRaises(AttributeError):
            self.option.key = '0'

        with self.assertRaisesRegexp(TypeError, r'key must be a string'):
            option = Option(True, 'Test', lambda: 'This is a test.')
        with self.assertRaisesRegexp(
                ValueError, r'key must be 1 character'):
            option = Option('12', 'Test', lambda: 'This is a test.')

    def test_text(self):
        self.assertEqual(self.option.text, 'Test')
        with self.assertRaises(AttributeError):
            self.option.text = 'Attribute Error'

        with self.assertRaisesRegexp(TypeError, r'text must be a string'):
            option = Option('1', 44.44, lambda: 'This is a test.')
        with self.assertRaisesRegexp(
                ValueError, r'text cannot be more than 72 characters'):
            option = Option(
                '1', ('This is a very very very very very very very very ' +
                      'very very very long string'),
                lambda: 'This is a test.')

    def test_functionality(self):
        self.assertEqual(self.option(), 'This is a test.')
        with self.assertRaisesRegexp(TypeError, r'function must be callable'):
            option = Option('1', 'Test', 'This is a test.')

    def test_str(self):
        self.assertEqual(self.option.__str__(), '[1] Test')

def main():
    run_unittest(OptionTest)
    run_unittest(PageTest)

if __name__ == '__main__':
    main()
