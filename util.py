__author__ = "Nico Tonnhofer <tonnhofer@gmail.com>"
__copyright__ = "Copyright 2015, Nico Tonnhofer"
__license__ = "GPL"

import datetime


def fsqrt(number):
    root = 0
    bit = 1 << 30

    while bit > number: bit >>= 2

    while bit != 0:
        if number >= root + bit:
            number -= (root + bit)
            root += (bit << 1)

        root >>= 1
        bit >>= 2

    return root


def sqrt7(number):

    number += 127 <<23
    number >>= 1

    return number


def test(function, count):
    start = datetime.datetime.now()

    for i in range(0, count):
        function(i)
        i += 1

    end = datetime.datetime.now()
    print(end-start)