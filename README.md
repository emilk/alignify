# Alignify


## What
Alignify is a python script designed to take a peice of code and align 'blocks' in that code. An example input is

	int one = 1; // Duh
	float pi = 3;   // Close enough.
	string h2g2 = 42; // ...

And output:

	int    one  =  1; // Duh
	float  pi   =  3; // Close enough.
	string h2g2 = 42; // ...

For more examples, see `sample_in.txt` vs `sample_out.txt`


## Why
Code readability matters. Alignify makes it easier to produce clean and readable code.


## Key points:
* Alignify will align code blocks using spaces
* Alignify will leave indentation intact (tabs as well as spaces)
* The output can be re-alignified (eg. to re-align after a change)
* Alignify will recognize quoted strings (`"double"` and `'single'`)
* Alignify will recognize `//C++` and `--Lua` comments


## How to use it

### From a terminal

	cat code.txt | python alignify.py
	python alignify.py code.txt


### As a Sublime Text 3 plugin
Copy `alignify.py` to `Packages/User` and add the following to your user keymap:

	{ "keys": ["super+shift+a"], "command": "alignify" }

### From Vim
Copy `alignify.py` to `~/.vim/alignify.py` and add the following to your .vimrc:

	map <C-A> :!~/.vim/alignify.py<CR>

Open Vim and mark the text you want to align with `V (shift+v)` and then `ctrl+shift+a`

### As a service (Mac OS X)
* Create a new script in Automator
* Drag-drop a "Run Shell Script" (under Library->Utilities)
* Pick /usr/bin/python
* Make sure "Ouput replaces selected text" is checked
* Save it as "Alignify"
* Open System Preferences -> Keyboard
* Under "Services", bind cmd-shift-A to Alignify
* Select any text in any application and press cmd-shift-A to align it
* ??????
* PROFIT!


### In Qt Creator (Windows)

* Choose Tools->External->Configure... from the main menu.
* Select 'Text' in the tree-view and klick the Add-button and choose 'Add Tool'.
* Name the tool 'Alignify'
* Write a short description in the 'Description'-field.
* Enter the path to your python.exe in the 'Executable'-field.
* Enter the path too the alignify.py script in the 'Argunments'-filed
* Change the 'Output'-dropdown menu to 'Replace Selection'.
* Put %{CurrentDocument:Selection} in the 'Input'-field.
* select OK or Apply.

You can now use Alignify from Tools->External->Text->Alignify on the main menu.

To bind the tool to a keyboard shortcut:

* Select Tools->Options... on the main menu. Select the Keyboard tab.
* SelectTools->External.Alignify on the list.
* Enter a shortcut in the 'Key sequence'-field, e.g. Ctrl+Shift+A.

Click OK and you're good to go.


## TODO:

### Smart-align
Handle gaps by matching code blocks to their closest neighbor:

	foo      bar   baz
	foobar           raboof
	badger  snake   mushroom

	  ->

	foo     bar     baz
	foobar          raboof
	badger  snake   mushroom


## I want to help
Great! Just clone it and send pull-requests =)
