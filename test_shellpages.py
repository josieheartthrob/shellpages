from shellpages import *

def test_menu():
    menu = Menu()

    def parse_1(data):
        args, kwargs = [], {}
        if data == 'n':
            args = [page_2]
        elif data != 'q':
            raise ParseError('"{}" is not a valid input'.format(data))
        return data, args, kwargs

    def parse_2(data):
        args, kwargs = [], {}
        if data == 'n':
            args = [page_3]
        elif data != 'b':
            raise ParseError('"{}" is not a valid input'.format(data))
        return data, args, kwargs

    def parse_3(data):
        if data not in page_3.order:
            raise ParseError('"{}" is not a valid input'.format(data))
        return data, (), {}

    page_1 = Page('test page', '', {
            'n': Option('n', 'next page', menu.push),
            'q': Option('q', 'quit', quit)},
        ['n', 'q'], parse_1)

    page_2 = Page('test page 2', '', {
            'n': Option('n', 'next page', menu.push),
            'b': Option('b', 'back', menu.back)},
        ['n', 'b'], parse_2)

    page_3 = Page('', 'this is the 3rd test page', {
            'b': Option('b', 'back', menu.back),
            'h': Option('h', '1st page', menu.home)},
        ['b', 'h'], parse_3)

    menu.push(page_1)
    while True:
        menu()

def test_page():
    def say(something):
        subprocess.call('cls', shell=True)
        print something
        raw_input('> ')

    def bye():
        say('bye')
        subprocess.call('cls', shell=True)
        quit()

    def parse(data):
        key, args, kwargs = data, (), {}
        if data == 'h':
            args = ('hi',)
        elif data != 'b':
            raise ParseError('"{}" is not a valid input.'.format(data))
        return key, args, kwargs

    page = Page('test page', 'some\narbitrary\nwords',
        {'h': Option('h', 'say hi', say),
         'b': Option('b', 'say bye', bye)},
        ['h', 'b'], parse)

    while True:
        page()

def test_option():
    def f(something):
        subprocess.call('cls', shell=True)
        print something
    option = Option('h', 'say hello', f)
    key = ''
    while key != 'h':
        subprocess.call('cls', shell=True)
        print option
        key = raw_input('\n> ')
    option('Hello, world.')

if __name__ == '__main__':
    test_menu()
    test_page()
    test_option)_
