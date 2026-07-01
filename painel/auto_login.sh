sudo usermod -aG nopasswdlogin rbeninca
sudo nano /etc/lightdm/lightdm.conf

[Seat:*]
autologin-user=rbeninca
autologin-user-timeout=0
user-session=LXDE


mkdir -p /home/rbeninca/.config/lxsession/LXDE
nano /home/rbeninca/.config/lxsession/LXDE/autostart

#adicionar a linha abaixo no autostart para iniciar o painel automaticamente apos o login
#https://chatgpt.com/c/69ea0876-b4fc-83e9-b628-bab82843f9ca#:~:text=%40chromium%20%2D%2Dkiosk%20http%3A//localhost
@/usr/bin/python3 /home/rbeninca/app/main.py