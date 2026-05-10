#!/bin/bash
# git rebase -i todo list editor — used as GIT_SEQUENCE_EDITOR.
# 첫 commit(base)은 pick 유지, 2번째부터 squash로 자동 변경.
sed -i.bak -E '2,$s/^pick /squash /' "$1"
