# Despliegue de VM Nexus
Este documento describe los pasos necesarios para **configurar y desplegar** VM Nexus en un entorno controlado.

## Índice
1. [Entorno de trabajo](#entorno-de-trabajo)
2. [Configuración de Proxmox](#configuración-de-proxmox)
3. [Configuración de Guacamole](#configuración-de-guacamole)
4. [Configuración del servidor Flask](#configuración-del-servidor-flask)
5. [Configuración de MySQL](#configuración-de-mysql)
6. [Inicialización del sistema (usuario administrador)](#inicialización-del-sistema-usuario-administrador)

## Entorno de trabajo

Antes de comenzar con el despliegue, se recomienda utilizar un **entorno virtual de Python** para gestionar las dependencias. Los siguientes pasos asumen que las dependencias se encuentran instaladas.

```bash
python -m venv NOMBRE_DEL_ENTORNO # En la máquina de Rocky es 'virtual_env'
source NOMBRE_DEL_ENTORNO/bin/activate # 'NOMBRE_DEL_ENTORNO\Scripts\activate' en Windows
pip install -r requirements.txt
```

> **Consejo**: incluir la carpeta con las dependencias en el archivo `.gitignore` para no sobrecargar el repositorio.

## Configuración de Proxmox

El servidor de Proxmox es instalado y configurado tal y como se haría con cualquier otro sistema operativo, no habiendo nada que destacar.

## Configuración de Guacamole
El servidor de Guacamole ha sido desplegado haciendo uso de contenedores **Docker**. En este caso, se ha usado **Podman** como gestor de contenedores.

El archivo `docker-compose.yml` usado en el proyecto se encuentra en la carpeta `/guacamole`.

Para inicializar la base de datos usada por Guacamole, se deben ejecutar los siguiente comandos:

```bash
# Desde la carpeta con los archivos de Guacamole
podman run --rm docker.io/guacamole/guacamole /opt/guacamole/bin/initdb.sh --mysql > initdb.sql
podman-compose up -d mysql
podman exec -i guacamole-db mysql -uroot -proot_password guacamole_db < initdb.sql
```

En caso de usar una distribución de Linux con SELinux activado, será necesario permitir el acceso a los archivos utilizados por los contenedores:

```bash
sudo chcon -Rt container_file_t guacamole.properties
```

Finalmente, se levanta el servidor:

```bash
podman-compose up -d
```

Tras esto, es posible que aparezca una nueva carpeta `/data` en la cual será necesario ejecutar `chcon` también.

## Configuración del servidor Flask

El servidor Flask hace uso de un archivo `.env` para la gestión de secretos. Éste posee la siguiente estructura:

```env
# Flask App configs
# SECRET_KEY="mysecretkey" # Se ha mantenido comentado durante el proyecto
ENCRYPTION_KEY="GENERATE_ME" # Usada para cifrar las contraseñas VNC de las VMs
DATABASE_URL="mysql+pymysql://username:password@localhost:3307/flask_db"
UPLOAD_FOLDER="app/static/flask_uploads"
ALLOWED_EXTENSIONS={'pdf'} # Archivos permitidos para subir en los laboratorios

# Proxmox
PROXMOX_NODE_NAME="NODE_NAME"
PROXMOX_HOST="192.168.0.0" # IP del servidor Proxmox
PROXMOX_PORT=8006
PROXMOX_ROOT_USER="root@pam"
PROXMOX_ROOT_PASSWORD="CHANGE_ME" # Usar la contraseña del usuario Root para realizar operaciones sobre las VMs

# Guacamole
## Ajustar estas credenciales según sea necesario. Se usan las por defecto
GUACAMOLE_HOST="http://192.168.O.0:8080/guacamole"
GUACAMOLE_USER="guacadmin"
GUACAMOLE_PASSWORD="guacadmin"
GUACAMOLES_DATABASE="guacamole-db"
```

La clave de cifrado se ha generado haciendo uso de la librería **Fernet** de Python y un script similar al siguiente:

```python
from cryptography.fernet import Fernet

# Generar la clave
clave = Fernet.generate_key()

# Guardarla en un archivo (opcional)
with open("clave.key", "wb") as archivo_clave:
    archivo_clave.write(clave)

print(f"Clave generada: {clave.decode()}")
```

## Configuración de MySQL

Para desplegar el servidor MySQL se hace uso de un contenedor Docker. El archivo `docker-compose.yml` se encuentra en la carpeta `/mysql`.

Antes de iniciar el servidor, es necesario crear un archivo `.env` en el mismo directorio con la siguiente estructura:

```env
MYSQL_ROOT_PASSWORD=CHANGE_ME
MYSQL_DATABASE=flask_db

MYSQL_USER=username
MYSQL_PASSWORD=password
```

El usuario y contraseña de usuario son utilizadas para establecer la conexión con la base de datos y realizar operaciones de gestión básicas.

En el caso de cambiarlas, se recuerda **realizar los cambios necesarios en el archivo `.env` del servidor Flask**.

Tras crear el archivo ya es posible desplegar el servidor MySQL.

> **Nota**: Si se usa un sistema con SELinux, será necesario correr `chcon` en los archivos accedidos por el contenedor.

### Estructura de la base de datos

Para establecer la estructura de la base de datos esperada por la aplicación, se deben seguir algunos pasos adicionales:

- Modificar el archivo `app/__init__.py` para evitar que la aplicación intente acceder a la base de datos.

```python
. . .
def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.FlaskAppConfig')

    Session(app) # Server-side session management

    db.init_app(app)
    migrate.init_app(app, db)

    register_blueprints(app)

    ## Comentar estas dos líneas
    # with app.app_context():
    #     initialize_tasks()

    return app
```

- Desde la ruta base, ahora será posible aplicar las migraciones de la base de datos, creando a su vez la estructura de la misma:

```bash
flask db upgrade
```

- Finalmente, se descomentan las líneas anteriores.

## Iniciación del sistema (usuario administrador)

En el proyecto se ofrece una función que permite crear un usuario administrador que permita hacer uso de la aplicación al inicio.

Para ello, se debe modificar una línea del archivo `app/routes/main_routes.py`:

```python
. . .
@main_bp.route('/login', methods=['GET', 'POST'])
def login():

    . . .

        if user.is_admin:
            return redirect(url_for('admin_bp.dashboard'))
        else:
            return redirect(url_for('student_bp.home'))

    # Data loading
    # Hace referencia al archivo app/utils/populate_database.py
    manage_data(0) # '1' para crear el usuario. RECORDAR CAMBIARLO TRAS CREARLO

    clean_orphaned_files()

    return render_template('login.html', show_footer=True, current_user=None)
. . .
```

En el archivo, se debe modificar la llamada a la función `manage_data(0)`, cambiando el `0` por un `1`.

Tras eso, se podrá correr la aplicación y esta creará el administrador por defecto.

> **Nota**: se debe recordar volver a cambiar la llamada a la función `manage_data` una vez se cree el administrador por defecto ya que aparecerán errores en caso contrario.

## Notas finales
- Todos los servicios deben ejecutarse antes de iniciar la aplicación Flask.
- Si alguno de los contenedores se detiene, puede reiniciarse con `docker-compose up -d` desde su carpeta correspondiente.
- Para entornos de producción, se recomienda configurar certificados SSL y restringir el acceso externo a MySQL.
