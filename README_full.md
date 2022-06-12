## Альтернативные способы установки

В целом в систему ставить необязательно, можно в пользовательскую папку, но в таком случае вы должны обеспечить наличие в `$PATH` путь до `$HOME/.local/bin/`.

``` shell
pip3 install --user epythets
```

Из исходников:

``` shell
git clone https://github.com/strizhechenko/epythets
cd epythets
sudo pip3 install .
```

А можно и вовсе не устанавливать. Вместо вызова утилиты `epythets` можно сидеть в папке с исходниками и дёргать `python3.8 -m epythets.__init__`. Разницы нет.
