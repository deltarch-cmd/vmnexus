from app.controllers import usuario_controller, asignatura_controller, laboratorio_controller, matricula_controller

# Create base data variables
def load_user_data():
    # user_email = 'user@example.com'
    # user_password = "user"

    admin_email = 'admin@example.com'
    admin_password = "admin"

    # user = usuario_controller.create_user(
    #     nombre="Trojes",
    #     email=user_email,
    #     password=user_password
    # )

    admin = usuario_controller.create_user(
        nombre="Admin",
        email=admin_email,
        password=admin_password,
        is_admin=True
    )

    return admin

def load_subject_data(admin_id):
    if not admin_id:
        raise Exception("Hubo un error al obtener el admin para crear las asignaturas")

    # Create some subjects
    subject1 = asignatura_controller.create_asignatura(
        nombre='Subject 1',
        profesor_id=admin_id,
        descripcion='This is the first subject'
    )

    subject2 = asignatura_controller.create_asignatura(
        nombre='Subject 2',
        profesor_id=admin_id,
        descripcion='This is the second subject'
    )

    return subject1, subject2

def load_labs_data(admin_id, subject):
    if admin_id:
        lab1 = laboratorio_controller.create_laboratorio(
            nombre=f"{subject.nombre}_lab1",
            asignatura_id=subject.id,
            profesor_id=admin_id
        )
        lab2 = laboratorio_controller.create_laboratorio(
            nombre=f"{subject.nombre}_lab2",
            asignatura_id=subject.id,
            profesor_id=admin_id
        )
        return lab1, lab2

    return None, None

def manage_data(manage_mode: int = 0):
    """DEPRECATED: Esta función no está actualizada con la nueva estructura de 
    la base de datos.

    Actualmente solo crea un usuario administrador para comenzar a usar el sistema

    Este método se encarga de cargar o eliminar los datos de la base de datos.

    :param manage_mode: Modo de gestión de los datos.
        0: No hacer nada (default)
        1: Cargar datos
        -1: Eliminar datos
    :type manage_mode: int
    """
    if manage_mode == 1: # Load the data
        load_user_data()

        # subject1, subject2 = load_subject_data(admin.id)
        #
        # # Create the laboratories for the subjects
        # load_labs_data(admin.id, subject1)
        # load_labs_data(admin.id, subject2)
        #
        # # Enroll the user in the subjects
        # matricula_controller.create_matricula(user.id, subject1.id)
        # matricula_controller.create_matricula(user.id, subject2.id)
        #
        # # Get the subjects in which the user is enrolled
        # subjects = matricula_controller.get_asignaturas_matriculadas(user.id)
        # print(subjects)
        #
        # # Get the students enrolled in a subject
        # students = matricula_controller.get_alumnos_matriculados(subject1.id)
        # print(students)

        print("Data loaded")

    if manage_mode == -1:
        # Delete the subjects created in the previous step
        ## The labs are deleted due to the cascade delete
        for subject in asignatura_controller.get_all_asignaturas():
            asignatura_controller.delete_asignatura(subject.id)

        # Delete the users created in the previous step
        for usuario in usuario_controller.get_all_usuarios():
            usuario_controller.delete_usuario(usuario.id)

        # Matriculas has a cascade delete, so we don't need to delete them manually
        print('Data deleted')
