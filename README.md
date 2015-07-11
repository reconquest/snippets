# Let me show

![package](https://cloud.githubusercontent.com/assets/8445924/8632729/62428936-2797-11e5-9a0b-a7c7bfe0941b.gif)
![struct](https://cloud.githubusercontent.com/assets/8445924/8632734/a3579b5a-2797-11e5-81fd-2f515ac04f04.gif)
![method](https://cloud.githubusercontent.com/assets/8445924/8632753/12040d18-2798-11e5-8844-03ef1a61c1ad.gif)
![log](https://cloud.githubusercontent.com/assets/8445924/8632754/1f67fb90-2798-11e5-825b-21f01e340ade.gif)
![autoimport](https://cloud.githubusercontent.com/assets/8445924/8632757/2b8f7196-2798-11e5-8060-1544c20879e8.gif)
![complete](https://cloud.githubusercontent.com/assets/8445924/8632759/338fe40c-2798-11e5-8dbf-4062e88ba08c.gif)


# Installation

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
```

```
imap <C-F> t<TAB>.
```
