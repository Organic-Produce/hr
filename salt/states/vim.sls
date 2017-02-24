/home/{{ pillar['main_user'] }}/.vim:
    file.directory:
        - user: {{ pillar['main_user'] }}
        - group: {{ pillar['main_user'] }}

/home/{{ pillar['main_user'] }}/.vim/autoload:
    file.directory:
        - user: {{ pillar['main_user'] }}
        - group: {{ pillar['main_user'] }}

pathogen:
    file.managed:
        - name: /home/{{ pillar['main_user'] }}/.vim/autoload/pathogen.vim
        - user: {{ pillar['main_user'] }}
        - group: {{ pillar['main_user'] }}
        - source: salt://vim/pathogen

nerdtree:
    git.latest:
        - name: https://github.com/scrooloose/nerdtree.git
        - rev: b0bb781fc73ef40365e4c996a16f04368d64fc9d
        - target: /home/{{ pillar['main_user'] }}/.vim/bundle/nerdtree
        - user: {{ pillar['main_user'] }}
        - force: True

solarized:
    git.latest:
        - name: git://github.com/altercation/vim-colors-solarized.git
        - rev: 528a59f26d12278698bb946f8fb82a63711eec21
        - target: /home/{{ pillar['main_user'] }}/.vim/bundle/vim-colors-solarized
        - user: {{ pillar['main_user'] }}
        - force: True

vimrc:
    file.managed:
        - name: /home/{{ pillar['main_user'] }}/.vimrc
        - user: {{ pillar['main_user'] }}
        - group: {{ pillar['main_user'] }}
        - source: salt://vim/vimrc

/home/{{ pillar['main_user'] }}/.vim/tmp:
    file.directory:
        - user: {{ pillar['main_user'] }}
        - group: {{ pillar['main_user'] }}
