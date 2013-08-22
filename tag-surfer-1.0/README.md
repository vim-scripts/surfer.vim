# Tag Surfer

Fuzzy tag search for Vim.

## Installation

**Step 1:** First, check if your system meets the following requirements:

* Linux, Mac OS, Windows
* Vim 7.3+ compiled with python 2.x
   
**Step 2:** Get [Exuberant Ctags](http://ctags.sourceforge.net/). You can check 
if it is already installed on your system with

    $ ctags --version. 

If you don't see the *Exuberant Ctags* string somewhere in the ouput then you
need to install it:
    
* **Windows:** You can easily get the `ctags.exe` executable from
[http://ctags.sourceforge.net](http://ctags.sourceforge.net).

* **Linux:** You may want to check out specific instructions for your
distribution.

* **Mac:** Unfortunately, the *ctags* program that you may find under
`/usr/bin` is outdated so you better get the new version using
*homebrew* (`brew install ctags`). 

Just be sure that once installed, the *ctags* executable can be found in your
`$PATH` (or `%PATH%` for Windows users). Usually *Tag Surfer* is able to locate
the correct *ctags* binary by himself. If this is not the case, set the 
option `g:tsurf_ctags_bin` in your `.vimrc`:   

    let g:tsurf_ctags_bin = "/path/to/my/ctags"  
  
**Step 3:** Copy the content of the *Tag Surfer* folder into your `~/.vim` 
directory or install the plugin with a plugin manager (recommended) such as
[Vundle](https://github.com/gmarik/vundle), [Pathogen](https://github.com/tpope/vim-pathogen) 
or [Neobundle](https://github.com/Shougo/neobundle.vim).

**Step 4:** **[Only for non-Windows users]** Compile the C component: 

    $ ./complete-installation.sh

This will compile some C files needed for better search performances.

I'm sorry for Windows users but there is no support for compiling the "search"
component on your system. But don't worry, this does not means *Tag
Surfer* won't work but just that searches won't be as fast as with this
component compiled.


## Quick start

Using *Tag Surfer* is straightforward. To search for tags in all loaded buffers
execute the `:Tsurf` command. If all you see is a disheartening error message
or just *nothing found...* then skip ahead to the *Common issues* section,
otherwise, you can start to interact with search results with the following
keys.

* `UP`, `TAB`, `CTRL+K`: move up.
* `DOWN`, `CTRL+J`: move down.
* `RETURN`, `CTRL+O`, `CTRL+G`: jump to the selected tag.
* `CTRL+P`: open a preview window for the selected tag.
* `CTRL+S`: split the window for the selected tag.
* `ESC`, `CTRL+C`: close the search results list.
* `CTRL+U`: clear the current search.

Rememberer that when you jump to a tag you can easily jump back to the previous
position pressing `CTRL+T`, just as you would normally do in Vim! 

#### Modifiers and the search scope

Searches are not limited to loaded buffers. You can narrow or widen the
search scope using modifiers. A modifier is simply a special letter that you
prepend to your search query. Below is list of all available modifiers:

* `%`: this modifier narrows the search scope to the current buffer.
* `#`: this modifier widens the search scope to all files of the current
project. Note that a project root is assumed to be the one that contains 
any of the file or directory names listed in the `g:tsurf_root_markers` 
option (by default these are `.git`, `.svn`, `.hg`, `.bzr` and `_darcs`).

#### Languages support

*Exuberant Ctags* only supports a limited set of languages. You can check what
languages are supported with

    $ ctags --list-languages

If your favorite language is not listed in the output of the previous command,
the easiest way to add support for it in *Tag Surfer* is to search for
a *ctags-compatible* program that can generate tags for that language. *Tag
Surfer* provides the `g:tsurf_custom_languages` option to easily integrate a custom
*ctags-compatible* program for non-supported languages:

```vim
let g:tsurf_custom_languages = {
    \ "<filetype>" : {
        \ "bin": "/path/to/my/custom/ctags",
        \ "args": "--arguments for the --custom ctags",
    \ }
\}
```

With the *bin* and *args* you can set the path of custom *ctags* program and
its arguments respectively.  In order to make things work you have to be sure
that the output of the custom *ctags-compatible* program is will be **sorted**
and redirected to **stdout**, so you may need to set the arguments accordingly.

```vim
let g:tsurf_custom_languages = {
    \ "<filetype>" : {
        \ "extensions": [".ext1", ".ext2"],
    \ }
\}
```

Setting the *extensions* key is paramount. This is a list of file extensions
used by source files of the given `<filetype>`. 

Other minor customizations require you to set a couple of others keys:

```vim
let g:tsurf_custom_languages = {
    \ "<filetype>" : {
        \ "exclude_kinds": ["constant", "variable"]
    \ }
\}
```

With the `exclude_kinds` key you can set exclusion rules based on the kind of the tag. 
For example, the code above will exclude all tags with the kind `constant` or `variable`
from search results for files with the filetype `<filetype>`. 

```vim
let g:tsurf_custom_languages = {
    \ "<filetype>" : {
        \ "kinds_map": {"c":"constant", "v":"variable"}
    \ }
\}
```

Setting the `kinds_map` key may be required when your custom *ctags* prgram
displays only single letters for the *kind* field and you want more readable
names. 

## Commands

#### :Tsurf

This command opens *Tag Surfer*.   
See the *Quick start* section for how to interact with the search results list.

#### :TsurfSetRoot

Use this command when you want to specify a custom root for your project. This
command may be useful if your project root cannot be located with any of the
markers in `g:tsurf_root_markers`.

If you run the command with no arguments the current working directory is used 
(the one that is printed by the comamnd `:pwd`), otherwise you have to specify
an absolute path (you can safely use `~` or `$HOME` for the home directory).  

Note that when you set a custom root for your project this will have always the
precedence over the markers specified in `g:tsurf_root_markers`.

#### :TsurfUnsetRoot

Use this command to unset the custom root previously set with the `:TsurfSetRoot`
command.


## Basic options

#### g:tsurf\_ctags\_bin

With this option you can set the path of the *ctags* binary on your system if
*Tag Surfer* cannot locate it by himself.

Default: `""`

#### g:tsurf\_ctags\_custom\_args

With this option you can set additional arguments for `g:tsurf_ctags_bin`.
I say *additional* because *Tag Surfer* already provides some default arguments
to `g:tsurf_ctags_bin` (`"-f - --format=2 --excmd=pattern --sort --fields=nKzmafilmsSt"`).
   
You may want to use this option when you need to provide filetype specific
arguements to the *ctags* executable. See the official [Exuberant Ctags documentation]
(http://ctags.sourceforge.net/ctags.html) for all the arguments available to
*Exuberant Ctags*.

Default: `""`

#### g:tsurf\_custom\_languages

With this option you can add support for languages not officially supported 
by Exuberant Ctags. See the section "Quick Start" for 
instructions on how to set this option.

Default: `{}`

#### g:tsurf\_smart\_case

With this option you can customize the behavior of uppercase letters in your
search query. If this option is set to `1` (which is by default),
case-sensitive matching is done only for uppercase letters of your search
query. (This works just as the vim option `smartcase`) 

Default:  `1`

#### g:tsurf\_root\_markers

This option is a list containing file or directory names used by *Tag Surfer*
to locate the current project root. Note that these have no precedence over
a custom root that may have been set with the `:TsurfSetRoot` command.

Default:  `['.git', '.svn', '.hg', '.bzr', '_darcs']`

#### g:tsurf\_buffer\_search\_modifier

With this option you can set the modifier used to narrow the search scope
to the current buffer.

Default: `"%"`

#### g:tsurf\_project\_search\_modifier

With this option you can set the modifier used to widen the search scope
to the current buffer.

Default: `"#"`

## Appearance options

#### g:tsurf\_max\_results

With this option you can set the maximum number of search results that will be displayed.

Default: `1`

#### g:tsurf\_line\_format

With this option you can set the format for the results fo your searches.
This option consists of a list of strings, each one containing a field name
surrounded by curly braces of the form `{<name>}` and that will be 
replaced with the respective *ctags* field `<name>` (have a look at the default 
value below). Each string item of the list can contain only field and the
reason is that if an attribut in unavailable for a specific tag the whole item
won't show up when formattin search results.

The set of available fields varies depending on the language you are using so
you have to consult the official [Exuberant Ctags documentation](http://ctags.sourceforge.net/ctags.html)
or have a look at the raw *ctags* output for a specific language. However, the 
list below shows all attributes that are always available:

* `name`: the tag name.
* `file`: the file where the tag is located.
* `kind`: the kind of the tag (execute in your terminal `ctags --list-kinds` to
list all kinds for every supported language).
* `context`: the line where the tag is located. (Note that if you are using a 
custom *ctags* executable this field may be a number).

Default: `['{file}', '| {kind}']` 

#### g:tsurf\_tag\_file\_full\_path

With this option you can decide whether or not the full path will be displayed
for the attribute `{file}` in the option `g:tsurf_line_format`. Note that, when
possible, `$HOME` is substituted by `~` and if you are in a project whose root
has been located (either via `g:tsurf_root_markers` or the `:TsurfSetRoot`
command) all the paths will be relative to the current project root.

Default: `0`

#### g:tsurf\_tag\_file\_custom\_depth

With this option you can decide how many directory levels will be displayed for
the attribute `{file}` in the option `g:tsurf_line_format`. For example, if you
set the value `2` for this option you'll end up with paths such as
`container/file.vim`. Note that when `g:tsurf_tag_file_full_path == 1` this
option is simply ignored.

Default: `-1` (the whole path is displayed)

#### g:tsurf\_tag\_file\_relative\_to\_project\_root

Set this option to `1` and paths value for the attribute `{file}` in the option
`g:tsurf_line_format` will always be relative to the project root when you
perform project-wide searches, even if `g:tsurf_tag_file_custom_depth > 1`.
Note that this behavior is default when `g:tsurf_tag_file_full_path == 1`.

Default: `1`

#### g:tsurf\_prompt

With this option you can customize the prompt appearance.

Default: `" @ "`

#### g:tsurf\_prompt\_color

With this option you can set the color for the prompt. As values, you can use
names of previously defined highlight groups, such as `String`, `Question`,
etc. Yo can execute the vim command `:hi` to see all defined highlight
groups.

Default: `"None"` (no color)

#### g:tsurf\_current\_line\_indicator

With this option you can set the character (or string) used to indicate the current
selected line in the search results window. Note that if you have `cursorline`
vim option set then the current line will be also highlighted with the color
group 'CursorLine'.

Default: `" > "`

#### g:tsurf\_no\_results\_msg

With this option you can set the string displayed when no result are found for
the current search query.

Default: `" nothing found..."`

#### g:tsurf\_shade\_color

With this option you can define the color used to highlight everything that is
not the tag name and the current line indicator in the search results window.
As values, you can use previously defined highlight groups, such as `String`,
`Comment`, etc.. or full-fledged color declarations as you would do when
defining your own highlight group (as you can see in the default argument).
see in the default argument).

Examples:

```vim
" example 1
let g:tsurf_shade_color = "gui=NONE guifg=#999999 cterm=NONE ctermfg=245"

" example 2
hi MyHighlightGroup gui=NONE guifg=#999999 cterm=NONE ctermfg=245
let g:tsurf_shade_color = "MyHighlightGroup" 

" example 3
let g:tsurf_shade_color = "String" 
```

Default: `"Comment"`

#### g:tsurf\_shade\_color\_darkbg

This option behaves as the `g:tsurf_shade_color` option but this one is used
when the current background is *dark* (`&backgroud == "dark"`).
  
See the `g:tsurf_shade_color` option for examples.

Default: `< the value of g:tsurf_shade_color >`

#### g:tsurf\_matches\_color

With this option you can define the color used to highlight every single
character that match your search query for each result. As values, you can use
previously defined highlight groups, such as `String`, `Comment`, etc.. or
full-fledged color declarations as you would do when defining your own
highlight group (as you can see in the default argument).
   
Examples:

```vim
" example 1
let g:tsurf_matches_color = "gui=NONE guifg=#ff6155 cterm=NONE ctermfg=203"

" example 2
hi MyHighlightGroup gui=NONE guifg=#ff6155 cterm=NONE ctermfg=203
let g:tsurf_matches_color = "MyHighlightGroup" 

" example 3
let g:tsurf_matches_color = "String" 
```

Default: `"WarningMsg"`

#### g:tsurf\_matches\_color\_darkbg

This option behaves as the `g:tsurf_matches_color` option but this one is used
when the current background is *dark* (`&backgroud == "dark"`).
  
See the `g:tsurf_matches_color` option for examples.

Default: `< the value of g:tsurf_matches_color >`


## Common issues


## Contributing

Do not esitate to send [patches](../../issues?labels=bug&state=open),
[suggestion](../../issues?labels=enhancement&state=open) or just to ask
[questions](../../issues?labels=question&state=open)! There is always
room for improvement.


## Credits

See [this page](https://github.com/gcmt/tag-surfer/graphs/contributors) for all
*Tag Surfer* contributors. 


## Changelog

See [CHANGELOG.md](CHANGELOG.md).


## License

Copyright (c) 2013 Giacomo Comitti

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
