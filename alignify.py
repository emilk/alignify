#!/usr/bin/env python
# https://github.com/emilk/alignify
# By Emil Ernerfeldt 2013-2016
# LICENSE:
#   This software is dual-licensed to the public domain and under the following
#   license: you are granted a perpetual, irrevocable license to copy, modify,
#   publish, and distribute this file as you see fit.
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
# 3.0.1 - 2014-06-27  -  Disabled AST:ing of () and []
# 3.0.2 - 2014-06-27  -  Fixed issue with splitting }; into separate tokens
# 3.0.3 - 2014-06-27  -  Fixed issue with aligning to last token on a line
# 3.1   - 2014-07-03  -  {}-nodes now aligned together, then aligned with string-nodes
# 3.1.0 - 2015-04-28  -  Switched to semantic versioning
# 3.1.1 - 2016-09-24  -  Minor fix for misinterpreting --decrement for -- Lua comment.
# 3.1.2 - 2016-09-24  -  Comments always aligned together right-most.

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


RE_NUMBER        = re.compile(r'^[+-]?\.?\d+.*$') # any number followed by whatever (e.g. a comma)
RE_SIGN_OR_DIGIT = re.compile(r'^[\d+-]$')


# For debugging
def spam(*stuff):
	#print( 'SPAM: ' + ''.join(map(str,stuff)) )
	pass


def alignify_string(s):
	return alignify_lines(s.splitlines())


def alignify_lines(lines):
	# Split into blocks of same indentation:
	left        = []
	right       = []
	last_indent = None

	output = ""

	for ix, line in enumerate(lines):
		spam("line: '", line, "'")

		if g_ignore_empty_lines and line == '':
			left.append('')
			right.append('')
			continue

		if g_suffer_whitespace_indentation:
			# Try matching tabs first - if none, match spaces two and two
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

		left.append(indent)
		right.append(nodes)
		last_indent = indent

	output += align_and_collect(left, right)

	if output.endswith('\n'):
		output = output[0:-1]

	return output


def is_comment(s):
	if len(s) >= 2 and s[0] == '#' and s[1] == ' ':
		# # one line Python comment
		# We only support these with a space after, else we get confused by Lua # operator
		return True

	if len(s) >= 2 and s[0] == '/' and s[1] == '/':
		# // one line C++ comment
		return True

	if len(s) >= 3 and s[0] == '-' and s[1] == '-' and s[2] == ' ':
		# -- one line Lua comment
		# We only support these with a space after, or we get confused by --i; in C/C++
		return True

	return False



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

			elif is_comment(s[i:]):
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


def align_ast_lines(ast_lines):
	n = len(ast_lines)
	spam("align_ast_lines ", n, ": ", ast_lines)

	# Comments should always come last, like this:
	# 	foo bar
	# 	baz // comment
	# ->
	#   foo bar
	#   baz     // comment
	#
	comments = [None] * n
	for ix, right in enumerate(ast_lines):
		if len(right) > 0:
			last = right[-1]
			if isinstance(last, str) and is_comment(last):
				comments[ix] = last
				right.pop()

	result = [line.rstrip() for line in align_nodes(ast_lines)]

	if any(comments):
		widest = len(max(result, key=len))
		for ix, line in enumerate(result):
			if comments[ix]:
				pad_width = widest - len(line)
				if any(ast_lines):
					pad_width += 1
				result[ix] = line + spaces(pad_width) + comments[ix]

	return result


def concat_lines(left, right):
	assert(len(left) == len(right))
	return [l + r for l, r in zip (left, right)]


def align_and_collect(left_indentation, right_ast_in):
	assert(len(left_indentation) == len(right_ast_in))
	right_aligned = align_ast_lines(right_ast_in)
	result = concat_lines(left_indentation, right_aligned)
	return '\n'.join(result) + '\n'


def align_nodes(lines):
	if len(lines) == 0:
		return []

	spam("align_nodes ", len(lines), ": ", lines)

	# ----------------------------------------------------
	# Find list nodes and convert to strings:

	list_lines = []
	lists      = []

	for line_nr, nodes in enumerate(lines):
		if len(nodes) > 0 and type(nodes[0]) is list:
			list_lines.append(line_nr)
			lists.append(nodes[0])

	lists_as_strings = align_nodes(lists)

	# ----------------------------------------------------
	# Replace list nodes with their aligned tokens:

	for ix,line_nr in enumerate(list_lines):
		lines[line_nr][0] = lists_as_strings[ix]

	# ----------------------------------------------------

	token_lines  = []
	tokens       = []
	tokens_right = []

	for line_nr,nodes in enumerate(lines):
		if len(nodes) > 0:
			assert(type(nodes[0]) is str)
			token_lines.append(line_nr)
			tokens.append(nodes[0])
			tokens_right.append(nodes[1:])

	tokens_out_left  = align_tokens(tokens, tokens_right)
	tokens_out_right = align_nodes(tokens_right)

	# ----------------------------------------------------

	out_lines = [''] * len(lines)

	for ix,line_nr in enumerate(token_lines):
		out_lines[line_nr] = tokens_out_left[ix] + tokens_out_right[ix]

	spam("align_nodes: ", lines, " -> ", out_lines)
	return out_lines


def spaces(num):
	return num * ' '

# lines = list of single tokens == list of strings
def align_tokens(lines, right):
	n = len(lines)
	if n == 0:
		return []

	spam("align_tokens: ", len(lines))

	# -----------------------------------------------------------
	# Calculate target width:

	decimal_place         = [None] * n
	rightmost_decimal     = 0
	right_side_of_decimal = 0  # At most, how many characters right of a decimal point?
	align_width           = 0

	for ix, token in enumerate(lines):
		is_number = RE_NUMBER.match(token)
		more_to_come = (len(right[ix]) > 0)

		if more_to_come:
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

	spam("align_tokens: ", lines, " => ", aligned_lines)
	return aligned_lines


def print_help():
	print("alignify.py [file_name_1, ...],  or:  cat text | alignify.py")


def main():
	''' CLI. TODO: parse some flags? '''
	import fileinput  # reads from stdin or from file given as argument
	import sys

	lines = []
	for line in fileinput.input():
		lines.append(line)

	if len(lines) == 0:
		print_help()
	else:
		aligned = alignify_lines(lines)
		sys.stdout.write(aligned) # no trailing newline


if __name__ == '__main__':
	main()


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
		def run(self, edit):
			for region in self.view.sel():
				if not region.empty():
					region = self.view.line(region) # Extend selection to full lines
					original = self.view.substr(region)
					aligned = alignify_string(original)
					if aligned != original:
						self.view.replace(edit, region, aligned)
