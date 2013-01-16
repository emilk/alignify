# Alignify

## What
Alignify is a python script is designed to take a peice of code and align 'blocks' in that code. An example input is

	void fun(  int  x,
	   float  baz )
	{
		int  foo  =  1;  // Some description
		string  sausage  =  "a test string";  // Bla bla bla
		int  bar  =  1;	// Some comment
		float  z  =  1.0f;
	}

And output:

	void fun(  int    x,
	           float  baz )
	{
		int     foo      =  1;                // Some description
		string  sausage  =  "a test string";  // Bla bla bla
		int     bar      =  1;                // Some comment
		float   z        =  1.0f;
	}

For a more extensive example, see test_input.txt vs test_output.txt

## Key points:
* Alignify will align code blocks using spaces
* Alignify will keep indentation intact
* The output can be re-alignified (eg. to re-align after a change)
* To signal a code block break to Alignify, use a tab or at least two spaces
* Alignify is agnostic to what it formats (ie. what programming language the input is written in, if any)
* The horizontal offset of a code block is controlled by the longest prefix (excluding spaces) plus the number of spaces that follows that.

	    
## How to use it
### From a terminal

		cat code.txt | python alignify.py
		python alignify.py code.txt
		
### As a service (Mac OS X)
* Create a new script in Automator
* Drag-drop a "Run Shell Script" (under Library->Utilities)
* Pick /usr/bin/python
* Make sure "Ouput replaces selected text" is checked
* Save it as "Alignify"
* Open System Preferences -> Keyboard
* Under "Services", bind ctrl-shift-A to Alignify
* Select any text in any application and press ctrl-shift-A to align it
* ??????
* PROFIT!


## Caveats
* Code must be indented with tabs (if at all). If you are indenting with spaces, [STOP](http://vim.wikia.com/wiki/Indent_with_tabs,_align_with_spaces). If the code is indented with tabs, Alignify can easily keep indentation intact, and align lines that start with spaces. However, if you indent your code with spaces then there is no sure-fire way for Alignify to distinguish between indentation and intent for align, eg:

	    if done:  // Comment
	        return  // Align 'return' or the comment or none?
	        
For this reason, support for indentation with spaces is limited.
	    
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


## Future work:
### Smart-align
Handle empy spaces by matching code blocks to its closest neighbor:

		foo      bar   baz
		foobar           raboof
		badger  snake   mushroom
		
		  ->
		
		foo     bar     baz
		foobar          raboof
		badger  snake   mushroom

### Better support for indentation with spaces
Even though indenting code with spaces is stupid (see *Caveats*), Alignify could support it to the point where it can detect it and ignore it on per-block-level, and perhaps smartly guess what is indentation or spaces.


## I want to help
Great! Just clone it and send pull-requests =)

## Who
Alignify was created by Emil Ernerfeldt, inspired by [Nick Gravgaard's Elastic Tabstops](http://nickgravgaard.com/elastictabstops/).