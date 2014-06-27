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
# 2.0   - 2013-08-23
# 2.1   - 2013-10-20  -  Aligns numbers by decimal point
# 2.1.1 - 2013-10-21  -  Fixes for number alignment and g_continuous == False
# 2.1.2 - 2013-10-22  -  Fixed tokenizer bug
# 2.2   - 2013-10-22  -  Whitespace indentation compatibility
# 2.2.1 - 2013-10-25  -  Fixed issue with failure to detect indentation change
# 2.3   - 2013-10-28  -  Forced spacing after ({, and before )}
# 2.3.1 - 2013-12-12  -  Fixed issue with some # detected as python comments when they where not
# 3.0   - 2014-06-26  -  Proper AST parsing for handling ({[]})-scopes separately
# 3.01  - 2014-06-27  -  Disabled AST:ing of () and []
# 3.02  - 2014-06-27  -  Fixed issue with splitting }; into separate tokens


# -----------------------------------------------------------
# Global settings:

g_ignore_empty_lines = True
# Iff true, will continue aligning across empty lines.
# False is recommended for whole-file alignment (though that is not recommended per se).

g_continuous = True
'''
Iff true, will align 'foo' and 'bar' in:

one foo
two
three bar
'''

g_suffer_whitespace_indentation = True
'''
Allow whitespace indentation? The indentation width will be assumed to be an even number.
Even if you turn this on you can use alignify on code indented with tabs.

If true, algignify can be made to work with code that indents code using spaces.
Of course, you should never do such a thing. Spaces, as the name implies, is for spacing - not for indentation.
The only way to reliably tell indentation fro alignment is if one uses different characters for the two - hence the dogma:

	Indent with tabs, align with spaces  -  http://vim.wikia.com/wiki/Indent_with_tabs,_align_with_spaces

Still - sometimes you are forces to work on a project that uses the wrong indentation style.
You should of course conform to the coding guidelines, and hence, alignify has a compatibility mode.

Since space-indentation comes with an inherent ambiguity between what's indentation and what's alignment.
Enabling the compatibility mode may keep alignify from correctly aligning things like:

rgb = [
    255,
    50,
        0,
]

Of course, the ambiguity disappears with correctly indented code:

rgb = [
	255,
	50,
	    0,
]

which is correctly aligned as:

rgb = [
	255,
	 50,
	  0,
]

'''

# -----------------------------------------------------------
# Actual code time!

import re  # Our one dependency - regular expressions


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

	output = ""

	for ix, line in enumerate(lines):
		spam("line: '", line, "'")

		if g_ignore_empty_lines and line == '':
			left.append( '' )
			right.append( '' )
			continue

		if g_suffer_whitespace_indentation:
			# Try mathcing tabs first - if none, match spaces two and two
			m      = re.match("(\t+|(  )*)(.*)", line)
			indent = m.group(1)
			meat   = m.group(3)
		else:
			m      = re.match("(\t*)(.*)", line)
			indent = m.group(1)
			meat   = m.group(2)

		#spam("indent: '", indent, "'")
		#spam("meat:  '", meat, "'")

		# Replace non-leading tabs with spaces. Any number of spaces will work.
		meat = re.sub(r'\t', '  ', meat)
		nodes, _ = parse(meat)
		assert(type(nodes) is list)

		if last_indent != None and indent != last_indent:
			# A change in indentation - align what we have so far:
			spam("alignify_lines: indentation break: '", indent, "'")
			output += align_and_collect(left, right)
			left  = []
			right = []

		left.append( indent )
		right.append( nodes )
		last_indent = indent

	output += align_and_collect(left, right)

	if output.endswith('\n'):
		output = output[0:-1]

	return output


# Recursive decent - breaks at end or reaching when pushing a string node starting with character 'until'.
# Returns an AST. Each node is either a string or a list.
def parse(s, i = 0, until = None):
	'''
	Input: a single line
	A token is a continuing block of code with no unquoted spaces
	'''

	SPACE_BEFORE = "}"
	SPACE_AFTER  = "{,"
	NESTINGS = {
		'{': '}',
		#'(': ')',
		#'[': ']',
	}

	nodes = []
	n = len(s)

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
			elif i+1 < n and c == '-' and s[i+1] == '-':
				# -- one line Lua comment
				i = n
			elif i+1 < n and c == '/' and s[i+1] == '/':
				# // one line C++ comment
				i = n
			elif i+1 < n and c == '#' and s[i+1] == ' ':
				# # one line Python comment
				# We only support these with a space after.
				# Else we get confused by Lua # operator
				i = n
			elif c in NESTINGS:
				# eg:  foo(
				opener = s[start:i+1]
				nested, i = parse(s, i+1, NESTINGS[c])
				nested.insert( 0, opener )
				nodes.append( nested )
				i += 1
				start = i

			elif c in SPACE_BEFORE:
				if start != i:
					nodes.append( s[start:i] )
					if nodes[-1][0] == until:
						return nodes,i
				start = i
				i += 1
			elif c in SPACE_AFTER:
				nodes.append( s[start:i+1] )
				if nodes[-1][0] == until:
					return nodes,i
				i += 1
				start = i
			else:
				i += 1

		if start != i:
			nodes.append( s[start:i] )
			if nodes[-1][0] == until:
				return nodes,i

	spam("parse: ", s, " -> ", nodes)

	return nodes, i


def align_and_collect(left_in, right_in):
	assert(len(left_in) == len(right_in))
	n = len(left_in)
	spam("align_and_collect ", n, ": ", right_in)

	right_out = align_nodes(right_in)
	out = [None] * n
	for ix, line in enumerate(right_out):
		out[ix] = left_in[ix] + right_out[ix].rstrip()
	return '\n'.join(out) + '\n'


def align_nodes(lines):
	if len(lines) == 0:
		return []

	spam("align_nodes ", len(lines), ": ", lines)

	string_lines  = []
	strings       = []
	strings_right = []

	list_lines    = []
	lists         = []
	lists_right   = []

	empty_lines   = []

	for line_nr,nodes in enumerate(lines):
		if len(nodes) > 0:
			first = nodes[0]
			if type(first) is str:
				string_lines.append(line_nr)
				strings.append(first)
				strings_right.append(nodes[1:])
			else:
				assert(type(first) is list)
				list_lines.append(line_nr)
				lists.append(first)
				lists_right.append(nodes[1:])
		else:
			# A break - ignore it
			empty_lines.append(line_nr)

	spam("aling_strings( strings       )")
	strings_out_left  = aling_strings( strings       )
	spam("align_nodes(   strings_right )")
	strings_out_right = align_nodes(   strings_right )
	spam("align_nodes(   lists         )")
	lists_out_left    = align_nodes(   lists         )
	spam("align_nodes(   lists_right   )")
	lists_out_right   = align_nodes(   lists_right   )

	out_lines = [''] * len(lines)

	for ix,line_nr in enumerate(string_lines):
		out_lines[line_nr] = strings_out_left[ix] + strings_out_right[ix]
	for ix,line_nr in enumerate(list_lines):
		out_lines[line_nr] = lists_out_left[ix] + lists_out_right[ix]

	spam("align_nodes: ", lines, " -> ", out_lines)
	return out_lines


RE_NUMBER        = re.compile( r'^[+-]?\.?\d+.*$' ) # any number followed by whatever (e.g. a comma)
RE_SIGN_OR_DIGIT = re.compile( r'^[\d+-]$'        )


def spaces(num):
	return num * ' '

# lines = list of single tokens == list of stirngs
def aling_strings(lines):
	n = len(lines)
	if n == 0:
		return []

	spam("aling_strings: ", len(lines))

	# -----------------------------------------------------------
	# Calculate target width:

	decimal_place         = [None] * n
	rightmost_decimal     = 0
	right_side_of_decimal = 0  # At most, how many characters right of a decimal point?
	align_width           = 0

	for ix, token in enumerate(lines):
		is_number = RE_NUMBER.match(token)

		align_width = max(align_width, len(token))

		if is_number:
			decimal_place[ix] = 0
			for c in token:
				if RE_SIGN_OR_DIGIT.match(c):
					decimal_place[ix] += 1
				else:
					break
			spam("Number '%s' has decimal at %i" % (token, decimal_place[ix]))
			rightmost_decimal     = max(rightmost_decimal,     decimal_place[ix])
			right_side_of_decimal = max(right_side_of_decimal, len(token) - decimal_place[ix])

	spam("align_width: ", align_width)
	spam("rightmost_decimal: ", rightmost_decimal)
	spam("right_side_of_decimal: ", right_side_of_decimal)
	align_width = max(align_width, rightmost_decimal + right_side_of_decimal)

	# -----------------------------------------------------------
	# Do the actual aligning:

	aligned_lines = []

	for ix, token in enumerate(lines):
		if decimal_place[ix] != None:
			# right-align number:
			token = spaces(rightmost_decimal - decimal_place[ix]) + token

		token += spaces(1 + align_width - len(token)) # +1: we want at least one!
		aligned_lines.append( token )

	spam("aling_strings: ", lines, " => ", aligned_lines)
	return aligned_lines


def print_help():
	print( "alignify.py [-t N] [file_name_1, ...]" )


def main(argv):
	'''
	CLI

	TODO:
	try:
		getopt.getopt(argv, "ht:", ["help"])
	except getopt.GetoptError:
		print_help()
		sys.exit(2)
	for opt, arg in opts:
		if opt in ("-h", "--help"):
			print_help()
			sys.exit()
		elif opt in ("-t"):
			g_num_tabs = arg
	'''
	import fileinput  # reads from stdin or from file given as argument

	lines = []
	for line in fileinput.input():
		lines.append(line)

	aligned = alignify_lines(lines)
	#print( aligned )
	sys.stdout.write( aligned )  # no trailing newline


if __name__ == '__main__':
	import sys
	main(sys.argv[1:])  # Skip 'alignify.py' in argv


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
					original = self.view.substr(region)
					aligned = alignify_string(original)
					if aligned != original:
						self.view.replace(edit, region, aligned)
