" ============================================================================
" File: autoload/tsurf.vim
" Description: Tag surfing for vim
" Mantainer: Giacomo Comitti (https://github.com/gcmt)
" Url: https://github.ctsurf/gcmt/tsurf
" License: MIT
" Version: 1.0
" Last Changed: 17 Aug 2013
" ============================================================================


" Init
" ----------------------------------------------------------------------------

let s:current_folder = expand("<sfile>:p:h")
py import vim, sys
py sys.path.insert(0, vim.eval("s:current_folder"))
py import tsurf.core
py tag_surfer = tsurf.core.TagSurfer()


" Wrappers
" ----------------------------------------------------------------------------

fu! tsurf#Open()
    py tag_surfer.Open()
endfu

fu! tsurf#SetProjectRoot(root)
    py tag_surfer.SetProjectRoot(vim.eval("a:root"))
endfu

fu! tsurf#UnsetProjectRoot()
    py tag_surfer.UnsetProjectRoot()
endfu


" Autocommands
" ----------------------------------------------------------------------------

augroup tag_surfer
    au!

    au BufWritePost .vimrc py tag_surfer.ui.renderer.setup_colors()
    au Colorscheme * py tag_surfer.ui.renderer.setup_colors()
    au VimLeave * py tag_surfer.close()

    " Invalidate the cache
    au BufEnter,BufWrite * py tag_surfer.services.curr_project.files_cache = []
    au BufEnter * py tag_surfer.services.curr_project.root_cache = ""

augroup END
