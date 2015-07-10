```viml
Plug 'reconquest/snippets'

# You should use patched ultisnips!
Plug 'seletskiy/ultisnips', { 'branch': 'autotrigger' }
    let g:UltiSnipsSmippetDirectories = [
    \     $HOME . '/.vim/Ultisnips/',
    \     $HOME . '/.vim/bundle/snippets/'
    \]
    let g:UltiSnipsEnableSnipMate = 0
    let g:UltiSnipsExpandTrigger="<TAB>"

    augroup textwidth_for_snippets
        au!
        au FileType snippets set textwidth=0
    augroup end

Plug 'reconquest/vim-pythonx'
    au filetype_go FileType go nmap <buffer>
         \ <Leader>gc :py px.go.goto_const()<CR>

    au filetype_go FileType go nmap <buffer>
         \ <Leader>gt :py px.go.goto_type()<CR>

    au filetype_go FileType go nmap <buffer>
         \ <Leader>gv :py px.go.goto_var()<CR>

    au filetype_go FileType go nmap <buffer>
         \ <Leader>gl :py px.go.goto_prev_var()<CR>
```

```
imap <C-F> t<TAB>.
```
