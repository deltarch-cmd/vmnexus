#!/usr/bin/env bash
base_url="http://192.168.1.140:8080/guacamole/api"

## Retrieve token
token="$(curl -X POST 'http://192.168.1.140:8080/guacamole/api/tokens' \
    -d 'username=guacadmin&password=guacadmin' | jq -r '.authToken')"

echo "TK: $token"

check="$(curl -s -o /dev/null -w "%{http_code}" -X POST 'http://192.168.1.140:8080/guacamole/api/tokens' \
    -d 'username=guacadmin&password=guacadmin')"

if [[ "$check" == "200" ]]; then
    echo "✅ Guacamole está activo"
else
    echo "❌ Guacamole no responde o hay un problema"
fi

