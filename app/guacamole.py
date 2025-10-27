import json, logging, requests

# Import the correct config file
from app.config import GuacamoleConfig
# from app.configUni import GuacamoleConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GuacamoleError(Exception):
    pass

def get_guacamole_token():
    """
    Obtiene un token para autenticar con Guacamole

    :return: El token para autenticar con Guacamole
    :rtype: str

    :raises GuacamoleError: Si la petición falla
    """
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    payload = {
        "username": GuacamoleConfig.USER,
        "password": GuacamoleConfig.PASSWORD,
    }

    response = requests.post(f"{GuacamoleConfig.BASE_URL}/api/tokens", headers=headers, data=payload, verify=False)

    if response.status_code != 200:
        raise GuacamoleError("Failed to authenticate with Guacamole.", response.status_code, response.text)

    return response.json().get('authToken')

# Functions to read data from Guacamole instead of writing
def get_guacamole_connections(token):
    """
    Obtiene todas las conexiones de Guacamole

    :param token: El token para autenticar con Guacamole
    :type token: str

    :return: La lista de conexiones en formato JSON
    :rtype: dict

    :raises GuacamoleError: Si la petición falla
    """
    url = f"{GuacamoleConfig.BASE_URL}/api/session/data/{GuacamoleConfig.DATABASE_TYPE}/connections"
    headers = {
        'Guacamole-Token': token,
        'Content-Type': 'application/json'
    }

    response = requests.get(url, headers=headers, verify=False)
    if response.status_code != 200:
        raise GuacamoleError("Failed to get Guacamole connections.", response.status_code, response.text)

    return response.json()

# UNUSED
def get_guacamole_users(token):
    """
    Obtiene todos los usuarios de Guacamole

    :param token: El token para autenticar con Guacamole
    :type token: str

    :return: La lista de usuarios en formato JSON
    :rtype: dict

    :raises GuacamoleError: Si la petición falla
    """
    url = f"{GuacamoleConfig.BASE_URL}/api/session/data/{GuacamoleConfig.DATABASE_TYPE}/users"
    headers = {
        'Guacamole-Token': token,
        'Content-Type': 'application/json'
    }

    response = requests.get(url, headers=headers, verify=False)
    if response.status_code != 200:
        raise GuacamoleError("Failed to get Guacamole users.", response.status_code, response.text)

    return response.json()

def create_guacamole_connection(
    token, virtual_machine_ip, connection_name,
    virtual_machine_username, connection_password,
    type_of_connection="vnc", connection_port=5901
):
    """
    Crea una nueva conexión en Guacamole

    Este método permite crear una nueva conexión en Guacamole. Soporta el uso de 
    diferentes protocolos de conexión, pero actualmente asume que se usará VNC.
    
    :param token: Token para autenticar con Guacamole
    :type token: str

    :param virtual_machine_ip: La dirección IP de la máquina virtual
    :type virtual_machine_ip: str

    :param connection_name: El nombre de la conexión a crear
    :type connection_name: str

    :param virtual_machine_username: El nombre de usuario para acceder a la máquina virtual
    :type virtual_machine_username: str

    :param virtual_machine_password: La contraseña del protocolo de conexión
    :type virtual_machine_password: str

    :param type_of_connection: El tipo de conexión a crear (default: "vnc")
    :type type_of_connection: str

    :param connection_port: El puerto de la conexión (default: 5901)
    :type connection_port: int

    :return: El ID de la conexión creada
    :rtype: str

    :raises GuacamoleError: Si la petición falla
    """

    url = f"{GuacamoleConfig.BASE_URL}/api/session/data/{GuacamoleConfig.DATABASE_TYPE}/connections"
    headers = {
        'Guacamole-Token': token,
        'Content-Type': 'application/json'
    }

    # VNC Connection
    payload = {
        "name": connection_name,
        "parentIdentifier": "ROOT",
        "protocol": type_of_connection,
        "parameters": {
            "hostname": virtual_machine_ip,
            "port": str(connection_port),
            "username": virtual_machine_username,
            "password": connection_password
        },
        "attributes": {
            "maxConnection": "",
            "weight": "",
            "guacd-port": "4822",
            "guacd-hostname": "guacd"
        }
    }

    response = requests.post(url, headers=headers, json=payload, verify=False)
    if response.status_code not in [200, 201]:
        raise GuacamoleError(
            f"Failed to create Guacamole connection. Status code: {response.status_code}. Response: {response.text}, URL: {url}"
        )

    connection_id = response.json().get('identifier')
    if connection_id is None:
        raise GuacamoleError("Failed to get the connection ID.")

    return connection_id # This is the connection ID for the new session

# UNUSED
def check_connection_exists(token, connection_name):
    """Comprueba si una conexión ya existe en Guacamole

    :param token: El token para autenticar con Guacamole
    :type token: str

    :param connection_name: El nombre de la conexión a buscar
    :type connection_name: str

    :return: El ID de la conexión si existe, None si no
    :rtype: str

    :raises GuacamoleError: Si la petición falla
    """
    connections = get_guacamole_connections(token)
    for conn_number in connections:
        conn = connections[conn_number]
        if conn['name'] == connection_name:
            return conn['identifier']

    return None

def test_guacamole_connection(token, connection_id):
    """
    Comprueba si una conexión de Guacamole existe

    :param token: El token para autenticar con Guacamole
    :type token: str

    :param connection_id: El ID de la conexión a probar
    :type connection_id: str

    :return: True si la conexión existe, False si no
, 204]
    :raises GuacamoleError: Si la petición falla
    """
    connections = get_guacamole_connections(token)
    for conn_number in connections:
        conn = connections[conn_number]
        if conn['identifier'] == str(connection_id):
            logger.info(f"Connection {connection_id} exists.")
            return True

    return False

def delete_guacamole_connection(token, connection_id):
    """
    Borra una conexión de Guacamole

    :param connection_id: El ID de la conexión a borrar
    :type connection_id: str

    :raises GuacamoleError: Si la petición falla
    """
    url = f"{GuacamoleConfig.BASE_URL}/api/session/data/{GuacamoleConfig.DATABASE_TYPE}/connections/{connection_id}"

    headers = {
        'Guacamole-Token': token,
        'Content-Type': 'application/json'
    }
    response = requests.delete(url, headers=headers, verify=False)

    if response.status_code not in [200, 204]:
        raise GuacamoleError(
            f"Failed to delete Guacamole connection. Status code: {response.status_code}. Response: {response.text}, URL: {url}"
        )

