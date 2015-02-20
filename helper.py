__author__ = "Nico Tonnhofer <tonnhofer@gmail.com>"
__copyright__ = "Copyright 2015, Nico Tonnhofer"
__license__ = "GPL"

from math import copysign, fabs


def sign(number):
    return copysign(1, number)


def uint(number, bit):
    maxbit = 2**bit - 1
    if number > maxbit:
        number = maxbit
        # print("uint_max_reached")
    # number = maxbit if number > maxbit else number
    return int(number)


def int_(number, bit):
    half_bit = 2**bit / 2 - 1
    number_sign = sign(number)
    number = fabs(number)
    if number > half_bit:
        number = half_bit
        # print("int_max_reached")
    # number = number if number < halfbit else number
    number *= number_sign
    return int(number)


def int16_t(number):
    return int_(number, 16)


def int32_t(number):
    return int_(number, 32)


def uint8_t(number):
    return uint(number, 8)


def uint16_t(number):
    return uint(number, 16)


def uint32_t(number):
    return uint(number, 32)


def uint64_t(number):
    return uint(number, 64)


def uint42_t(number):
    return uint(number, 42)
