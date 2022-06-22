#!/bin/bash

set -euE

echo "$0 $@ [$$] START" >&2

if [ "${1:-}" == '--help' ]; then
	echo "Info: $0 - утилита для автоинкремента версии и выкладывания."
	echo "Usage: $0 [--help]"
	echo "Example: $0 - $(grep $0 "# [0-9]")"
	exit 0
fi

main() {
	local last_tag tags new_tag
	# 1 - прогонит тесты
	pytest epythets
	# 2 - найдёт последний тег в репе
	tags="$(git tag -l)"
	last_tag="$(sort -rV <<< "$tags" | head -n1)"
	new_tag="${last_tag%.*}.$((${last_tag##*.}+1))"
	# 3 выставит его в setup.py
	sed -e "s/version=.*/version='$new_tag',/" -i setup.py
	# 4 закоммитит
	git add setup.py
	git commit -m "Выпуск версии $new_tag"
	# 5 поставит новый тег поверх этого коммита
	git tag "$new_tag"
	# 6 запушит
	git push origin main --tags
	# 7 соберёт sdist
	python3.8 setup.py sdist
	# 8 отправит его в pypi
	twine upload "dist/epythets-${new_tag#v}.tar.gz"
	return 0
}

main "$@"
echo "$0 $@ [$$] SUCCESS" >&2
exit 0
