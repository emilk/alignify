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
			1e32 |
			420e5 |
			-3e-12 |
		""", """
			  1e32  |
			420e5   |
			 -3e-12 |
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
			Map<String, Int> foo;
			int bar;
		""", """
			Map<String, Int> foo;
			int              bar;
		"""
	),
	(
		"""
			Map<String, Int> foo;
			int bar = 10;
		""", """
			Map<String, Int> foo;
			int              bar = 10;
		"""
	),
	(
		"""
			Map<String, Int> foo = 10;
			int bar;
		""", """
			Map<String, Int> foo = 10;
			int              bar;
		"""
	),
	(
		"""
			Map<String, Int> foo = 10;
			int bar = 10;
		""", """
			Map<String, Int> foo = 10;
			int              bar = 10;
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
			( first, second, third )
			( { a, b, c }, [ a, b, c ], { a, b, c } )
			( { foo, bar, baz }, [ short ], { a, b, c } )
		""", """
			( first,             second,      third       )
			( { a,   b,   c   }, [ a, b, c ], { a, b, c } )
			( { foo, bar, baz }, [ short   ], { a, b, c } )
		"""
	),
	(
		"""
			Matrix x = {
				{ 12, 0, 0, 0 },
				{ 0, 0.2, 0, 0 },
				{ 0, 0, 10, 0 },
				{ 0.3, 0, 0, -127 },
			}
		""", """
			Matrix x = {
				{ 12,   0,    0,    0 },
				{  0,   0.2,  0,    0 },
				{  0,   0,   10,    0 },
				{  0.3, 0,    0, -127 },
			}
		"""
	),
	(
		"""
			Matrix x = {
				{12, 0, 0, 0},
				{0, 0.2, 0, 0},
				{0, 0, 10, 0},
				{0.3, 0, 0, -127},
			}
		""", """
			Matrix x = {
				{12,   0,    0,    0},
				{ 0,   0.2,  0,    0},
				{ 0,   0,   10,    0},
				{ 0.3, 0,    0, -127},
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
			name: "grass" symmetry: "X"
			name: "grasscorner" symmetry: "L" weight: 0.0001
		""", """
			name: "grass"       symmetry: "X"
			name: "grasscorner" symmetry: "L" weight: 0.0001
		"""
	),
	(
		"""
			const std::string name = config["name"].as_string();
			const size_t out_width = config.get_or("width", 48);
		""", """
			const std::string name      = config["name"].as_string();
			const size_t      out_width = config.get_or("width", 48);
		"""
	),
	(
		"""
			{ name: "hole", n: 3, width: 64, height: 64, }
			{ name: "gradient", n: 3, width: 64, height: 64, symmetry: 2, foundation: true }
		""", """
			{ name: "hole",     n: 3, width: 64, height: 64,                               }
			{ name: "gradient", n: 3, width: 64, height: 64, symmetry: 2, foundation: true }
		"""
	),
	(
		"""
			{ name: "hole", n: 4, width: 32, height: 32 }
			{ name: "gradient", n: 3, symmetry: 2, width: 64, height: 64, foundation: true }
		""", """
			{ name: "hole",     n: 4,              width: 32, height: 32                   }
			{ name: "gradient", n: 3, symmetry: 2, width: 64, height: 64, foundation: true }
		"""
	),
	(
		"""
		{ "symmetry": 1 },
		{ "screenshots": 1, "width": 47 },
		""", """
		{ "symmetry":    1              },
		{ "screenshots": 1, "width": 47 },
		"""
	),
	(
		"""
			input_ir = readCvImage(ir_path, cv::IMREAD_GRAYSCALE);
			input_depth = readDepthCvImage(depth_path);
		""", """
			input_ir    = readCvImage(ir_path, cv::IMREAD_GRAYSCALE);
			input_depth = readDepthCvImage(depth_path);
		"""
	),
	(
		"""
			Texture::Texture(
				const void* data,
				Size size,
				ImageFormat format,
				const std::string& name);
		""", """
			Texture::Texture(
				const void*        data,
				Size               size,
				ImageFormat        format,
				const std::string& name);
		"""
	),
	(
		"""
			const cv::Mat1b& image,
			std::vector<std::vector<size_t>>& out_components);
		""", """
			const cv::Mat1b&                  image,
			std::vector<std::vector<size_t>>& out_components);
		"""
	),
	(
		"""
			const std::string& label,
			int height_in_items)
		""", """
			const std::string& label,
			int                height_in_items)
		"""
	),
	(
		"""
			vault::Client& io_vault_client,
			View& io_view,
			Memory& io_memory,
			const std::vector<View>& all_views)
		""", """
			vault::Client&           io_vault_client,
			View&                    io_view,
			Memory&                  io_memory,
			const std::vector<View>& all_views)
		"""
	),
	(
		"""
			CameraInterface& io_camera,
			scheduling::PoolScheduler& io_scheduler,
			const fs::path& output_dir,
			size_t num_frames,
			size_t num_skip_frames)
		""", """
			CameraInterface&           io_camera,
			scheduling::PoolScheduler& io_scheduler,
			const fs::path&            output_dir,
			size_t                     num_frames,
			size_t                     num_skip_frames)
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
