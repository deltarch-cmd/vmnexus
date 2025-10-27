import time, logging, json
from proxmoxer import ProxmoxAPI

# Import the appropiate configuration
from app.config import Config
# from app.configUni import Config

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the Proxmox node to connect to
proxmox_node = Config.PROXMOX.NODE_NAME

class ProxmoxConnection:
    """
    Clase Singleton para manejar la conexión con Proxmox

    Se encarga de inicializar la conexión con Proxmox y de devolver la instancia de la conexión,
    asegurando que solo se inicialice una vez.
    """
    _instance = None # holds the singleton instance
    _is_initialized = False # flag to check if the connection has been initialized

    def __new__(cls):
        # Check if the singleton instance already exists
        if cls._instance is None:
            # If not, create a new instance
            cls._instance = super(ProxmoxConnection, cls).__new__(cls)
            cls._instance._initialize_connection()
        return cls._instance

    def _initialize_connection(self):
        # Only initializes the connection once
        try:
            self.proxmox = ProxmoxAPI(
                Config.PROXMOX.HOST,
                port=Config.PROXMOX.PORT,
                user=Config.PROXMOX.ROOT_USER,
                password=Config.PROXMOX.PASSWORD,
                verify_ssl=False
            )
            self._is_initialized = True
        except Exception as e:
            self.proxmox = None
            self._is_initialized = False
            self.error = str(e)
            logger.error(f"Failed to initialize the Proxmox connection: {e}")

    def get_connection(self):
        if not self._is_initialized:
            self._initialize_connection()
        return self.proxmox

    def get_error(self):
        return getattr(self, 'error', None)

class ProxmoxError(Exception):
    pass

def wait_for_task(task_upid, timeout=60, interval=5):
    """
    Función de ayuda para esperar a que una tarea de Proxmox termine

    :param task_upid: El UPID de la tarea a esperar
    :type task_upid: str

    :param timeout: El tiempo máximo para esperar a que la tarea termine (default: 60 segundos)
    :type timeout: int

    :param interval: El intervalo para comprobar si la tarea ha terminado (default: 5 segundos)
    :type interval: int

    :raises TimeoutError: Si la tarea no termina en el tiempo dado
    :raises ProxmoxError: Si la tarea falla al ejecutarse
    """
    proxmox = get_proxmox_conn()

    logger.info(f"Waiting for task {task_upid} to finish...")

    # Wait until the task is finished
    elapsed_time = 0
    while elapsed_time < timeout:
        task_status = proxmox.nodes(proxmox_node).tasks(task_upid).status.get()
        if task_status and task_status['status'] == 'stopped':
            logger.info(f"Task {task_upid} finished with status: {task_status['exitstatus']}")
            return

        elif task_status and task_status['status'] in ['failed']:
            raise ProxmoxError(f"La tarea {task_upid} ha fallado")

        time.sleep(interval)
        elapsed_time += interval

    raise TimeoutError(f"La tarea {task_upid} no terminó en {timeout} segundos")

# UNUSED
def get_proxmox_credentials():
    """Obtiene las credenciales para acceder a Proxmox

    :return: Las credenciales para acceder a Proxmox
    :rtype: dict
    """

    # Ask for the credentials for the Proxmox API
    proxmox_host_ip = input("Enter the Proxmox server IP: ")

    # Credentials to access the server
    proxmox_user = input("Enter the Proxmox username: ")
    proxmox_pass = input("Enter the Proxmox password: ")

    return {
        "host_ip": proxmox_host_ip,
        "user": proxmox_user,
        "pass": proxmox_pass,
    }

# UNUSED
def init_proxmox():
    """Inicializa la conexión con Proxmox

    :return: La conexión con Proxmox
    :rtype: ProxmoxAPI

    :raises ConnectionError: Si no se puede conectar con Proxmox
    """
    proxmox_connection = ProxmoxAPI(
        Config.PROXMOX.HOST,
        port=Config.PROXMOX.PORT,
        user=Config.PROXMOX.ROOT_USER,
        password=Config.PROXMOX.PASSWORD,
        verify_ssl=False
    )
    return proxmox_connection

def get_proxmox_conn():
    """Obtiene la conexión con Proxmox

    :return: La conexión con Proxmox
    :rtype: ProxmoxAPI

    :raises ConnectionError: Si no se puede conectar con Proxmox
    """
    proxmox_connection_instance = ProxmoxConnection()
    proxmox = proxmox_connection_instance.get_connection()

    if not proxmox:
        raise ConnectionError(f"Se ha fallado al conectar con Proxmox: {proxmox_connection_instance.get_error()}")

    return proxmox

def get_node_status():
    """
    Obtiene el estado del nodo de Proxmox.

    Esta función es utilizada en las pruebas de rendimiento para comprobar los recursos del nodo durante ciertas operaciones.
    """
    proxmox = get_proxmox_conn()
    node_status = proxmox.nodes(proxmox_node).status.get()

    if not node_status:
        raise ProxmoxError("No se han podido obtener los datos del nodo")

    data = {
        'cpu': node_status['cpu'],
        'memory': node_status['memory'],
        'uptime': node_status['uptime'],
    }

    return data

# Como proxmox devuelve muchos datos innecesarios, se usa este método para devolver solo aquellos datos útiles para el frontend
def get_all_vms_serialized():
    """
    Obtiene una lista de las VMs en Proxmox con los datos necesarios para el frontend

    :return: La lista de VMs serializadas
    :rtype: list

    :raises ConnectionError: Si no se puede conectar con Proxmox
    :raises ProxmoxError: Si no se pueden obtener las VMs de Proxmox
    """
    try:
        proxmox = get_proxmox_conn()
        vms = proxmox.nodes(proxmox_node).qemu.get()

        if not vms:
            return []

        vms_serialized = [
            {
                'id': vm['vmid'],
                'name': vm['name'],
                'status': vm['status'],
                'uptime': vm['uptime'],
                'maxdisk': vm['maxdisk'],
                'maxmem': vm['maxmem']
                # 'ip': vm_ip if vm['status'] == 'running' else None
            }
            for vm in vms
        ]

    except ConnectionError as e:
        logger.error(f"Failed to connect to Proxmox: {e}")
        raise ConnectionError(f"No se ha podido conectar con Proxmox: {e}")

    except Exception as e:
        logger.error(f"Failed to retrieve the VMs from Proxmox: {e}")
        raise ProxmoxError(f"Se ha fallado al obtener las VMs de Proxmox: {e}")

    return vms_serialized

def get_vm_serialized(vmid):
    """
    Obtiene los datos de una VM en Proxmox con los datos necesarios para el frontend

    :param vmid: ID de la VM a obtener
    :type vmid: str

    :return: Los datos de la VM serializados o None si no se encuentra
    :rtype: dict

    :raises ProxmoxError: Si no se puede obtener la VM de Proxmox
    """
    vm = get_vm_by_id(vmid)

    if not vm:
        return None

    vm_serialized = {
        'id': vm['vmid'],
        'name': vm['name'],
        'status': vm['status'],
        'uptime': vm['uptime'],
        'maxdisk': vm['maxdisk'],
        'maxmem': vm['maxmem']
    }
    return vm_serialized

def get_vm_by_id(vmid):
    """
    Obtiene una VM en Proxmox por su ID

    :param vmid: ID de la VM a obtener
    :type vmid: str

    :return: Los datos de la VM o None si no se encuentra
    :rtype: dict

    :raises ProxmoxError: Si no se puede obtener la VM de Proxmox
    """
    try:
        proxmox = get_proxmox_conn()
        return proxmox.nodes(proxmox_node).qemu(vmid).status.current.get()
    except Exception as e:
        raise ProxmoxError(f"Se ha fallado al obtener la VM {vmid}: {e}")

def get_virtual_machines_ip(list_vmid, timeout=60, interval=5, batch_size=3, off_when_done=True):
    """Obtiene la dirección IP de un conjunto de máquinas virtuales en Proxmox

    Este método obtiene la primera dirección IPv4 de las máquinas virtuales en 
    la lista.

    Batch_size determina el número máximo de máquinas virtuales que estarán 
    activas al mismo tiempo.

    NOTA: Las máquinas virtuales encendidas por este proceso se apagarán al 
    finalizar en función del valor de off_when_done. Si la máquina virtual ya
    estaba encendida, no se apagará.

    :param list_vmid: Lista de IDs de las VMs a obtener la dirección IP
    :type list_vmid: list

    :param timeout: El tiempo máximo para esperar a que las VMs se inicien (default: 60 segundos)
    :type timeout: int

    :param interval: El intervalo para comprobar si las VMs se han iniciado (default: 5 segundos)
    :type interval: int

    :param batch_size: El tamaño del lote de VMs a obtener la dirección IP en paralelo (default: 3)
    :type batch_size: int

    :param off_when_done: Apagar las VMs cuando se haya obtenido la dirección IP (default: True)

    :return: Un diccionario con las direcciones IP de las vm
    :rtype: dict

    :raises ConnectionError: Si no se puede conectar con Proxmox
    :raises TimeoutError: Si alguna VM no se inicia en el tiempo dado
    :raises ProxmoxError: Si no se puede obtener la dirección IP de alguna VM
    """
    started_vms = []
    ip_addresses = {}
    try:
        proxmox = get_proxmox_conn()
        elapsed_time = 0

        # Start the VMs in batches
        for i in range(0, len(list_vmid), batch_size):
            batch = list_vmid[i:i + batch_size]
            logger.info(f"Starting batch: {batch}")

            # Start the VMs in parallel
            for vm_id in batch:
                try:
                    status = proxmox.nodes(proxmox_node).qemu(vm_id).status.current.get()
                    if status and status['status'] == 'running':
                        logger.info(f"VM {vm_id} is already running")
                        continue

                    logger.info(f"Starting VM {vm_id}...")
                    proxmox.nodes(proxmox_node).qemu(vm_id).status.start.post()
                    started_vms.append(vm_id)
                except Exception as e:
                    logger.error(f"Failed to start VM {vm_id}: {e}")
                    continue

            # Wait for the VMs to start
            elapsed_time = 0
            while elapsed_time < timeout:
                try:
                    statuses = [
                        proxmox.nodes(proxmox_node).qemu(vm_id).status.current.get()
                        for vm_id in batch
                    ]
                    if all(status and status['status'] == 'running' for status in statuses):
                        logger.info(f"Batch {batch} started successfully")
                        break

                except Exception as e:
                    logger.error(f"Failed to get VM status: {e}")

                time.sleep(interval)
                elapsed_time += interval
            
            if elapsed_time >= timeout:
                logger.error(f"Failed to start batch {batch} in {timeout} seconds")
                raise TimeoutError(f"Se ha fallado al iniciar el lote {batch} en {timeout} segundos")

            # En este punto las VMs del batch ya están encendidas
            for vm_id in batch:
                try:
                    ip_addr = get_vm_ip_addr(vm_id, 20, 2) # Esperar 20 segundos y comprobar cada 2 segundos. Se usan valores más bajos porque las VMs deberían ya estar iniciándose

                except (Exception, TimeoutError) as e:
                    logger.error(f"Failed to get IP address for VM {vm_id}: {e}")
                    ip_addr = None

                ip_addresses[vm_id] = ip_addr

            if off_when_done:
                for vm_id in started_vms:
                    stop_vm(vm_id)
                started_vms = [] # Reset the list of started VMs

    except Exception as e:
        logger.error(f"Ha ocurrido un error inesperado: {e}")
        raise e

    return ip_addresses

def get_vm_ip_addr(vmid, timeout=60, interval=5):
    """
    Obtiene la primera dirección IPv4 de una VM en Proxmox

    El método iniciará la máquina si es necesario y, en caso de que lo haga,
    la apagará al finalizar.

    :param vmid: ID de la VM a obtener la dirección IP
    :type vmid: str

    :param timeout: El tiempo máximo para esperar a que la VM se inicie (default: 60 segundos)
    :type timeout: int

    :param interval: El intervalo para comprobar si la VM se ha iniciado (default: 5 segundos)
    :type interval: int

    :return: La dirección IPv4 de la VM
    :rtype: str

    :raises ConnectionError: Si no se puede conectar con Proxmox
    :raises TimeoutError: Si la VM no se inicia en el tiempo dado
    :raises ProxmoxError: Si no se puede iniciar la VM u obtener la dirección IP
    :raises Exception: Si ocurre un error inesperado
    """
    started = False
    try:
        proxmox = get_proxmox_conn()
        elapsed_time = 0
        ip_address = None

        # Start the VM if it's not running
        vm_status = proxmox.nodes(proxmox_node).qemu(vmid).status.current.get()
        if vm_status and vm_status['status'] != 'running':
            try:
                logger.info(f"Starting VM {vmid}...")
                proxmox.nodes(proxmox_node).qemu(vmid).status.start.post() # Start the VM
                started = True
            except Exception as e:
                raise ProxmoxError(f"Ha habido un error al iniciar la VM {vmid}: {e}")
        else:
            logger.info(f"VM {vmid} is already running")

        logger.info(f"Trying to get IP address for VM {vmid}...")
        while elapsed_time < timeout:
            try:
                vm_agent_info = proxmox.nodes(proxmox_node).qemu(vmid).agent.get('network-get-interfaces')
                if vm_agent_info:
                    for interface in vm_agent_info['result']:
                        if interface['name'] != 'lo':
                            for ip_info in interface.get('ip-addresses', []):
                                if ip_info['ip-address-type'] == 'ipv4':
                                    ip_address = ip_info['ip-address']

                    if ip_address:
                        logger.info(f"IP address for VM {vmid}: {ip_address}")
                        break

            except Exception as e:
                if elapsed_time + interval >= timeout:
                    logger.warning(f"Timeout is near. Failed to get IP address for VM {vmid}: {e}")

            time.sleep(interval)
            elapsed_time += interval

        if elapsed_time >= timeout:
            raise TimeoutError(f"No se ha podido obtener la dirección IP de la VM {vmid} en {timeout} segundos")

        if not ip_address:
            logger.error(f"Failed to get IP address for VM {vmid}")
            raise ProxmoxError(f"Ha habido un error al obtener la dirección IP de la VM {vmid}")

    except Exception as e:
        logger.error(f"Ha ocurrido un error inesperado: {e}")
        raise

    finally:
        if started:
            stop_vm(vmid)

    return ip_address

# UNUSED
def create_vm(vmid, vm_name, vm_os, vm_cores, vm_memory, vm_disk_size, vm_iso):
    """
    Crea una VM en Proxmox

    :param vmid: El ID de la VM
    :type vmid: str

    :param vm_name: El nombre de la VM
    :type vm_name: str

    :param vm_os: El sistema operativo de la VM
    :type vm_os: str

    :param vm_cores: El número de cores para la VM
    :type vm_cores: int

    :param vm_memory: La memoria RAM (MB) para la VM
    :type vm_memory: int

    :param vm_disk_size: El tamaño del disco (GB) para la VM
    :type vm_disk_size: int

    :param vm_iso: La ISO para instalar el sistema operativo
    :type vm_iso: str

    :raises ConnectionError: Si no se puede conectar con Proxmox
    :raises ProxmoxError: Si no se puede crear la VM
    """
    proxmox = get_proxmox_conn()

    # Create the VM
    try:
        proxmox.nodes(proxmox_node).qemu.create(
            vmid=vmid,
            name=vm_name,
            ostype=vm_os,
            sockets=1,
            cores=vm_cores,
            memory=vm_memory,
            disksize=vm_disk_size,
            net0='virtio,bridge=vmbr0',
            ide2=f"{vm_iso},media=cdrom",
            boot="cdn"
        )
    except Exception as e:
        logger.error(f"Failed to create VM {vmid}: {e}")
        raise ProxmoxError(f"Ha habido un error al crear la VM {vmid}: {e}")

def batch_start_virtual_machines(vm_id_batch, timeout=60, check_interval=5, batch_size=2):
    """
    Inicia un conjunto de VMs en Proxmox en lotes

    :param vm_id_batch: Lista de IDs de las VMs a iniciar
    :type vm_id_batch: list[int]

    :param timeout: El tiempo máximo para esperar a que las VMs se inicien (default: 60 segundos)
    :type timeout: int

    :param check_interval: El intervalo (segundos) para comprobar si las VMs se han iniciado (default: 5 segundos)
    :type check_interval: int

    :param batch_size: El tamaño del lote de VMs a iniciar (default: 2)
    :type batch_size: int

    :raises ConnectionError: Si no se puede conectar con Proxmox
    :raises ProxmoxError: Si no se pueden iniciar las VMs
    """
    proxmox = get_proxmox_conn()

    # Split the VMs in batches
    for i in range(0, len(vm_id_batch), batch_size):
        batch = vm_id_batch[i:i + batch_size]
        logger.info(f"Starting batch: {batch}")

        # Start the VMs in parallel
        for vm_id in batch:
            try:
                status = proxmox.nodes(proxmox_node).qemu(vm_id).status.current.get()
                if status and status['status'] == 'running':
                    logger.info(f"VM {vm_id} is already running")
                    continue

                logger.info(f"Starting VM {vm_id}...")
                proxmox.nodes(proxmox_node).qemu(vm_id).status.start.post()
            except Exception as e:
                logger.error(f"Failed to start VM {vm_id}: {e}")
                continue

        # Wait for the VMs to start
        elapsed_time = 0
        while elapsed_time < timeout:
            try:
                statuses = [
                    proxmox.nodes(proxmox_node).qemu(vm_id).status.current.get()
                    for vm_id in batch
                ]
                if all(status and status['status'] == 'running' for status in statuses):
                    logger.info(f"Batch {batch} started successfully")
                    break

            except Exception as e:
                logger.error(f"Failed to get VM status: {e}")

            time.sleep(check_interval)
            elapsed_time += check_interval
        
        if elapsed_time >= timeout:
            logger.error(f"Failed to start batch {batch} in {timeout} seconds")
            raise TimeoutError(f"Se ha fallado al iniciar el lote {batch} en {timeout} segundos")

    logger.info("All VMs started successfully")

def stop_vm(vmid, timeout=60, interval=5):
    """
    Apaga una VM en Proxmox y espera a que el proceso termine

    :param vmid: El ID de la VM a apagar
    :type vmid: str

    :param timeout: El tiempo máximo para esperar a que la VM se apague (default: 60 segundos)
    :type timeout: int

    :param interval: El intervalo para comprobar si la VM se ha apagado (default: 5 segundos)
    :type interval: int

    :raises ConnectionError: Si no se puede conectar con Proxmox
    :raises TimeoutError: Si la VM no se apaga en el tiempo dado
    """
    proxmox = get_proxmox_conn()
    proxmox.nodes(proxmox_node).qemu(vmid).status.stop.post()

    # Wait until the VM is stopped
    elapsed_time = 0
    vm_apagada = False
    while elapsed_time < timeout:
        vm_status = proxmox.nodes(proxmox_node).qemu(vmid).status.current.get()
        if vm_status and vm_status['status'] == 'stopped':
            vm_apagada = True
            break

        time.sleep(interval)
        elapsed_time += interval

    if not vm_apagada:
        raise TimeoutError(f"Failed to stop VM {vmid} in {timeout} seconds")

def batch_stop_virtual_machines(vm_id_batch, batch_size=2, check_interval=5, timeout=60):
    """
    Apaga un conjunto de VMs en Proxmox

    Las máquinas virtuales se apagan en lotes de 2 para evitar sobrecargar el servidor.

    :param vm_id_batch: Lista de IDs de las VMs a apagar
    :type vm_id_batch: list[int]

    :param batch_size: El tamaño del lote de VMs a apagar (default: 2)
    :type batch_size: int

    :param check_interval: El intervalo (segundos) para comprobar si las VMs se han apagado (default: 5 segundos)
    :type check_interval: int

    :param timeout: El tiempo máximo (segundos) para esperar a que las VMs se apaguen (default: 60 segundos)
    :type timeout: int

    :raises ConnectionError: Si no se puede conectar con Proxmox
    :raises ProxmoxError: Si no se pueden apagar las VMs
    """
    proxmox = get_proxmox_conn()

    # Split the VMs in batches
    logger.info(f"Stopping VMs in batches of {batch_size}")
    for i in range(0, len(vm_id_batch), batch_size):
        batch = vm_id_batch[i:i + batch_size]

        # Stop the VMs in parallel
        for vm_id in batch:
            try:
                status = proxmox.nodes(proxmox_node).qemu(vm_id).status.current.get()
                if status and status['status'] == 'stopped':
                    logger.info(f"VM {vm_id} is already stopped")
                    continue

                logger.info(f"Stopping VM {vm_id}...")
                proxmox.nodes(proxmox_node).qemu(vm_id).status.stop.post()
            except Exception as e:
                logger.error(f"Failed to stop VM {vm_id}: {e}")
                continue # Continue with the next VM

        # Wait for the VMs to stop
        elapsed_time = 0
        while elapsed_time < timeout:
            try:
                statuses = [
                    proxmox.nodes(proxmox_node).qemu(vm_id).status.current.get()
                    for vm_id in batch
                ]
                if all(status and status['status'] == 'stopped' for status in statuses):
                    logger.info(f"Batch {batch} stopped successfully")
                    break

            except Exception as e:
                logger.error(f"Failed to get VM status: {e}")

            time.sleep(check_interval)
            elapsed_time += check_interval

        if elapsed_time >= timeout:
            logger.error(f"Failed to stop batch {batch} in {timeout} seconds")
            raise TimeoutError(f"Se ha fallado al apagar el lote {batch} en {timeout} segundos")

    logger.info("All VMs stopped successfully")

def clone_vm(vmid, base_vm_name, new_starting_id, number_of_clones=1, timeout=60, batch_size=2):
    """
    Clona una máquina virtual en Proxmox

    Los nuevos IDs comenzarán desde new_starting_id (inclusivo)
    Los clones se nombrarán como clone-{new_id}-{base_vm_name}.

    El método esperará a que todos los clones hayan terminado de crearse.

    :param vmid: ID de la VM a clonar
    :type vmid: str

    :param base_vm_name: Nombre base para los clones
    :type base_vm_name: str

    :param new_starting_id: ID inicial para los nuevos clones
    :type new_starting_id: int

    :param number_of_clones: Número de clones a crear (default: 1)
    :type number_of_clones: int

    :param timeout: Tiempo máximo (segundos) para esperar a que los clones se creen (default: 60 segundos)
    :type timeout: int

    :param batch_size: Tamaño del lote de clones a crear (default: 2)
    :type batch_size: int

    :raises ConnectionError: Si no se puede conectar con Proxmox
    :raises ProxmoxError: Si no se pueden clonar las VMs
    """
    proxmox = get_proxmox_conn()

    # First we make sure that the VM is stopped
    try:
        vm_status = proxmox.nodes(proxmox_node).qemu(vmid).status.current.get()
        if vm_status and vm_status['status'] == 'running':
            logger.info(f"Stopping VM {vmid} before cloning...")
            stop_vm(vmid)
    except Exception as e:
        logger.error(f"Failed to stop VM {vmid} before cloning: {e}")
        raise ProxmoxError(f"Ha habido un error al clonar la VM {vmid}: {e}")

    logger.info(f"Cloning VM {vmid} to {number_of_clones} new VMs...")
    clone_errors = []
    for batch_start in range(0, number_of_clones, batch_size):
        batch_end = min(batch_start + batch_size, number_of_clones)

        # Clone the VMs in parallel
        tasks = []
        for i in range(batch_start, batch_end):
            new_vmid = new_starting_id + i
            new_vm_name = f"clone-{new_vmid}-{base_vm_name}"

            try:
                task = proxmox.nodes(proxmox_node).qemu(vmid).clone.create(
                    newid=new_vmid,
                    name=new_vm_name
                )
                tasks.append(task)
            except Exception as e:
                clone_errors.append({"vmid": new_vmid, "name": new_vm_name, "error": str(e)})
                logger.error(f"Failed to clone VM {vmid} to {new_vm_name}: {e}")
                continue

        # Wait for the tasks to finish
        for task in tasks:
            wait_for_task(task, timeout)

    if clone_errors:
        logger.error(f"Failed to clone the following VMs: {json.dumps(clone_errors, indent=2)}")
        raise ProxmoxError(f"Ha habido un error al clonar las VMs: {json.dumps(clone_errors, indent=2)}")

    logger.info(f"VM {vmid} cloned successfully to {number_of_clones} new VMs")

def delete_vm(vmid):
    """
    Borra una VM en Proxmox

    :param vmid: ID de la VM a borrar
    :type vmid: str

    :raises ConnectionError: Si no se puede conectar con Proxmox
    :raises ProxmoxError: Si no se puede borrar la VM
    """
    proxmox = get_proxmox_conn()
    try:
        proxmox.nodes(proxmox_node).qemu(vmid).delete()
    except Exception as e:
        logger.error(f"Failed to delete VM {vmid}: {e}")
        raise ProxmoxError(f"Ha habido un error al borrar la VM {vmid}: {e}")
