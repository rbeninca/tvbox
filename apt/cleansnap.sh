#!/bin/bash
set -e

echo "=== Limpando cache APT ==="
apt clean
apt autoremove --purge -y

echo "=== Removendo Snap e pacotes Snap pesados ==="
if command -v snap >/dev/null 2>&1; then
    snap remove chromium || true
    snap remove cups || true
    snap remove gnome-46-2404 || true
    snap remove gtk-common-themes || true
    snap remove mesa-2404 || true
    snap remove core24 || true
    snap remove core22 || true
    snap remove bare || true
    snap remove snapd || true
fi

echo "=== Removendo snapd via APT ==="
apt purge snapd -y || true

echo "=== Limpando restos do Snap ==="
rm -rf /snap
rm -rf /var/snap
rm -rf /var/lib/snapd

echo "=== Desativando download de Contents do APT ==="
cat > /etc/apt/apt.conf.d/99disable-contents <<'EOF'
Acquire::IndexTargets::deb::Contents-deb::DefaultEnabled "false";
Acquire::IndexTargets::deb::Contents-udeb::DefaultEnabled "false";
Acquire::IndexTargets::deb-src::Contents-dsc::DefaultEnabled "false";
Acquire::Languages "none";
EOF

echo "=== Ajustando fontes Deb822 para baixar apenas Packages ==="
for f in /etc/apt/sources.list.d/*; do
    if grep -q "URIs: http://ports.ubuntu.com/" "$f"; then
        if ! grep -q "Targets: Packages" "$f"; then
            sed -i '/URIs: http:\/\/ports.ubuntu.com\//,/Signed-By:/ {/Components:/a Targets: Packages
}' "$f"
        fi
    fi
done

echo "=== Limpando listas antigas do APT ==="
rm -rf /var/lib/apt/lists/*

echo "=== Limpando logs ==="
journalctl --vacuum-time=3d || true

echo "=== Limpando cache do root ==="
rm -rf /root/.cache/*

echo "=== Limpando documentação e manuais opcionais ==="
#rm -rf /usr/share/doc/*
#rm -rf /usr/share/man/*
#rm -rf /usr/share/info/*

echo "=== Limpando fontes de kernel ==="
#rm -rf /usr/src/*

echo "=== Atualizando APT ==="
apt update

echo "=== Espaço final ==="
df -h
du -h --max-depth=1 / | sort -hr | head -20