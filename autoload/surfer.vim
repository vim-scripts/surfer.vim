
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

let s:current_folder = expand("<sfile>:p:h")

let g:surfer_ctags_prg = surfer#find_ctags_prg(g:surfer_ctags_prg)
py import vim, sys
py sys.path.insert(0, vim.eval("s:current_folder"))
py import surfer.core
py _surfer = surfer.core.Surfer()


" Wrappers
" ----------------------------------------------------------------------------

fu! surfer#Open()
    py _surfer.Open()
endfu


" Autocommands
" ----------------------------------------------------------------------------

augroup surfer
    au!

    au BufWritePost .vimrc py _surfer.ui.setup_colors()
    au Colorscheme * py _surfer.ui.setup_colors()
    au VimLeave * py _surfer.close()

    au BufEnter * py _surfer.services.project.update_project_root()
    au BufWritePost * py _surfer.generator.rebuild_tags = True
    au BufDelete,BufNew * if empty(&buftype) | exec "py _surfer.generator.rebuild_tags = True" | endif

augroup END
