import app.proxmox as prox
import time, json

def check():
    total_ram = 8329920512
    elapsed_time = 0
    cpu_checks = []
    memory_checks = []

    muestras = 0
    try:
        while elapsed_time < 300:
            resources = prox.get_node_status()
            if resources is not None:
                cpu_checks.append(resources['cpu'])
                memory_checks.append(resources['memory']['used'])
                muestras += 1
            time.sleep(0.5)
            elapsed_time += 0.5
    except KeyboardInterrupt:
        print("Saliendo")

    if muestras == 0:
        print("No hay muestras")
    else:
        cpu_avg = sum(cpu_checks) / muestras
        memory_avg = sum(memory_checks) / muestras

        print(f"CPU: {cpu_avg}")
        print(f"Memory: {memory_avg}")
        print(f"Total RAM: {total_ram}")
        print(f"Porcentaje de uso de memoria: {memory_avg / total_ram * 100}%")
        print(f"Porcentaje de uso de CPU: {cpu_avg}%")

        data = {
            "cpu_checks": cpu_checks,
            "memory_checks": memory_checks,
            "total_ram": total_ram
        }
        with open("consumos.json", "w") as f:
            json.dump(data, f)

if __name__ == "__main__":
    check()
