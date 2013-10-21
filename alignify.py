#!/usr/bin/python
#
# Made by Emil Ernerfeldt (emil ernerfeldt at gmail dot com)
# https://github.com/emilk/alignify
# Feel free to use, abuse, modify, redistribute.
#
# Usage:  cat test.txt | python alignify_cli.py
# Or:     python alignify_cli.py test.txt
#
# Or import and use as a python module
#
# Or use in Sublime Text 3:
# { "keys": ["super+shift+a"], "command": "alignify" }
#
#
# Changelog:
# 2.0  - 2013-08-23
# 2.1  - 2013-10-20  - Aligns numbers by decimal point
# 2.11 - 2013-10-21  - Fixes for number alignment and g_continuous == False


import re


# If set, will ignore empty lines and will not break on indentation change
g_continuous = True


# For debugging
def spam(*stuff):
	#print( 'SPAM: ' + ''.join(map(str,stuff)) )
	pass


def alignify_string(s):
	lines = s.split('\n')
	return alignify_lines( lines )


def alignify_lines(lines):
	# Split into blocks of same indentation:
	left        = []
	right       = []
	last_indent = None
	last_line   = None

	output = ""

	for ix, line in enumerate(lines):
		spam("line: '", line, "'")

		m    = re.match("(\t*)(.*)", line)
		tabs = m.group(1)
		meat = m.group(2)

		#spam("tabs: '", tabs, "'")
		#spam("meat: '", meat, "'")

		# Replace non-leading tabs with spaces. Any number of spaces will work.
		meat = re.sub(r'\t', '  ', meat)
		tokens = tokenize(meat)

		if last_indent != None and tabs != last_indent:
			# A change in indentation
			if g_continuous and (line == '' or last_line == ''):
				# Ignore empty line
				pass
			else:
				spam("alignify_lines: indentation break: '", tabs, "'")
				output += align_and_collect(left, right)
				left  = []
				right = []

		left.append(  tabs   )
		right.append( tokens )
		last_indent = tabs
		last_line   = line

	output += align_and_collect(left, right)

	if output.endswith('\n'):
		output = output[0:-1]

	return output


def tokenize(s):
	'''
	Input: a single line
	A token is a continuing block of code with no unquoted spaces
	'''
	tokens = []
	n = len(s)
	i = 0
	while i < n:
		# Skip spaces:
		while i < n and s[i] == ' ':
			i += 1

		start = i

		while i < n and s[i] != ' ':
			c = s[i]

			if c == "'" or c == '"':
				i += 1
				while i < n:
					if s[i] == '\\':
						i += 2
					elif s[i] == c:
						i += 1
						break
					else:
						i += 1
			elif c == '-' and s[i+1] == '-':
				# -- one line Lua comment
				i = n
			elif c == '/' and s[i+1] == '/':
				# // one line C++ comment
				i = n
			elif c == '#' and (s[i+1] == ' ' or len(tokens) == 0):
				# # one line Python comment
				# We only support these as the only token on a line, or with a space after.
				# Else we get confused by Lua # operator
				i = n
			else:
				i += 1

		tokens.append( s[start:i] )

	return tokens


def align_and_collect(left_in, right_in):
	'''
	'left_in' is indentation + already aligned text
	'right_in' is tokens

	This function will move one token from each line to the left, and call align on those lines
	'''
	assert( len(left_in) == len(right_in) )

	next_left   = []
	next_tokens = []
	next_right  = []

	output = ''

	for i,tokens in enumerate(right_in):
		if len(tokens) > 0:
			next_left.append( left_in[i] )
			next_tokens.append( tokens[0] )
			next_right.append( tokens[1:] )
		elif g_continuous:
			# No breaks!
			next_left.append( left_in[i] )
			next_tokens.append( None )
			next_right.append( [] )
		else:
			# Break on this line
			output += align(next_left, next_tokens, next_right)
			output += left_in[i] + '\n'
			next_left   = []
			next_tokens = []
			next_right  = []

	output += align(next_left, next_tokens, next_right)

	#spam("align_and_collect output: ", output)
	return output


RE_NUMBER = re.compile(r'^[+-]?\.?\d+.*$')  # any number followed by whatever (e.g. a comma)
RE_SIGN_OR_DIGIT = re.compile(r'^[\d+-]$')


def spaces(num):
	return num * ' '


def align(left, tokens, right):
	assert(len(left) == len(right) == len(tokens))
	n = len(left)
	if n == 0:
		return ''

	#######################################
	# Calculate target width:

	decimal_place         = [None] * n
	rightmost_decimal     = 0
	right_side_of_decimal = 0      # At most, how many characters right of a decimal point?
	align_width           = 0
	need_to_continue      = False

	for ix, token in enumerate(tokens):
		if token:
			need_to_continue = True
			more_to_come = (len(right[ix]) > 0)
			is_number = RE_NUMBER.match(token)

			if more_to_come or is_number:
				align_width = max(align_width, len(token) + 1)

			if is_number:
				decimal_place[ix] = 0
				for c in token:
					if RE_SIGN_OR_DIGIT.match(c):
						decimal_place[ix] += 1
					else:
						break
				spam("Number '%s' has decimal at %i" % (token, decimal_place[ix]))
				rightmost_decimal     = max(rightmost_decimal,     decimal_place[ix])
				right_side_of_decimal = max(right_side_of_decimal, 1 + len(token) - decimal_place[ix])

	align_width = max(align_width, rightmost_decimal + right_side_of_decimal)

	if not need_to_continue:
		return '\n'.join(left) + '\n'

	#######################################
	# Align tokens and move left:

	new_left = []

	for ix, token in enumerate(tokens):
		if token:
			if RE_NUMBER.match(token):
				# right-align:
				token = spaces(rightmost_decimal - decimal_place[ix]) + token

			more_to_come = (len(right[ix]) > 0)

			if more_to_come:
				token += spaces(align_width - len(token))

			new_left.append( left[ix] + token )
		else:
			new_left.append( left[ix] )

	return align_and_collect(new_left, right)


if __name__ == '__main__':
	# CLI
	import fileinput  # reads from stdin or from file given as argument
	import sys

	lines = []
	for line in fileinput.input():
		lines.append(line)

	aligned = alignify_lines(lines)
	#print( aligned )
	sys.stdout.write( aligned )  # no trailing newline


def module_exists(module_name):
	try:
		__import__(module_name)
	except ImportError:
		return False
	else:
		return True


if module_exists('sublime_plugin'):
	# ST3 plugin
	import sublime_plugin

	class AlignifyCommand(sublime_plugin.TextCommand):
		'''
		def __init__(self, view):
			super(AlignifyCommand, self).__init__(view)
		'''

		def run(self, edit):
			for region in self.view.sel():
				if not region.empty():
					region = self.view.line(region) # Extend selection to full lines
					s = self.view.substr(region)
					s = alignify_string(s)
					self.view.replace(edit, region, s)
