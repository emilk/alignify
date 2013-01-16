# Alignify

This perl script is designed to take a peice of code and find and align blocks in that code.
The idea for this comes from Nick Gravgaard's Elastic Tabstops ( http://nickgravgaard.com/elastictabstops/ )
What does that mean? It means it will take code like this:

	void fun(  int  x,
	   float  baz )
	{
		int  foo  =  1;  // Some description
		string  sausage  =  "a test string";  // Bla bla bla
		int  bar  =  1;  // Some comment
		float  z  =  1.0f;
	}

And output:

	void fun(  int    x,
	           float  baz )
	{
		int     foo      =  1;                // Some description
		string  sausage  =  "a test string";  // Bla bla bla
		int     bar      =  1;                // Some comment
		float   x        =  1.0f;
	}


## Key points:
* Alignify will align code blocks using spaces
* Alignify will keep indentation intact
* The output can be re-alignified (eg. to re-align after a change)
* To signal a code block break to Alignify, use a tab or at least two spaces
* Alignify is meant to be run on snippets of code, not entire source files (at least not yet)
* Alignify is agnostic to what it formats (ie. what programming language the input is written in)
* The horizontal offset of a code block is controlled by the longest prefix (excluding spaces) plus the number of spaces that follows that.


## Caveats
* Code must be indented with tabs (if at all). Why? If the code is indented with tabs, Alignify can easily keep idnentation intact, and align lines that start with spaces. However, if you indent your code with spaces there are many reasons to stop, and there is one more: there is no sure-fire way for Alignify to distinguish between indentation and intent for align, eg:

	if foo  &&  bar:
	    align this line or not? 
	    
## Tips and tricks:
* To keep a code block "alive", append two empty spaces on a row ("Madonna  ")

		First name  Last name
		Marilyn  Monroe
		Madonna  
		John  Lennon	
		
		  ->
		
		First name  Last name
		Marilyn     Monroe
		Madonna     
		John        Lennon


## TODO:
### Smart-align
Handle empy spaces by matching code blocks to its closest neighbor:

		foo      bar   baz
		foobar           raboof
		badger  snake   mushroom
		
		  ->
		
		foo     bar     baz
		foobar          raboof
		badger  snake   mushroom

### Support for indentation with spaces
Even though indenting code with spaces is stupid (see Caveats), Alignify should support it to the point where it can detect it and ignore it, so that if every line starts with a space, then all leading spaces are kept.

## APPROACH
* Replace any non-leading tabs with 2 spaces
* Break into segments based indentation. For each segment:
* Break lines into parts
* Align parts
