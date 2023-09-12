if ! git diff --exit-code data evaluation spatialyze; then
  git add --all
  git config --global user.name 'Github Actions Bot'
  git config --global user.email 'spatialyze-actions-bot@users.noreply.github.com'
  git commit -m "style: $1"
fi

git status

git pull --rebase
git push

exit 0