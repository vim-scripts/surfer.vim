
" autoload/surfer.vim


" Helper functions
" ----------------------------------------------------------------------------

" This function try to automatically spot the `ctags` program location
fu! surfer#find_ctags_prg(prg)
    let pathsep = has("win32") ? '\' : '/'
    if match(a:prg, pathsep) != -1
        return a:prg
    endif
    " Try to automatically discover Exuberant Ctags
    if has("win32")
        " `globpath()` wants forward slashes even on Windows
        let places = split(substitute($PATH, '\', '/', 'g'), ";")
    else
        let places = extend(split($PATH, ":"),
            \ ["/usr/local/bin", "/opt/local/bin", "/usr/bin"])
    endif
    let prgs = ['ctags', 'ctags-exuberant', 'exctags', 'ctags.exe']
    let prgs = extend(empty(a:prg) ? [] : [a:prg], prgs)
    for prg in prgs
        for ctags in split(globpath(join(places, ","), prg), "\n")
            let out = system(ctags . " --version")
            if v:shell_error == 0 && match(out, "Exuberant Ctags") != -1
                return ctags
            endif
        endfor
    endfor
    return a:prg
endfu


" Init
" ----------------------------------------------------------------------------

let s:curr_folder = expand("<sfile>:p:h")

" this variable MUST match the `version` constant in the extension module
" `surfer.ext.search` so that we can tell the user when he needs to recompile
" the search component.
let s:latest_extension_version = 2
let s:extension_exists = filereadable(s:curr_folder."/surfer/ext/search.so")

" On non-Windows plarforms, tell the user that faster searches can be possible
" by compiling the C extension module.
if !has("win32") && !s:extension_exists
    echohl WarningMsg |
        \ echomsg "[surfer] For better performances go to the plugin root"
                \ "directory and excute `./install.sh" |
        \ echohl None
endif

py import vim, sys
py sys.path.insert(0, vim.eval("s:curr_folder"))

" Check if the user is using the latest version of the C extension module
if s:extension_exists
    py import surfer.ext.search
    py vim.command("let s:curr_version = {}".format(
        \ getattr(surfer.ext.search, "__version__", -1)))
    if s:curr_version != s:latest_extension_version
        echohl WarningMsg |
            \ echomsg "[surfer] The search component has been updated, you"
                    \ "need to recompile it. Go to the plugin root directory"
                    \ "and excute `./install.sh`" |
            \ echohl None
        let g:_surfer_stay_silent = 1
    endif
endif

" Discover the ctags program
let g:surfer_ctags_prg = surfer#find_ctags_prg(g:surfer_ctags_prg)

" Instantiate the plugin object
py import surfer.core
py _surfer = surfer.core.Surfer()


" Wrappers
" ----------------------------------------------------------------------------

fu! surfer#Open()
    if get(g:, "_surfer_stay_silent", 0)
        let g:_surfer_stay_silent = 0
    else
        py _surfer.Open()
    endif
endfu


" Autocommands
" ----------------------------------------------------------------------------

augroup surfer
    au!

    au BufWritePost .vimrc py _surfer.ui.setup_colors()
    au Colorscheme * py _surfer.ui.setup_colors()
    au VimLeave * py _surfer.close()

    au BufEnter * py _surfer.project.update_root()
    au BufWritePost * py _surfer.generator.rebuild_tags = True
    au BufDelete,BufNew * if empty(&buftype) | exec "py _surfer.generator.rebuild_tags = True" | endif

augroup END
