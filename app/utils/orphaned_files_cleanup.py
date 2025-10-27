import os, logging
from flask import current_app
from app.controllers import laboratorio_controller

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_orphaned_files():
    """
    Elimina los archivos PDF que no están asociados a ningún laboratorio en la base de datos

    :raises Exception: Si ocurre un error al obtener los laboratorios
    :raises OSError: Si ocurre un error al eliminar un archivo
    """
    labs_list = laboratorio_controller.get_all_laboratorios()
    if labs_list is None:
        raise Exception("Error al obtener los laboratorios")

    labs_clean_list = list(filter(lambda lab: lab.pdf_url is not None, labs_list))
    labs_pdf_list = list(map(lambda lab: lab.pdf_url.split('/')[-1], labs_clean_list))

    upload_dir = current_app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_dir):
        logger.warning(f"Upload directory '{upload_dir}' not found")
        return

    for file in os.listdir(upload_dir):
        if file in labs_pdf_list:
            continue

        path_to_file = f"{upload_dir}/{file}" 
        if os.path.exists(path_to_file):
            try:
                os.remove(path_to_file)
                logger.info(f"File '{path_to_file}' deleted gracefully")

            except OSError as e:
                raise OSError(f"Error al eliminar el archivo '{path_to_file}': {e}") from e
        else:
            logger.warning(f"File '{path_to_file}' not found")
