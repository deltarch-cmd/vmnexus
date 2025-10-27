import atexit, logging
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
# from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore # To store jobs in the database

from app.utils.orphaned_files_cleanup import clean_orphaned_files

from app.controllers import horario_controller, asignatura_controller, virtual_machines_controller
import app.proxmox as proxmox

scheduler = BackgroundScheduler()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_scheduler():
    if not scheduler.running:
        scheduler.start()

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")

atexit.register(stop_scheduler) # Se asegura de que el scheduler se detenga cuando la aplicación se detenga

def __try_remove_job(job_id, retries=3):
    """Intenta eliminar un trabajo del scheduler

    :param job_id: ID del trabajo a eliminar
    :type job_id: str

    :param retries: Número de intentos (default: 3)
    :type retries: int
    """
    for attempt in range (1, retries + 1):
        try:
            scheduler.remove_job(job_id)
            break
        except Exception as e:
            logger.error(f"Error removing job '{job_id}' (attempt {attempt}/{retries}): {e}")
            if attempt == retries:
                logger.error(f"Job '{job_id}' could not be removed after {retries} retries")

def manage_schedule_times(start_time, end_time, buffer=10):
    """Maneja los tiempos de inicio y fin de las tareas programadas

    :param start_time: Hora de inicio de la tarea
    :type start_time: str

    :param end_time: Hora de fin de la tarea
    :type end_time: str

    :param buffer: Tiempo de buffer en minutos (default: 10). Se añade antes y después de la tarea
    :type buffer: int

    :return: Hora de inicio y fin de la tarea con buffer
    :rtype: tuple (datetime, datetime)
    """
    start_hour, start_minute = map(int, start_time.split(':'))
    end_hour, end_minute = map(int, end_time.split(':'))

    # Datetime objects for time management
    start_time = datetime(2025, 1, 1, start_hour, start_minute)
    end_time = datetime(2025, 1, 1, end_hour, end_minute)

    # Buffering
    start_time_buffer = start_time - timedelta(minutes=buffer)
    end_time_buffer = end_time + timedelta(minutes=buffer)

    return start_time_buffer, end_time_buffer

def check_machines_state(vm_id_batch, day, start_time, end_time):
    """Verifica el estado de las máquinas virtuales antes de programar las tareas

    :param vm_id_batch: Batch de IDs de máquinas virtuales
    :type vm_id_batch: list

    :param day: Día de la semana
    :type day: str

    :param start_time: Hora de inicio de la tarea
    :type start_time: datetime

    :param end_time: Hora de fin de la tarea
    :type end_time: datetime
    """
    day_to_int = {
        "mon": 0,
        "tue": 1,
        "wed": 2,
        "thu": 3,
        "fri": 4,
        "sat": 5,
        "sun": 6
    }
    # Check if the machines should already be running
    int_day = day_to_int[day]
    current_day = datetime.now().weekday()
    current_time = datetime.now().time()

    if current_day == int_day and current_time >= start_time.time() and current_time <= end_time.time():
        proxmox.batch_start_virtual_machines(vm_id_batch)

    if current_day == int_day and current_time >= end_time.time():
        proxmox.batch_stop_virtual_machines(vm_id_batch)

def schedule_virtual_machine_tasks(asignatura_id, vm_id_batch, schedule_data):
    """
    Inicializa las tareas de programación de máquinas virtuales para los horarios de una asignatura

    :param asignatura_id: ID de la asignatura
    :type asignatura_id: int

    :param vm_batch: Batch de máquinas virtuales
    :type vm_batch: list

    :param schedule: Horario de las tareas
    :type schedule: dict

    :raises Exception: Si ocurre un error al programar las tareas
    """
    day = schedule_data["day"]
    start_time = schedule_data["hora_inicio"].isoformat(timespec="minutes")
    end_time = schedule_data["hora_fin"].isoformat(timespec="minutes")

    start_time_buffer, end_time_buffer = manage_schedule_times(start_time, end_time)

    start_job_id = f"start_vm_job_{asignatura_id}_{day}_{start_time_buffer.hour}_{start_time_buffer.minute}"
    end_job_id = f"stop_vm_job_{asignatura_id}_{day}_{end_time_buffer.hour}_{end_time_buffer.minute}"

    logger.info(f"Programando tareas para la asignatura {asignatura_id} en el día {day} a las {start_time_buffer} y {end_time_buffer}")

    logger.info(f"Time buffer: {datetime.now().isoweekday()}")
    logger.info(f"Time end buffer: {end_time_buffer.time()}")

    # Check if the machines should already be running
    check_machines_state(vm_id_batch, day, start_time_buffer, end_time_buffer)

    # Add jobs to the scheduler
    try:
        # Start job
        scheduler.add_job(
            proxmox.batch_start_virtual_machines,
            'cron',
            day_of_week=day,
            hour=start_time_buffer.hour,
            minute=start_time_buffer.minute,
            args=[vm_id_batch],
            id=start_job_id
        )
        # End job
        scheduler.add_job(
            proxmox.batch_stop_virtual_machines,
            'cron',
            day_of_week=day,
            hour=end_time_buffer.hour,
            minute=end_time_buffer.minute,
            args=[vm_id_batch],
            id=end_job_id
        )
    except Exception as e:
        logger.error(f"Error al programar las tareas: {e}")
        raise e

def reschedule_virtual_machines_tasks(asignatura_id):
    """
    Reprograma las tareas de programación de máquinas virtuales para los horarios de una asignatura

    :param asignatura_id: ID de la asignatura
    :type asignatura_id: int
    """
    for job in scheduler.get_jobs():
        if job.id.startswith(f"start_vm_job_{asignatura_id}") or job.id.startswith(f"stop_vm_job_{asignatura_id}"):
            __try_remove_job(job.id)

    # Se obtienen los horarios de las asignaturas
    try:
        horarios = horario_controller.get_all_horarios_by_asignatura(asignatura_id)
    except ValueError as e:
        logger.error(f"Error al obtener los horarios de la asignatura {asignatura_id}: {e}")
        return

    # Virtual machine de la asignatura
    try:
        virtual_machines = virtual_machines_controller.get_virtual_machine_by_asignatura(asignatura_id)
    except ValueError as e:
        logger.error(f"Error al obtener la máquina virtual de la asignatura {asignatura_id}: {e}")
        return

    if not horarios or not virtual_machines:
        return

    # Lista de IDs de máquinas virtuales sin la máquina base
    clones_list = [vm.proxmox_id for vm in virtual_machines if not vm.is_base_vm]
    for horario in horarios:
        schedule_data = {
            "day": horario.dia,
            "hora_inicio": horario.hora_inicio,
            "hora_fin": horario.hora_fin
        }
        try:
            schedule_virtual_machine_tasks(asignatura_id, clones_list, schedule_data)
        except Exception as e:
            logger.error(f"Error al programar las tareas para la asignatura {asignatura_id}: {e}")

def __virtual_machine_tasks():
    """Inicializa todos los jobs para todas las asignaturas"""
    asignaturas = asignatura_controller.get_all_asignaturas()
    for a in asignaturas:
        reschedule_virtual_machines_tasks(a.id)

def __orphaned_files_cleanup():
    """Limpieza de archivos huérfanos"""
    scheduler.add_job(
        clean_orphaned_files,
        'interval',
        hours=24,
        id="orphaned_files_cleanup"
    )

def initialize_tasks():
    """Inicializa las tareas programadas"""
    start_scheduler()

    # Se inicializan las tareas de programación de máquinas virtuales
    __virtual_machine_tasks()

    # Se inicializa la tarea de limpieza de archivos huérfanos
    __orphaned_files_cleanup()

    logger.info("\n\nTareas programadas inicializadas\n")
