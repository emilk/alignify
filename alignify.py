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
# 4.0.0 - 2016-10-09  -  Parse spaces as tokens + smart matching of tokens
# 4.0.1 - 2016-10-18  -  Improve levenshtein distance

# -----------------------------------------------------------
# Algorithm overview:
#     Split each line into indentation and meat
#     Group lines based on indentation
#     For each group:
#         Parse the meat on each line into an list of AST Node:s
#         Remove trailing comments, and put them to the side.
#             Intelligently add dummy '' tokens to short lines, so all lines are equally long
#             For each column:
#                 If the column has any lines with {groups}, recurse on those and replace
#             For each column, for those lines that have non-empty token on that line:
#                 Look for decimal places, and align on that (if any)
#                 Pad so each token starts on the same column
#         Append any trailing comments
#

# -----------------------------------------------------------
# Global settings:

g_ignore_empty_lines = True
# Iff true, will continue aligning across empty lines.
# False is recommended for whole-file alignment(though that is recommended).

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

import copy
import re


# any number followed by whatever (e.g. a comma):
RE_NUMBER        = re.compile(r'^[+-]?\.?\d+.*$')
RE_SIGN_OR_DIGIT = re.compile(r'^[\d+-]$')
RE_DIGIT         = re.compile(r'\d')
RE_CHARACTER     = re.compile(r'[a-zA-Z_]')


# For debugging
def spam(*stuff):
	#print( 'SPAM: ' + ''.join(map(str,stuff)) )
	pass


# -----------------------------------------------------------
# Type checks for debugging/readability:


def assert_is_list_of_strings(x):
	assert isinstance(x, list) and all((isinstance(elem, str) for elem in x)), \
		"Expected List[str], got '{}'".format(x)


def assert_is_node(x):
	if not isinstance(x, str):
		assert isinstance(
			x, list), "Expected Node (str or list), got {}: {}".format(type(x), x)
		for elem in x:
			assert id(elem) != id(x), "Self-containing list: {}".format(x)
			assert_is_node(elem)


def assert_is_list_of_nodes(x):
	assert isinstance(
		x, list), "Expected List[Node], got {}: {}".format(type(x), x)
	for elem in x:
		assert_is_node(elem)


# -----------------------------------------------------------


def alignify_string(s):
	return alignify_lines(s.split('\n'))


def alignify_lines(lines):
	# Split into blocks of same indentation:
	block_indent = []
	block_meat   = []
	last_indent  = None

	output = ""

	for ix, line in enumerate(lines):
		spam("line: '", line, "'")

		if g_ignore_empty_lines and line == '':
			block_indent.append('')
			block_meat.append([''])
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

		# Replace non-leading tabs with spaces. Any number of spaces will work.
		meat = re.sub(r'\t', '  ', meat)
		nodes, _ = parse(meat)
		assert_is_list_of_nodes(nodes)

		if last_indent != None and indent != last_indent:
			# A change in indentation - align what we have so far:
			spam("alignify_lines: indentation break: '", indent, "'")
			output += align_and_collect(block_indent, block_meat)
			block_indent = []
			block_meat   = []

		block_indent.append(indent)
		block_meat.append(nodes)
		last_indent = indent

	output += align_and_collect(block_indent, block_meat)

	if output.endswith('\n'):
		output = output[0:-1]

	return output


def is_comment(s):
	if len(s) >= 2 and s[0] == '#' and s[1] == ' ':
		# # one line Python/bash comment
		# We only support these with a space after, else we get confused by Lua # operator
		return True

	if len(s) >= 2 and s[0] == '/' and s[1] == '/':
		# // one line C++ comment. Will get confused by Python3 // integer divide.
		return True

	if len(s) >= 3 and s[0] == '-' and s[1] == '-' and s[2] == ' ':
		# -- one line Lua comment
		# We only support these with a space after, or we get confused by --i; in C/C++
		return True

	return False


def parse(s, i = 0, until = None):
	'''
	Recursive decent - breaks at end or reaching when pushing a string node starting with character 'until'.
	Returns an AST. Each node is either a string or a list.
	Input: a single line
	A token is a continuing block of code with no unquoted spaces
	'''

	SPACE_BEFORE = ""
	SPACE_AFTER  = ""
	NESTINGS = {
		'{': '}',
		# '(': ')', # Will sometimes add spaces between ()
		# '[': ']', # Will split [i] which is ugly
		# '<': '>',
	}

	nodes = []
	n = len(s)

	while i < n:
		# Skip spaces:
		did_skip_spaces = False
		while i < n and s[i] == ' ':
			i += 1
			did_skip_spaces = True
		if did_skip_spaces:
			nodes.append(' ')

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
				# eg:  foo{
				opener = s[start:i+1]
				nested, i = parse(s, i+1, NESTINGS[c])
				nested.insert(0, opener)
				nodes.append(nested)
				start = i

			elif c in SPACE_BEFORE:
				if start != i:
					nodes.append(s[start:i])
					if nodes[-1][0] == until:
						return nodes, i
				start = i
				i += 1

			elif c in SPACE_AFTER:
				nodes.append(s[start:i+1])
				if nodes[-1][0] == until:
					return nodes, i
				i += 1
				start = i

			else:
				i += 1

		if start != i:
			nodes.append(s[start:i])
			if nodes[-1][0] == until:
				return nodes, i

	spam("parse: ", s, " -> ", nodes)

	return nodes, i


def concat_lines(left, right):
	assert len(left) == len(right)
	assert_is_list_of_strings(left)
	assert_is_list_of_strings(right)
	return [l + r for l, r in zip(left, right)]


def align_and_collect(left_indentation, ast_lines):
	assert len(left_indentation) == len(ast_lines)
	if len(left_indentation) == 0:
		return "\n"

	assert_is_list_of_strings(left_indentation)
	assert_is_list_of_nodes(ast_lines[0])
	comments = strip_comments(ast_lines)
	lines = align_ast_lines(ast_lines)
	lines = append_comments(lines, comments)
	results = concat_lines(left_indentation, lines)
	return "\n".join(results) + "\n"


def strip_comments(ast_lines):
	# Comments should always come last, like this:
	# 	foo bar
	# 	baz // comment
	# ->
	#   foo bar
	#   baz     // comment
	#
	comments = [None] * len(ast_lines)
	for line_nr, right in enumerate(ast_lines):
		if len(right) >= 2:
			last = right[-1]
			if isinstance(last, str) and is_comment(last):
				comments[line_nr] = last
				right.pop()

	return comments


def append_comments(lines, comments):
	assert_is_list_of_strings(lines)
	if any(comments):
		widest = 0
		for line_nr in range(len(lines)):
			if comments[line_nr]:
				widest = max(widest, len(lines[line_nr]))

		for line_nr in range(len(lines)):
			if comments[line_nr]:
				pad_width = widest - len(lines[line_nr])
				lines[line_nr] += spaces(pad_width) + comments[line_nr]

	return lines


def align_ast_lines(ast_lines):
	assert len(ast_lines) > 0
	assert_is_list_of_nodes(ast_lines[0])
	# print("ast_lines: {}".format(ast_lines))
	ast_lines = expand_short_lines(ast_lines)
	# print("expanded:  {}".format(ast_lines))
	ast_lines = unfold_list_nodes(ast_lines)
	# print("unfolded:  {}".format(ast_lines))
	assert_is_list_of_strings(ast_lines[0])
	aligned = align_columns(ast_lines)
	assert_is_list_of_strings(aligned)
	# print("aligned:   {}".format(aligned))
	return aligned


def unfold_list_nodes(in_ast_lines):
	num_lines = len(in_ast_lines)
	num_columns = len(in_ast_lines[0])

	out_ast_lines = copy.deepcopy(in_ast_lines)

	for column_idx in range(num_columns):
		# Find list nodes and convert to strings:
		line_numbers = []
		lists        = []

		for line_nr, line_nodes in enumerate(in_ast_lines):
			if type(line_nodes[column_idx]) is list:
				line_numbers.append(line_nr)
				lists.append(line_nodes[column_idx])

		if line_numbers:
			aligned_lists = align_ast_lines(lists)
			assert_is_list_of_strings(aligned_lists)

			for line_nr, aligned in zip(line_numbers, aligned_lists):
				out_ast_lines[line_nr][column_idx] = aligned

	return out_ast_lines


def align_columns(lines):
	assert len(lines) > 0
	assert_is_list_of_strings(lines[0])

	# print("align_columns: {}".format(lines))

	num_lines = len(lines)
	num_columns = len(lines[0])
	output = num_lines * ['']

	for column_idx in range(num_columns):
		# Find space tokens and append:
		for line_nr, line in enumerate(lines):
			if line[column_idx] == ' ':
				output[line_nr] += ' '
				line[column_idx] = ''

		# Find lines with non-empty tokens at this column:
		line_numbers = []
		tokens       = []
		for line_nr, line in enumerate(lines):
			assert isinstance(line[column_idx], str)
			if line[column_idx] != '':
				line_numbers.append(line_nr)
				tokens.append(line[column_idx])

		if tokens:
			aligned_column = align_tokens(tokens)
			assert_is_list_of_strings(aligned_column)

			max_width = 0
			for line_nr in line_numbers:
				max_width = max(max_width, len(output[line_nr]))

			for line_nr, aligned in zip(line_numbers, aligned_column):
				output[line_nr] += spaces(max_width - len(output[line_nr]))
				output[line_nr] += aligned

	return output


def collapse_list_nodes(ast_lines):
	# Find list nodes and convert to strings:

	list_lines = []
	lists      = []

	for line_nr, nodes in enumerate(ast_lines):
		if len(nodes) > 0 and type(nodes[0]) is list:
			list_lines.append(line_nr)
			lists.append(nodes[0])

	lists_as_strings = align_nodes(lists)

	# Replace list nodes with their aligned tokens:

	str_lines = copy.deepcopy(ast_lines)

	for ix, line_nr in enumerate(list_lines):
		str_lines[line_nr][0] = lists_as_strings[ix]

	return str_lines


def is_alpha_num(c):
	return re.match(RE_CHARACTER, c) or re.match(RE_DIGIT, c)


def is_operator_token(x):
	return len(x) == 1 and x != ' ' and not re.match(RE_DIGIT, x) and not re.match(RE_CHARACTER, x)


# -----------------------------------------------------------------------------
# levenshtein distance distance implementation

def substitution_cost_char(a, b):
	if a == b:
		return 0
	elif re.match(RE_CHARACTER, a):
		if re.match(RE_CHARACTER, b):
			if a.isupper() == b.isupper():
				return 1 # Same-case characters
			else:
				return 2 # Different-case character
		elif re.match(RE_DIGIT, b):
			return 3 # Character-Digit
		else:
			return 10 # Character-Symbol
	elif re.match(RE_DIGIT, a):
		if re.match(RE_DIGIT, b):
			return 1 # Digit-digit
		elif re.match(RE_CHARACTER, b):
			return 2 # Digit-Character
		else:
			return 10 # Digit-Symbol
	else:
		if re.match(RE_DIGIT, b):
			return 10 # Symbol-digit
		elif re.match(RE_CHARACTER, b):
			return 10 # Symbol-Character
		else:
			return 3 # Symbol-Symbol


def substitution_cost(s1, i1, s2, i2):
	# We care less about the last character, e.g. trailing comma
	is_last_char = i1 + 1 == len(s1) or i2 + 1 == len(s2)
	cost = substitution_cost_char(s1[i1], s2[i2])
	if is_last_char:
		return min(cost, 1)
	else:
		return cost


def add_del_cost(s, i):
	if i + 1 == len(s):
		return 1 # We care less about the last character, e.g. trailing comma
	c = s[i]
	if re.match(RE_CHARACTER, c) or re.match(RE_DIGIT, c):
		return 1
	else:
		return 10


def levenshtein_distance(s1, s2):
	if len(s1) < len(s2):
		return levenshtein_distance(s2, s1)

	previous_row = [0]
	for i2 in range(len(s2)):
		previous_row.append(previous_row[-1] + add_del_cost(s2, i2))

	for i1, c1 in enumerate(s1):
		current_row = [previous_row[0] + add_del_cost(s1, i1)]
		for i2, c2 in enumerate(s2):
			addcost = previous_row[i2 + 1] + add_del_cost(s1, i1)
			delcost = current_row[i2] + add_del_cost(s2, i2)
			subcost = previous_row[i2] + substitution_cost(s1, i1, s2, i2)
			# print("'{}' '{}' add: {}, del: {}, sub: {}".format(c1, c2, addcost, delcost, subcost))
			current_row.append(min(addcost, delcost, subcost))
		# print("previous_row: {}".format(previous_row))
		# print("current_row:  {}".format(current_row))
		previous_row = current_row
	return previous_row[-1]


# -----------------------------------------------------------------------------


def character_similarity(a, b):
	return 10 - substitution_cost_char(a, b)


def token_similarity(a, b):
	assert isinstance(a, str)
	assert isinstance(b, str)

	# print("token_similarity '{}' vs '{}'".format(a, b))

	# Special case to prevent this:
	#     string mushroom = badger;
	#     int               snake;
	# And this:
	#     print a + b;
	#     print     c;
	if a != b and (is_operator_token(a) or is_operator_token(b)):
		return -1000

	if a == '' or b == '':
		return 0

	# if a == b:
	# 	return 10000

	similarity = 0

	# Similarity in the first character weighs more heavily than other characters
	similarity += 100 * character_similarity(a[0], b[0])

	# Check last character? The problem then is that we want
	#    x, y
	#    z
	# NOT:
	#    x, y
	#       z
	# However, we do want:
	#    int       x;
	#    map<a, b> y;
	# But not:
	#    print a + b;
	#    print     c;
	# Solution: only give points if the last character is special and a MATCH
	# if a[-1] == b[-1] and not is_alpha_num(a[-1]):
	# 	similarity += 200

	# Take word similarity into account:
	similarity -= 10 * levenshtein_distance(a, b);

	# Use token length as a tie-breaker:
	# similarity -= abs(len(a) - len(b))

	return similarity


def collapse_node(node):
	if isinstance(node, str):
		return node
	else:
		return " ".join((collapse_node(child) for child in node))


def node_similarity(a, b):
	assert_is_node(a)
	assert_is_node(b)
	return token_similarity(collapse_node(a), collapse_node(b))


def calc_similarity(line_a, line_b):
	similarity = 0
	for a, b in zip(line_a, line_b):
		similarity += node_similarity(a, b)
	return similarity


# Add phantom tokens to "short_line"
def expand_short_line(long_line, short_line):
	assert_is_list_of_nodes(long_line)
	assert_is_list_of_nodes(short_line)

	if len(short_line) >= len(long_line):
		return short_line

	if len(short_line) <= 1:
		return short_line

	return [short_line[0]] + expand_line_ending(long_line[1:], short_line[1:])


def dynamic_similarity(context, a, b):
	long_line  = context["long_line"]
	short_line = context["short_line"]
	similarity = context["similarity"]

	if a == len(long_line) or b == len(short_line):
		# print("We should insert at {}/{}".format(a,b))
		return (0, False)

	left_of_long  = len(long_line)  - a
	left_of_short = len(short_line) - b
	assert left_of_long >= left_of_short

	if similarity[a][b] is None:
		match_similarity  = node_similarity(long_line[a], short_line[b]) + dynamic_similarity(context, a + 1, b + 1)[0]

		if left_of_long <= left_of_short:
			# print("We should match at {}/{}".format(a,b))
			similarity[a][b] = (match_similarity, True)
			assert similarity[a][b][1]
		else:
			insert_similarity = node_similarity(long_line[a], '')            + dynamic_similarity(context, a + 1, b + 0)[0]
			insert_similarity -= 1 # Small penalty for inserts

			if match_similarity >= insert_similarity:
				# print("We should match at {}/{}".format(a,b))
				similarity[a][b] = (match_similarity, True)
				assert similarity[a][b][1]
			else:
				# print("We should insert at {}/{}".format(a,b))
				similarity[a][b] = (insert_similarity, False)

	should_match = similarity[a][b][1]
	if not should_match:
		assert left_of_long > left_of_short

	return similarity[a][b]


def expand_line_ending(long_line, short_line):
	# We want to insert '' tokens into short_line in places so as to
	# maximize its similarity to long_line, as defined by calc_similarity.
	# This is a dynamic programming problem. Let's make a NxN table
	# where N = len(long_line).
	# similarity[a][b] is the best achievable similarity of long_line[a:] and short_line[b:],
	# assuming we can insert more empty tokens after point 'b'
	# We can fill this in dynamically (memoization style)

	N = len(long_line)

	similarity = [[None for x in range(N)] for y in range(N)]
	assert id(similarity[0]) != id(similarity[1])

	context = {
		"long_line":  long_line,
		"short_line": short_line,
		"similarity": similarity,
	}

	# print("long line:  {}".format(long_line))
	# print("short line: {}".format(short_line))

	result_line = []
	a = 0
	b = 0
	while len(result_line) < len(long_line):
		# print("a/b: {}/{}".format(a,b))
		_, match = dynamic_similarity(context, a, b)

		left_of_long  = len(long_line)  - a
		left_of_short = len(short_line) - b
		assert left_of_long >= left_of_short

		if match:
			# print("Matching '{}'".format(short_line[b]))
			result_line.append(short_line[b])
			a += 1
			b += 1
		else:
			assert left_of_long > left_of_short
			# print("Inserting")
			result_line.append('')
			a += 1

	# print("similarity: {}".format(context["similarity"]))
	# print("long_line: {}".format(long_line))
	# print("result_line: {}".format(result_line))

	assert len(result_line) == len(long_line)

	return result_line


# Find short lines and add "phantom tokens" (empty string) in strategic places
# This will ensure this alignment:
	# map<x, y> foo;
	# int       bar;
# By inserting a phantom token between "int" and "bar" to align with "y>"
# This function returns equally long lines (measured in Ast Ndoes)
def expand_short_lines(in_lines):
	assert isinstance(in_lines, list)
	assert_is_list_of_nodes(in_lines[0])

	longest_line = max(in_lines, key=len)

	expanded = []
	for line in in_lines:
		expanded_line = expand_short_line(longest_line, line)
		while len(expanded_line) < len(longest_line):
			expanded_line.append('')
		expanded.append(expanded_line)
	return expanded


def spaces(num):
	return num * ' '


def align_tokens(tokens):
	n = len(tokens)
	if n == 0:
		return []

	assert_is_list_of_strings(tokens)
	spam("align_tokens: ", len(tokens))

	# -----------------------------------------------------------
	# Calculate target width:

	decimal_place         = [None] * n
	rightmost_decimal     = 0
	# right_side_of_decimal = 0  # At most, how many characters right of a decimal point?
	# align_width           = 0

	for ix, token in enumerate(tokens):
		is_number = RE_NUMBER.match(token)

		if is_number:
			decimal_place[ix] = 0
			for c in token:
				if RE_SIGN_OR_DIGIT.match(c):
					decimal_place[ix] += 1
				else:
					break
			spam("Number '%s' has decimal at %i" % (token, decimal_place[ix]))
			rightmost_decimal     = max(rightmost_decimal,     decimal_place[ix])
			# right_side_of_decimal = max(right_side_of_decimal, len(token) - decimal_place[ix])

	# align_width = max(align_width, rightmost_decimal + right_side_of_decimal)

	# -----------------------------------------------------------
	# Do the actual aligning:

	aligned_lines = []

	for ix, token in enumerate(tokens):
		aligned_token = ''

		if decimal_place[ix] != None:
			# right-align number:
			aligned_token += spaces(rightmost_decimal - decimal_place[ix])

		aligned_token += token
		# aligned_token += spaces(align_width - len(aligned_token))
		aligned_lines.append(aligned_token)

	spam("align_tokens: ", tokens, " => ", aligned_lines)
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
		sys.stdout.write(aligned)  # no trailing newline


if __name__ == '__main__':
	main()

	# def lev_test(a, b):
	# 	print('"{}" - "{}": {}'.format(a, b, levenshtein_distance(a, b)))
	# lev_test("foo", "bar")
	# lev_test("foo", "ba")
	# lev_test("f!", "f")
	# lev_test("fo", "f!")
	# lev_test("f!", "fo")
	# lev_test("height_in_items", "label,")
	# lev_test("height_in_items", "std::string&")
	# lev_test("foo", "a,")
	# lev_test("foo", "c")
	# lev_test("A!", "a")


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
					# Extend selection to full lines:
					region = self.view.line(region)
					original = self.view.substr(region)
					aligned = alignify_string(original)
					if aligned != original:
						self.view.replace(edit, region, aligned)
