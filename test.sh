# create dummy files
mkdir -p dummy-folder && echo dummy file contents > dummy-folder/dummy-file

# test excluded
mkdir -p exclude-dummy-file-folder && cd $_ && echo $_ test > some-other.file && echo 1 > password.gpg

mkdir -p ~/test-dotfiles-folder; cd $_
git init 
git submodule add https://github.com/mvrozanti/dotty 
git submodule update --remote dotty

cat >~/test-dotfiles-folder/dotty-test-config.json <<EOL
{
    "mkdirs": ["~/.vim"],

    "copy": {
        "dummy-folder": "~/dummy-folder"
    },

    "install_cmd": "apt-get install",
    "install": [
        "vim"
    ],

    "before_bak":[
        "echo before_bak test > ~/before_bak_test_file"
    ],

    "excluded": [
        "password.gpg"
    ],

    "commands": [
        "echo commands test > ~/commands_test_file"
    ]
}
EOL

./dotty/dotty.py -b

[   -d ~/test-dotfiles-folder/dummy-folder                           ] || exit 9
[   -f ~/test-dotfiles-folder/dummy-folder/dummy-file                ] || exit 10

git add .
git commit -m "first commit"
git remote add origin https://mvrozanti:"$GITHUBPASS"@github.com/mvrozanti/test.git
git push -f -u origin master

./dotty/dotty.py -s "second commit"

find

[   -d ~/test-dotfiles-folder                                        ] || exit 2
[   -f ~/test-dotfiles-folder/dotty-test-config.json                 ] || exit 3
[ ! -f ~/test-dotfiles-folder/exclude-dummy-file-folder/password.gpg ] || exit 4
[ ! -f ~/commands_test_file                                          ] || exit 5
[ ! -f ~/test-dotfiles-folder/password.gpg                           ] || exit 6
[   -d ~/test-dotfiles-folder                                        ] || exit 7
command -v vim                                                         || exit 8

./dotty/dotty.py -r

[   -d ~/.vim ]                                                        || exit 1

echo All tests passed.
