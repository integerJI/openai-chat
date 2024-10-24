#!/bin/bash

git pull

# 커밋 메시지를 입력받음
echo "Enter your commit message:"
read commit_message

# Git 명령어 실행
git init
git add .
git commit -m "$commit_message"
git push origin main
