#!/usr/bin/env python

def place_cursor(line, col):
    return '\033[{0};{1}H'.format(line,col)

def up_lines(n):
    return '\033[{0}A'.format(n)
up_line = up_lines(1)

def down_lines(n):
    return '\033[{0}B'.format(n)
down_line = down_lines(1)

def advance(n):
    return '\033[{0}C'.format(n)
forward = advance(1)

def reverse(n):
    return '\033[{0}D'.format(n)
backward = reverse(1)

clear_screen = '\033[2J'
clear_to_endl = '\033[K'
start_line = '\r'
