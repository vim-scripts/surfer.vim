" ============================================================================
" File: plugin/tagsurfer.vim
" Description: Tag surfing for vim
" Mantainer: Giacomo Comitti (https://github.com/gcmt)
" Url: https://github.com/gcmt/tsurf
" License: MIT
" Version: 1.0
" Last Changed: 17 Aug 2013
" ============================================================================


" Init
" ----------------------------------------------------------------------------

if  v:version < 703 || !has('python') || exists("g:tsurf_loaded") || &cp
    finish
endif

" Check for the correct python version
python << END
import sys
current = sys.version_info[0]
if current != 2:
    vim.command("let g:tsurf_unsupported_python = 1")
END
if exists("g:tsurf_unsupported_python")
    echohl WarningMsg |
        \ echomsg "[tsurf] Tag Surfer unavailable: requires python 2.x" |
        \ echohl None
    finish
endif

let g:tsurf_loaded = 1

" On non-Windows plarforms, tell the user that he can have better search
" prformances compiling the C extension module.
if !has("win32")
    let s:plugin_root = expand("<sfile>:p:h:h")
    if !filereadable(s:plugin_root."/autoload/tsurf/ext/search.so")
        echohl WarningMsg |
            \ echomsg "[tsurf] For better search performances go to the plugin "
                \ "root directory and excute `./complete-installation`." |
            \ echohl None
    endif
endif


" Help functions
" ----------------------------------------------------------------------------

" This function try to automatically spot the `ctags` program location
fu! s:find_ctags_bin(bin)
    let pathsep = has("win32") ? '\' : '/'
    if match(a:bin, pathsep) != -1
        return a:bin
    endif
    " Try to automatically discover Exuberant Ctags
    if has("win32")
        " `globpath()` wants forward slashes even on Windows
        let places = split(substitute($PATH, '\', '/', 'g'), ";")
    else
        let places = extend(split($PATH, ":"),
            \ ["/usr/local/bin", "/opt/local/bin", "/usr/bin"])
    endif
    for bin in [a:bin, 'ctags', 'ctags-exuberant', 'exctags', 'ctags.exe']
        for ctags in split(globpath(join(places, ","), bin), "\n")
            let out = system(ctags . " --version")
            if v:shell_error == 0 && match(out, "Exuberant Ctags") != -1
                return ctags
            endif
        endfor
    endfor
    return a:bin
endfu


" Initialize settings
" ----------------------------------------------------------------------------

let g:tsurf_debug =
    \ get(g:, "tsurf_debug", 0)

" Core options

let g:tsurf_ctags_bin =
    \ s:find_ctags_bin(get(g:, "tsurf_ctags_bin", ""))

let g:tsurf_ctags_args =
    \ get(g:, "tsurf_ctags_args", "-f - --format=2 --excmd=pattern --sort=yes --fields=nKzmafilmsSt")

let g:tsurf_ctags_custom_args =
    \ get(g:, "tsurf_ctags_custom_args", "")

" Search type and scope

let g:tsurf_smart_case =
    \ get(g:, "tsurf_smart_case", 1)

let g:tsurf_buffer_search_modifier =
    \ get(g:, "tsurf_buffer_search_modifier", "%")

let g:tsurf_project_search_modifier =
    \ get(g:, "tsurf_project_search_modifier", "#")

let g:tsurf_root_markers =
    \ extend(get(g:, 'tsurf_root_markers', []), ['.git', '.svn', '.hg', '.bzr', '_darcs'])

" Custom languages support

let g:tsurf_custom_languages =
    \ get(g:, "tsurf_custom_languages", {})

" Appearance

let g:tsurf_max_results =
    \ get(g:, "tsurf_max_results", 15)

let g:tsurf_prompt =
    \ get(g:, "tsurf_prompt", " @ ")

let g:tsurf_prompt_color =
    \ get(g:, "tsurf_prompt_color", "")

let g:tsurf_current_line_indicator =
    \ get(g:, "tsurf_current_line_indicator", " > ")

let g:tsurf_line_format =
    \ get(g:, "tsurf_line_format", ["{file}", " | {kind}"])

let g:tsurf_tag_file_full_path =
    \ get(g:, "tsurf_tag_file_full_path", 0)

let g:tsurf_tag_file_custom_depth =
    \ get(g:, "tsurf_tag_file_custom_depth", -1)

let g:tsurf_tag_file_relative_to_project_root =
    \ get(g:, "tsurf_tag_file_relative_to_project_root", 1)

let g:tsurf_no_results_msg =
    \ get(g:, "tsurf_no_results_msg", " nothing found...")

let g:tsurf_shade_color =
    \ get(g:, 'tsurf_shade_color', 'Comment')

let g:tsurf_shade_color_darkbg =
    \ get(g:, 'tsurf_shade_color_darkbg', g:tsurf_shade_color)

let g:tsurf_matches_color =
    \ get(g:, 'tsurf_matches_color', 'WarningMsg')

let g:tsurf_matches_color_darkbg =
    \ get(g:, 'tsurf_matches_color_darkbg', g:tsurf_matches_color)


" Commands
" ----------------------------------------------------------------------------

command! Tsurf call tsurf#Open()
command! -nargs=? -complete=file TsurfSetRoot call tsurf#SetProjectRoot(<q-args>)
command! TsurfUnsetRoot call tsurf#UnsetProjectRoot()
