# VM Nexus
VM Nexus es una aplicación web que permite la gestión y uso de máquinas virtuales alojadas en un servidor **Proxmox**, accesibles mediante **Apache Guacamole** a través de una conexión **VNC**.

El proyecto fue desarrollado como Trabajo Fin de Grado en Ingeniería Informática, con el objetivo de crear una plataforma que facilite la enseñanza práctica mediante laboratorios virtuales.

## Características principales
- Gestión de **usuarios**, **asignaturas** y **máquinas virtuales** desde una interfaz web para administradores (profesores).
- **Acceso individual para estudiantes**, quienes pueden conectarse a las máquinas virtuales asignadas directamente desde el navegador.
- Integración con **Proxmox VE** y **Apache Guacamole**, permitiendo el acceso remoto a entornos de prácticas.
- **Backend y Frontend en Flask** y **base de datos MySQL**.
- Despliegue documentado y reproducible mediante configuración detallada de los servicios necesarios.

## Objetivo general
Ofrecer una solución centralizada que permita a docentes y alumnos trabajar con entornos virtuales sin necesidades de configuraciones locales, fomentando la enseñanza práctica en asignaturas técnicas sin preocuparse por los recursos de los alumnos.

## Tecnologías utilizadas
- Python (Flask)
- MySQL
- Apache Guacamole
- Proxmox VE
- HTML / CSS / JavaScript

## Documentación adicional
La información sobre el despligue puede encontrarse en [DEPLOYMENT.md](./DEPLOYMENT.md)

## Licencia
This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)
