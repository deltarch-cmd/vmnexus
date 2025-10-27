# VNC
Para las conexiones con el resto de máquinas a través de Guacamole se va a usar VNC. El proceso para esto es bastante sencillo, siendo necesario levantar un servidor VNC en la máquina a la cual el servidor de Guacamole se conectará.
## Instalación
### Archlinux
El paquete para preparar un servidor VNC en una distribución basada en Archlinux es **tigervnc**, el cual se encuentra disponible en los repositorios oficiales.
```bash
sudo pacman -S tigervnc
```

### Debian
Por otro lado, el paquete en una distribución basada en Debian se llama **tightvncserver**.
```bash
sudo apt install tightvncserver
```

## Credenciales para la conexión
User: El mismo que el de la VM a la cual nos queremos conectar
Password: La introducida al iniciar el servidor por primera vez

## Configuración
Debido a que en ambos casos la configuración del servidor es prácticamente idéntica, lo separo en el mismo apartado.
- [Guía seguida para Debian](https://www.digitalocean.com/community/tutorials/how-to-install-and-configure-vnc-on-debian-10)

En la guía anterior se muestra una configuración relativamente más avanzada (y la que posiblemente sea recomendada realizar). Por otro lado, yo voy a poner la configuración que yo hice, siendo esta mucho más simple y rápida.

- Establecer la contraseña
```bash
vncpasswd
```
Esta debe tener mínimo 6 caracteres (y máximo 8 teóricamente). En el promp yo solo creé la contraseña para el acceso completo de la máquina, ignorando la "*view-only*" contraseña.

- Creación del archivo de configuración VNC
```bash
mkdir -p ~/.vnc
vim ~/.vnc/xtartup 
```
Este archivo será el usado para iniciar la "vista" VNC y contendrá las siguientes líneas:
```bash
#!/bin/bash
## I recommend using #!/usr/bin/env bash instead

unset SESSION_MANAGER
unset DEBUS_SESSION_BUS_ADDRESS
exec startlxqt & # Esto es solo en mi caso al usar LXQT como DE
```
Por último, solo es necesario hacer el archivo ejecutable:
```bash
chmod +x ~/.vnc/xstartup
```

### Iniciar el servidor VNC
Para iniciar el servidor VNC solo hará falta correr el siguiente comando:
```bash
vncserver :1 # El 1 representa el "display" a usar
```
Dependiendo del "display" que sea usado, el puerto usado por VNC cambiará, siendo el 5901 para el 1, 5902 para el 2, etc.

### Servidor VNC como servicio de Systemd
En el tutorial indicado anteriormente se muestra una forma de establecer el servidor como servicio de Systemd, permitiendo que el usuario pueda levantar el servidor en el momento en el que la máquina es encendida si así se quiere. Voy a mostrar una configuración distinta dada por ChatGPT, por si acaso la del enlace no termina de funcionar.
```bash
sudo vim /etc/systemd/system/vncserver@:1.service
```
En el archivo se incluirá la siguiente información:
```bash
[Unit]
Description=Start TigerVNC server at startup
After=syslog.target network.target

[Service]
Type=forking
User=[your_username]
PAMName=login
PIDFile=/home/[your_username]/.vnc/%H:%i.pid
ExecStartPre=-/usr/bin/vncserver -kill :%i > /dev/null 2>&1
ExecStart=/usr/bin/vncserver :%i -localhost no -geometry 1920x1080 -depth 24
ExecStop=/usr/bin/vncserver -kill :%i

[Install]
WantedBy=multi-user.target
```
Por último, se habilita e inicia el servicio:
```bash
sudo systemctl enable vncserver@:1.service --now
```
