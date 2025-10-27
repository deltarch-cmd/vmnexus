from app.extensions import db
from app.models.virtual_machine import VirtualMachine

from sqlalchemy.exc import SQLAlchemyError

class VirtualMachineException(Exception):
    pass

def __check_ids(**ids):
    for key, value in ids.items():
        if not isinstance(value, int):
            raise ValueError(f"El ID {key} debe ser un entero")

def create_virtual_machine(proxmox_id, name, user_id, asignatura_id, vnc_username=None, vnc_password=None, is_base=False, cloned_from=None):
    """Crea una máquina virtual

    :param proxmox_id: ID de la máquina virtual
    :type proxmox_id: int

    :param name: Nombre de la máquina virtual
    :type name: str

    :param user_id: ID del usuario dueño de la máquina virtual
    :type user_id: int

    :param asignatura_id: ID de la asignatura a la que pertenece la máquina virtual
    :type asignatura_id: int

    :param vnc_username: Nombre de usuario para acceder a la máquina virtual (default: None)
    :type vnc_username: str

    :param vnc_password: Contraseña para acceder a la máquina virtual (default: None)
    :type vnc_password: str

    :param is_base: Indica si la máquina virtual es base (default: False)
    :type is_base: bool

    :param cloned_from: ID de la máquina virtual de la que se clonó (default: None)
    :type cloned_from: int

    :return: La máquina virtual creada
    :rtype: VirtualMachine

    :raises ValueError: Si alguno de los IDs no es un entero
    :raises VirtualMachineException: Si un error al establecer la contraseña VNC
    :raises SQLAlchemyError: Si ocurre un error al crear la máquina virtual
    """
    __check_ids(proxmox_id=proxmox_id, user_id=user_id, asignatura_id=asignatura_id)
    try:
        virtual_machine = VirtualMachine(
            proxmox_id=proxmox_id,
            nombre=name,
            user_id=user_id,
            asignatura_id=asignatura_id,
            vnc_username=vnc_username,
            is_base_vm=is_base,
            cloned_from=cloned_from
        )

        if vnc_password and vnc_username:
            virtual_machine.set_vnc_password(vnc_password)
        else:
            virtual_machine.vnc_password = None

        if not virtual_machine.check_vnc_password(vnc_password):
            raise VirtualMachineException("Ha habido un error al crear la contraseña VNC")

        db.session.add(virtual_machine)
        db.session.commit()

    except SQLAlchemyError as e:
        db.session.rollback()
        raise SQLAlchemyError(f"Error al crear la máquina virtual: {e}") from e

    return virtual_machine

def get_all_virtual_machines():
    """Obtiene todas las máquinas virtuales

    :return: Lista de máquinas virtuales
    :rtype: list[VirtualMachine]
    """
    return VirtualMachine.query.all()

def get_all_virtual_machines_base():
    """Obtiene todas las máquinas virtuales *base*

    :return: Lista de máquinas virtuales base
    :rtype: list[VirtualMachine]
    """
    return VirtualMachine.query.filter_by(is_base_vm=True).all()

def get_virtual_machine_by_id(proxmox_id):
    """Obtiene una máquina virtual por su ID

    :param proxmox_id: ID de la máquina virtual
    :type proxmox_id: int

    :return: La máquina virtual encontrada
    :rtype: VirtualMachine

    :raises ValueError: Si proxmox_id no es un entero
    """
    if not isinstance(proxmox_id, int):
        raise ValueError("El ID de la máquina virtual debe ser un entero")

    return VirtualMachine.query.get(proxmox_id)

def get_virtual_machine_by_asignatura(asignatura_id):
    """Obtiene la máquina virtual base de una asignatura y todos sus clones

    :param asignatura_id: ID de la asignatura
    :type asignatura_id: int

    :return: Lista de máquinas virtuales
    :rtype: list[VirtualMachine]

    :raises ValueError: Si asignatura_id no es un entero
    """
    if not isinstance(asignatura_id, int):
        raise ValueError("El ID de la asignatura debe ser un entero")

    return VirtualMachine.query.filter_by(asignatura_id=asignatura_id).all()

def get_clones_of_virtual_machine(proxmox_id):
    """Obtiene todos los clones de una máquina virtual

    :param proxmox_id: ID de la máquina virtual
    :type proxmox_id: int

    :return: Lista de máquinas virtuales clonadas
    :rtype: list[VirtualMachine]

    :raises ValueError: Si proxmox_id no es un entero
    """
    if not isinstance(proxmox_id, int):
        raise ValueError("El ID de la máquina virtual debe ser un entero")

    return VirtualMachine.query.filter_by(cloned_from=proxmox_id).all()

def update_virtual_machine(proxmox_id, commit=True, **kwargs):
    """Actualiza una máquina virtual

    :param proxmod_id: ID de la máquina virtual
    :type proxmod_id: int

    :param kwargs: Campos a actualizar
    :type kwargs: dict

    :return: La máquina virtual actualizada
    :rtype: VirtualMachine

    :raises ValueError: Si proxmod_id no es un entero
    :raises VirtualMachineException: Si la máquina virtual no existe
    :raises SQLAlchemyError: Si ocurre un error al actualizar la máquina virtual
    """
    if not isinstance(proxmox_id, int):
        raise ValueError("El ID de la máquina virtual debe ser un entero")

    try:
        virtual_machine = VirtualMachine.query.get(proxmox_id)
        if not virtual_machine:
            raise VirtualMachineException("Virtual machine not found")

        for key, value in kwargs.items():
            setattr(virtual_machine, key, value)

        if commit:
            db.session.commit()

        return virtual_machine

    except SQLAlchemyError as e:
        db.session.rollback()
        raise SQLAlchemyError(f"Failed to update the virtual machine: {e}") from e

def bulk_update_virtual_machines(virtual_machines):
    """Actualiza varias máquinas virtuales

    :param virtual_machines: Lista de máquinas virtuales a actualizar. Cada máquina virtual es un diccionario con el campo obligatorio:
        - proxmox_id: ID de la máquina virtual
    :type virtual_machines: list[dict]

    :return: Lista de máquinas virtuales actualizadas
    :rtype: list[VirtualMachine]

    :raises VirtualMachineException: Si no se proporciona el ID de la máquina virtual o esta no existe
    :raises SQLAlchemyError: Si ocurre un error al actualizar las máquinas virtuales
    """
    try:
        updated_vms = []
        for vm in virtual_machines:
            proxmox_id = vm.pop('proxmox_id', None)
            if not proxmox_id:
                raise VirtualMachineException("Cada máquina virtual debe tener un ID")

            virtual_machine = VirtualMachine.query.get(proxmox_id)
            if not virtual_machine:
                raise VirtualMachineException(f"Máquina virtual con ID {proxmox_id} no encontrada")

            for key, value in vm.items():
                setattr(virtual_machine, key, value)

            updated_vms.append(virtual_machine)

        db.session.commit()
        return updated_vms

    except SQLAlchemyError as e:
        db.session.rollback()
        raise SQLAlchemyError(f"Error al actualizar las máquinas virtuales: {e}") from e

def delete_virtual_machine(proxmox_id):
    """Elimina una máquina virtual de la base de datos

    :param proxmox_id: ID de la máquina virtual
    :type proxmox_id: str

    :return: La máquina virtual eliminada
    :rtype: VirtualMachine

    :raises ValueError: Si proxmox_id no es un entero
    :raises VirtualMachineException: Si la máquina virtual no existe
    :raises SQLAlchemyError: Si ocurre un error al eliminar la máquina virtual
    """
    if not isinstance(proxmox_id, int):
        raise ValueError("El ID de la máquina virtual debe ser un entero")

    try:
        virtual_machine = VirtualMachine.query.get(proxmox_id)
        if not virtual_machine:
            raise VirtualMachineException("Máquina virtual no encontrada")

        db.session.delete(virtual_machine)
        db.session.commit()
        return virtual_machine

    except SQLAlchemyError as e:
        db.session.rollback()
        raise SQLAlchemyError(f"Error al eliminar la máquina virtual: {e}") from e
