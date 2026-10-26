#!/bin/sh
set -eu
case "${PORT:-}" in
  ''|*[!0-9]*) echo 'PORT must be an integer from 1024 to 65535' >&2; exit 1 ;;
esac
[ "${#PORT}" -le 5 ] && [ "$PORT" -ge 1024 ] && [ "$PORT" -le 65535 ] || {
  echo 'PORT must be an integer from 1024 to 65535' >&2; exit 1;
}
# Substitute only PORT; retain nginx variables such as $uri.
envsubst '${PORT}' < /etc/enrama/nginx.conf.template > /tmp/enrama-nginx.conf
exec nginx -c /tmp/enrama-nginx.conf -g 'daemon off;'
