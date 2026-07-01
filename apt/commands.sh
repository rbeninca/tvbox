
cat /etc/apt/sources.list.d/*

#impedir o apt de baixar listas de pacotes  Contents
sed -i '/URIs: http:\/\/ports.ubuntu.com\//,/Signed-By:/ {/Components:/a Targets: Packages }' /etc/apt/sources.list.d/*

rm -rf /var/lib/apt/lists/*
apt update