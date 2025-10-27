import matplotlib.pyplot as plt

if __name__ == "__main__":

    # Pruebas a realizar
    ## Clon sin guacamole, 5 veces
    ## Clon con guacamole, 5 veces
    ## 3 clones sin guacamole, 5 veces
    ## 3 clones con guacamole, 5 veces

    # Otros datos
    ## median_idle_cpu = 0.004731741065200017 ~ 0.47%
    ## median_idle_ram = 3138301337.6
    ## La ram es ~2.92 GB o 37.67% de la ram total
    ## Unas 4 horas y 30 minutos de uptime

    # Pruebas con un solo clon
    # times_single_clone = [57.047, 55.346, 57.167, 55.123, 59.632, 55.244, 57.795, 55.336, 57.644, 55.262]
    # times_single_clone = [122.031, 121.788, 138.949, 129.327, 147.652, 132.023, 122.098, 126.139, 129.173, 137.289]
    times_single_clone = [24.728, 24.549, 23.695, 23.775, 23.846, 23.689, 23.780, 24.363, 23.798, 23.745]

    # Tiempo
    plt.plot(range(1, len(times_single_clone) + 1), times_single_clone, marker='o', linestyle='-')
    plt.xlabel("Intento")
    plt.ylabel("Tiempo (s)")
    plt.title("Tiempo de creación de conexión en Guacamole")
    plt.ylim(min(times_single_clone) - 0.2, max(times_single_clone) + 0.2)
    plt.savefig("tiempo_guacamole_conection.png")


