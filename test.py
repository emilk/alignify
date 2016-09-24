#!/usr/bin/env python
import alignify

TESTS = [
	(
		"""
			Use this as a template
		""", """
			Use this as a template
		"""
	),
	(
		"""
			one foo
			two
			three bar
		""", """
			one   foo
			two
			three bar
		"""
	),
	(
		"""
			int one = 1; // Duh
			float pi = 3;   // Close enough.
			string h2g2 = 42; // ...
		""", """
			int    one  =  1; // Duh
			float  pi   =  3; // Close enough.
			string h2g2 = 42; // ...
		"""
	),
	(
		"""
			red = { 255, 0, 0 }
			green = { 0, 255, 0 }
			blue = { 0, 0, 255 }
		""", """
			red   = { 255,   0,   0 }
			green = {   0, 255,   0 }
			blue  = {   0,   0, 255 }
		"""
	),
	(
		"""
			123 |
			23.45 |
			1 |
			1.2 |
			.1337       |
		""", """
			123      |
			 23.45   |
			  1      |
			  1.2    |
			   .1337 |
		"""
	),
	(
		"""
			a b
			a_very_long_thing
			short thing
		""", """
			a     b
			a_very_long_thing
			short thing
		"""
	),
	(
		"""
			C++ // C++ comment
			Python # Bash/Python comment
			Lua -- lua comment
			--i; // C++ statement
		""", """
			C++    // C++ comment
			Python # Bash/Python comment
			Lua    -- lua comment
			--i;   // C++ statement
		"""
	),
	(
		"""
			int x; // Some comment
			float y = 32; // Another comment
		""", """
			int   x;      // Some comment
			float y = 32; // Another comment
		"""
	),
	(
		"""
			short(); // One-line comments should come after everything else
			some = very.long(line);
		""", """
			short();                // One-line comments should come after everything else
			some = very.long(line);
		"""
	),
	(
		"""
			// Only a comment
		""", """
			// Only a comment
		"""
	),
	(
		"""
			int x;
			map<a, b> y;
			map<int, string> z;
		""", """
			int              x;
			map<a,   b>      y;
			map<int, string> z;
		"""
	),
]

def main():
	failures = 0

	for before, expected in TESTS:
		expected = expected.strip('\n')
		actual = alignify.alignify_string(before).strip('\n')
		if actual != expected:
			print("\nFAILURE!\nInput:\n{}\nExpected:\n{}\nGot:\n{}\n\n".format(before, expected, actual))
			failures += 1


	if failures == 0:
		print("All {} tests passed".format(len(TESTS)))
	else:
		print("{}/{} tests failed".format(failures, len(TESTS)))




if __name__ == '__main__':
	main()
