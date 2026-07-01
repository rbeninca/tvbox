sudo -u rbeninca DISPLAY=:0 XAUTHORITY=/home/rbeninca/.Xauthority chromium --kiosk https://ifsc.edu.br


sudo -u rbeninca env \
DISPLAY=:0 \
XAUTHORITY=/home/rbeninca/.Xauthority \
DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
chromium --kiosk --no-first-run --disable-infobars https://ifsc.edu.br



#video com gpu
sudo -u rbeninca DISPLAY=:0 XAUTHORITY=/home/rbeninca/.Xauthority \
DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
chromium \
  --kiosk \
  --enable-gpu \
  --enable-features=VaapiVideoDecoder \
  --disable-software-rasterizer \
  --no-sandbox \
  https://youtube.com/shots/9n2m8Xo7l3A



#testar gpu no contexto do user rbeninca
root@aml-s9xx-box:~# sudo -u rbeninca env DISPLAY=:0 XAUTHORITY=/home/rbeninca/.Xauthority \
glxinfo | grep -i "OpenGL renderer"
OpenGL renderer string: Mali450
root@aml-s9xx-box:~# 
