sudo usermod -aG nopasswdlogin rbeninca
sudo nano /etc/lightdm/lightdm.conf

[Seat:*]
autologin-user=rbeninca
autologin-user-timeout=0
user-session=LXDE


mkdir -p /home/rbeninca/.config/lxsession/LXDE
nano /home/rbeninca/.config/lxsession/LXDE/autostart

#adicionar a linha abaixo no autostart para iniciar o painel automaticamente apos o login
@/usr/bin/python3 /home/rbeninca/app/main.py