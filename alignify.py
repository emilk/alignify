#!/usr/bin/python
# 
# Last edited 2013-08-23
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


import re  # reg-ex


# For debugging
def spam(*stuff):
	#print( 'SPAM: ' + ''.join(map(str,stuff)) )
	pass


def alignify_string(s):
	lines = s.split('\n')
	return alignify_lines( lines )


def alignify_lines(lines):
	# Split into blocks of same indentation:
	beg = []
	tokens = []
	last_indent = ''

	output = ""

	for ix, line in enumerate(lines):
		spam("line: '", line, "'")

		m    = re.match("(\t*)(.*)", line)
		tabs = m.group(1)
		meat = m.group(2)

		spam("tabs: '", tabs, "'")
		spam("meat: '", meat, "'")

		# Replace non-leading tabs with spaces. Any number of spaces will work.
		meat = re.sub(r'\t', '  ', meat)

		if len(beg) > 0 and tabs != last_indent:
			# A change in indentation - new block
			output += alignify_beg_end(beg, tokens)
			beg    =  []
			tokens =  []

		beg.append( tabs )
		tokens.append( tokenize(meat) )
		last_indent = tabs

	output += alignify_beg_end(beg, tokens)

	if len(output) > 0 and output[-1] == '\n':
		output = output[0:-1]

	return output


def tokenize(s):
	'''
	A token is a continuing block of code with no quoted spaces
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
						u += 1
			elif c == '-' and s[i+1] == '-':
				# -- one line Lua comment
				i = n
			elif c == '/' and s[i+1] == '/':
				# // one line C++ comment
				i = n
			else:
				i += 1

		tokens.append( s[start:i] )

	return tokens


def alignify_beg_end(indents, lines):
	'''
	Takes a bunch of lines all with the same indentation.
	Each line is tokenized.
	'''
	assert( len(indents) == len(lines) )
	
	if len(lines) == 0:
		return ''

	spam("alignify_beg_end: ", len(lines))

	begs   = []
	firsts = []
	ends   = []

	output = ''

	for i,line in enumerate(lines):
		if len(line) == 0:
			output += align(begs, firsts, ends)
			output += indents[i] + '\n'
			begs   = []
			firsts = []
			ends   = []
		elif len(line) == 1:
			output += align(begs, firsts, ends)
			output += indents[i] + line[0] + '\n'
			begs   = []
			firsts = []
			ends   = []
		else:
			begs.append( indents[i] )
			firsts.append( line[0] )
			ends.append( line[1:] )

	output += align(begs, firsts, ends)

	spam("alignify_beg_end output: ", output)
	return output


def align(begs, tokens, ends):
	assert(len(begs) == len(tokens))
	assert(len(begs) == len(ends))
	if len(begs) == 0:
		return ''

	spam("align: ", len(tokens))
	widest = 0
	for _,t in enumerate(tokens):
		widest = max(widest, len(t))

	# Append padded tokens onto 'begs' to produce 'new_begs':
	new_begs   = []
	
	for ix, beg in enumerate(begs):
		token = tokens[ix]
		while len(token) < widest + 1:
			token += ' '
		new_begs.append(begs[ix] + token)

	spam('new_begs: ', new_begs)
	
	return alignify_beg_end(new_begs, ends)


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
					s = self.view.substr(region)
					s = alignify_string(s)
					self.view.replace(edit, region, s)  












# --------------------------------------
# Debug code:




#tokens = tokenize("if s = 'a string' -- comment")
#spam(tokens)

if False:
	examples = [
	'''
// Madonna has two trailing spaces:
First name  Last name
John  Lennon
Madonna  
Marilyn  Monroe
	'''

	'''
		a b c
		aa bb cc
	''',

	'''
		void fun(int x, float baz)
		{
			int foo = 1;  // Some description
			string sausage = "a test string";  // Bla bla bla
			int bar = 1;	// Some comment
			float z = 1.0f;
		}
	''',

	'''
		output += alignify_beg_end(beg, tokens)
		beg = []
		tokens = []
	'''
	]


	for _,s in enumerate(examples):
		print( '--------------------------------' )
		print( 'EXAMPLE INPUT:' )
		print( s )
		print( '--------------------------------' )
		aligned = alignify_string(s)
		print( '--------------------------------' )
		print( 'EXAMPLE OUTPUT:' )
		print( aligned )
		print( '--------------------------------' )
		print( '\n\n' )
		break