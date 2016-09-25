#!/usr/bin/env python
import alignify

TESTS = [
	(
		"",
		""
	),
	(
		"hello   world       !",
		"hello world !"
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
			// Comment
			a = b;
		""", """
			// Comment
			a = b;
		"""
	),
	(
		"""
			// Comment
			a = b; // Also a comment
		""", """
			// Comment
			a = b; // Also a comment
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
	(
		"""
			map<shared_ptr<Foo>, string> foo;
			map<double, int> bar;
			map<unsigned, string> baz;
			vector<string> badger;
		""", """
			map<shared_ptr<Foo>, string> foo;
			map<double,          int>    bar;
			map<unsigned,        string> baz;
			vector<string>               badger;
		"""
	),
	(
		"""
			std::map<std::string, unsigned> foo;
			std::vector<std::string> bar;
		""", """
			std::map<std::string, unsigned> foo;
			std::vector<std::string>        bar;
		"""
	),
	(
		"""
			std::map<std::string, unsigned> foo = 0;
			int bar = 0;
		""", """
			std::map<std::string, unsigned> foo = 0;
			int                             bar = 0;
		"""
	),
	(
		"""
			std::map<std::string, unsigned> foo = 0;
			int bar;
		""", """
			std::map<std::string, unsigned> foo = 0;
			int                             bar;
		"""
	),
	(
		"""
			std::map<std::string, unsigned> foo;
			int bar = 0;
		""", """
			std::map<std::string, unsigned> foo;
			int                             bar = 0;
		"""
	),
	(
		"""
			int x = 2;
			int baz = 30;
			int foobar;
		""", """
			int x   =  2;
			int baz = 30;
			int foobar;
		"""
	),
	(
		"""
			( foo )
			( { a } )
		""", """
			( foo   )
			( { a } )
		"""
	),
	(
		"""
			( foo, bar, foobar, badger, mushroom, snake )
			( { a, b, c }, { a, b, c }, { a, b, c }, { a, b, c }, { a, b, c }, { a, b, c } )
			( { foo, bar, baz }, { short }, { a, b, c }, { a, b, c }, { a, b, c }, { a, b, c } )
		""", """
			( foo,               bar,         foobar,      badger,      mushroom,    snake       )
			( { a,   b,   c   }, { a, b, c }, { a, b, c }, { a, b, c }, { a, b, c }, { a, b, c } )
			( { foo, bar, baz }, { short   }, { a, b, c }, { a, b, c }, { a, b, c }, { a, b, c } )
		"""
	),
	(
		"""
			Matrix x = {
				{ 12, 0, 0, 0 },
				{ 0, 0.2, 0, 0 },
				{ 0, 0, -10, 0 },
				{ 0.3, 0, 0, 46 },
			}
		""", """
			Matrix x = {
				{ 12,   0,     0,  0 },
				{  0,   0.2,   0,  0 },
				{  0,   0,   -10,  0 },
				{  0.3, 0,     0, 46 },
			}
		"""
	),
	(
		"""
			Matrix x = {
				{12, 0, 0, 0},
				{0, 0.2, 0, 0},
				{0, 0, -10, 0},
				{0.3, 0, 0, 46},
			}
		""", """
			Matrix x = {
				{12,   0,     0,  0},
				{ 0,   0.2,   0,  0},
				{ 0,   0,   -10,  0},
				{ 0.3, 0,     0, 46},
			}
		"""
	),
	(
		"""
			{ foo }
			{ a, b, c }
		""", """
			{ foo     }
			{ a, b, c }
		"""
	),
	(
		"""
			foo |
			a, b, c |
		""", """
			foo     |
			a, b, c |
		"""
	),
	(
		"""
			string mushroom = badger;
			int snake;
		""", """
			string mushroom = badger;
			int    snake;
		"""
	),
	(
		"""
			print a + b;
			println c;
		""", """
			print   a + b;
			println c;
		"""
	),
	(
		"""
			Map<String, Int> foo;
			bool bar = 10;
		""", """
			Map<String, Int> foo;
			bool             bar = 10;
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
