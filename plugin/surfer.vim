" ============================================================================
" File: plugin/surfer.vim
" Description: Code navigator for vim
" Mantainer: Giacomo Comitti (https://github.com/gcmt)
" Url: https://github.com/gcmt/vim-surfer
" License: MIT
" ============================================================================


" Init
" ----------------------------------------------------------------------------

if  v:version < 703 || !has('python') || exists("g:surfer_loaded") || &cp
    finish
endif

" Check for the correct python version
python << END
import sys
current = sys.version_info[0]
if current != 2:
    vim.command("let g:surfer_unsupported_python = 1")
END
if exists("g:surfer_unsupported_python")
    echohl WarningMsg |
        \ echomsg "[surfer] Surfer unavailable: requires python 2.x" |
        \ echohl None
    finish
endif

let g:surfer_loaded = 1

" On non-Windows plarforms, tell the user that faster searches can be possible
" by compiling the C extension module.
if !has("win32")
    let s:plugin_root = expand("<sfile>:p:h:h")
    if !filereadable(s:plugin_root."/autoload/surfer/ext/search.so")
        echohl WarningMsg |
            \ echomsg "[surfer] For better performances go to the plugin "
                \ "root directory and excute `./install.sh" |
            \ echohl None
    endif
endif


" Initialize settings
" ----------------------------------------------------------------------------

let g:surfer_debug =
    \ get(g:, "surfer_debug", 0)

" Core options

let g:surfer_ctags_prg =
    \ get(g:, "surfer_ctags_prg", "")

let g:surfer_ctags_args =
    \ get(g:, "surfer_ctags_args",
    \ "-f - --format=2 --excmd=number --sort=yes --fields=nKzmafilmsSt")

let g:surfer_smart_case =
    \ get(g:, "surfer_smart_case", 1)

let g:surfer_buffer_search_modifier =
    \ get(g:, "surfer_buffer_search_modifier", "%")

let g:surfer_project_search_modifier =
    \ get(g:, "surfer_project_search_modifier", "#")

let g:surfer_root_markers =
    \ extend(get(g:, 'surfer_root_markers', []),
    \ ['.git', '.svn', '.hg', '.bzr', '.travis.yml'])

let g:surfer_exclude =
    \ get(g:, "surfer_exclude", [])

let g:surfer_exclude_kinds =
    \ get(g:, "surfer_exclude_kinds", [])

" Custom languages support

let g:surfer_custom_languages =
    \ get(g:, "surfer_custom_languages", {})

" Appearance

let g:surfer_max_results =
    \ get(g:, "surfer_max_results", 15)

let g:surfer_prompt =
    \ get(g:, "surfer_prompt", " @ ")

let g:surfer_prompt_color =
    \ get(g:, "surfer_prompt_color", "")

let g:surfer_prompt_color_darkbg =
    \ get(g:, "surfer_prompt_color_darkbg", g:surfer_prompt_color)

let g:surfer_cursorline =
    \ get(g:, "surfer_cursorline", 1)

let g:surfer_current_line_indicator =
    \ get(g:, "surfer_current_line_indicator", " ")

let g:surfer_line_format =
    \ get(g:, "surfer_line_format", [" @ {file}"])

let g:surfer_tag_file_custom_depth =
    \ get(g:, "surfer_tag_file_custom_depth", -1)

let g:surfer_tag_file_relative_to_project_root =
    \ get(g:, "surfer_tag_file_relative_to_project_root", 1)

let g:surfer_no_results_msg =
    \ get(g:, "surfer_no_results_msg", " nothing found...")

let g:surfer_shade_color =
    \ get(g:, 'surfer_shade_color', 'Comment')

let g:surfer_shade_color_darkbg =
    \ get(g:, 'surfer_shade_color_darkbg', g:surfer_shade_color)

let g:surfer_matches_color =
    \ get(g:, 'surfer_matches_color', 'WarningMsg')

let g:surfer_matches_color_darkbg =
    \ get(g:, 'surfer_matches_color_darkbg', g:surfer_matches_color)

let g:surfer_visual_kinds =
    \ get(g:, "surfer_visual_kinds", 1)

let g:surfer_visual_kinds_shape =
    \ get(g:, "surfer_visual_kinds_shape", "\u2022") . " "

let g:surfer_visual_kinds_colors =
    \ extend({
        \ "interface": "Repeat",
        \ "class": "Repeat",
        \ "member": "Function",
        \ "method": "Function",
        \ "function": "Function",
        \ "type": "Type",
        \ "variable": "Conditional",
        \ "constant": "Conditional",
        \ "field": "String",
        \ "property": "String",
    \ },
    \ get(g:, "surfer_visual_kinds_colors", {}), "force")

let g:surfer_visual_kinds_colors_darkbg =
    \ get(g:, "surfer_visual_kinds_colors_darkbg", g:surfer_visual_kinds_colors)



" Commands
" ----------------------------------------------------------------------------

command! Surf call surfer#Open()
