# Setup the Guacamole containers
Steps to setup the containers needed to deploy Guacamole server + Guacamole client
- Access in http://localhost:8080/guacamole

## Pasos para inicializar el contenedor de la base de datos por la primera vez
``` bash
podman run --rm docker.io/guacamole/guacamole /opt/guacamole/bin/initdb.sh --mysql > initdb.sql
podman-compose up -d mysql

# Depende de los usuarios establecidos en el docker-compose
podman exec -i guacamole-db mysql -uroot -proot_password guacamole_db < initdb.sql 

podman-compose up -d
```

## Comandos importante para la gestión de contenedores 
``` bash
# Check the status of the containers, even the ones stopped
podman ps -a

# Remove stopped containers
podman rm container_id # Works with container_name too

# Check the logs of a container
podman logs container_name 

# Remove existing pods by name
podman pod rm pod_name

# Remove any stopped containers, images, or unused pods named "pod_name"
podman pod rm pod_name -f
podman container prune -f
```

## Problems with SELinux and containers
Tuve problemas en la máquina de Rocky con el archivo guacamole.properties y la carpeta ./data, la cual contiene todos los datos de la base de datos. El problema en general era que los contenedores no tenían acceso a estos archivos, haciendo que no fuera posible usar los datos de ./data o leer el archivo guacamole.properties.

Esto se debe a que Rocky Linux (RHEL based, Fedora based y CentOS based en general) tiene habilitado SELinux (Security Enhanced Linux) por defecto en modo "Enforcing", por lo que hay que indicar que ambos archivos sean accesibles para los contenedores con los siguientes comandos.
``` bash
sudo chcon -Rt container_file_t ./data
sudo chcon -Rt container_file_t guacamole.properties
```

### SELinux
Para comprobar si nuestro OS tiene SELinux habilitado y en qué modo, se puede correr el siguiente comando
``` bash
sestatus
```

Para modificarlo, se puede hacer desde el siguiente archivo:
``` bash
/etc/selinux/config
```

Este archivo muestra la configuración de SELinux, pudiendo establecer el **modo** en el que queremos que corra (Enforcing, Permissive o Disabled) y el **tipo**, el cual indica los procesos que son protegidos.
