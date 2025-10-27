import json
import matplotlib.pyplot as plt

try:
    with open("consumos.json", "r") as file:
        data = json.load(file)
except FileNotFoundError:
    print("No se ha encontrado el archivo 'consumos.json'")
    exit(1)

# Obtener datos
cpu_checks = data["cpu_checks"]
memory_checks = data["memory_checks"]
total_ram = data["total_ram"]
try_number = input("Introduce el número de intento: ")


# Crear eje X (tiempo en segundos)
time_axis = [i * 0.5 for i in range(len(cpu_checks))]  # Cada muestra se toma cada 0.5s

# Convertir RAM a porcentaje
ram_percentages = [(mem / total_ram) * 100 for mem in memory_checks]

plt.figure(figsize=(10, 5))

# Graficar CPU y RAM
plt.plot(time_axis, [cpu * 100 for cpu in cpu_checks], label="CPU (%)", color='red')
plt.plot(time_axis, ram_percentages, label="RAM (%)", color='blue')

plt.xlabel("Tiempo (s)")
plt.ylabel("Uso (%)")
plt.title("Evolución del consumo de CPU y RAM durante la clonación")
plt.legend()
plt.grid(True)

# Guardar
plt.savefig(f"cpu_ram_overtime_{try_number}.png")
