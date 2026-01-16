# MANUAL DE USUARIO
## Sistema de Control de Equipos Informáticos (SCEI)

**Dirección de Informática**  
*Versión 2.0*

---

## ÍNDICE

1. [Introducción](#1-introducción)
2. [Requisitos e Instalación](#2-requisitos-e-instalación)
3. [Acceso al Sistema](#3-acceso-al-sistema)
4. [Navegación General](#4-navegación-general)
5. [Módulos del Sistema](#5-módulos-del-sistema)
    - [Inicio (Direcciones)](#51-inicio-direcciones)
    - [Gestión de Equipos](#52-gestión-de-equipos)
    - [Mantenimientos](#53-mantenimientos)
    - [Analítica](#54-analítica)
    - [Bitácora](#55-bitácora)
    - [Configuración](#56-configuración)
6. [Reportes](#6-reportes)
7. [Seguridad y Soporte](#7-seguridad-y-soporte)

---

## 1. INTRODUCCIÓN

El **Sistema de Control de Equipos Informáticos (SCEI)** es una solución integral diseñada para optimizar la gestión del inventario tecnológico y el seguimiento de mantenimientos preventivos y correctivos dentro de la Dirección de Informática y las diversas dependencias de la organización.

**Objetivos del Sistema:**
- Centralizar el inventario de hardware.
- Registrar y auditar mantenimientos técnicos.
- Generar reportes automatizados (PDF, Excel, Word).
- Ofrecer estadísticas en tiempo real sobre el estado del parque tecnológico.
- Garantizar la trazabilidad de cambios mediante auditoría detallada.

---

## 2. REQUISITOS E INSTALACIÓN

### Requisitos del Sistema
- **Sistema Operativo:** Windows 10 o superior (64-bits).
- **Espacio en Disco:** 200 MB libres.
- **Memoria RAM:** Mínimo 4 GB.
- **Cámara Web:** Requerida solo si se desea utilizar el **Ingreso Facial**.

### Ejecución (Modo Portátil)
El sistema se distribuye como un **ejecutable único (`SCEI.exe`)** y portátil. No requiere instalación tradicional.

1. Copie el archivo `SCEI.exe` a su ubicación preferida (Ej: Escritorio o Documentos).
2. Haga doble clic para iniciar.
3. **Nota Importante:** En la primera ejecución, el sistema configurará automáticamente su base de datos en una carpeta segura del sistema para garantizar que la información perdure.

---

## 3. ACCESO AL SISTEMA

Al iniciar la aplicación, se presentará la pantalla de **Login** con un diseño moderno de panel dividido.

- **Usuario:** Seleccione o escriba su usuario (aparecen sugerencias para usuarios existentes).
- **Contraseña:** Ingrese su clave de acceso.
- **Ingreso Facial:** Si ha configurado previamente su biometría, puede acceder haciendo clic en el botón "Ingreso Facial" y mirando a la cámara.
- **Recuperación:** Opciones para "Olvidaste tu contraseña" (preguntas de seguridad) y "Registrarse" (nuevos usuarios).

> *Nota: Por defecto, el sistema siempre se inicia maximizado para una mejor experiencia.*

---

## 4. NAVIGACIÓN GENERAL

El diseño del sistema ("Premium Dark") está pensado para reducir la fatiga visual y facilitar la operación.

- **Ventana Maximizada:** El sistema opera siempre en pantalla completa para aprovechar el espacio de trabajo.
- **Barra Lateral (Izquierda):** Contiene el menú principal para navegar entre módulos (Inicio, Analítica, Bitácora, Configuración).
- **Cabecera de Módulo:** Muestra el título de la sección actual.
- **Pestañas de Gestión (Superior):** Dentro de cada Dirección, permiten alternar rápidamente entre **Equipos** y **Mantenimientos**.

---

## 5. MÓDULOS DEL SISTEMA

### 5.1. INICIO (DIRECCIONES)
Este es el panel principal donde se organiza la estructura jerárquica de la institución.

- **Visualización:** Las direcciones y coordinaciones se muestran como tarjetas.
- **Búsqueda y Acciones:** Barra de búsqueda compacta y botón de "Nueva Dirección" en la cabecera.
- **Edición/Eliminación:** Haga clic en el botón de opciones (⋮) en cada tarjeta para **Editar** el nombre o **Eliminar** la dependencia.

### 5.2. GESTIÓN DE EQUIPOS
El núcleo del inventario. Aquí se administra todo el hardware.

- **Listado:** Tabla con columnas ordenables (Código, Descripción, Marca, Modelo, Serie, Estado).
- **Auditoría de Cambios:** Cualquier modificación crítica (cambio de estado, marca, modelo) queda registrada detalladamente en la Bitácora (Ej: "Estado: Bueno -> Malo").
- **Nuevo Equipo:** Botón para registrar un activo.
- **Editar/Eliminar:** Opciones para modificar o dar de baja equipos.
- **Reportes:** Generación directa de reportes PDF/Word/Excel desde el panel de acciones.

### 5.3. MANTENIMIENTOS
Módulo para el control técnico y hojas de vida de los equipos.

- **Registro:** Asocie una actividad técnica a un huesped.
- **Trazabilidad:** Al editar un mantenimiento, se guarda un registro exacto de qué cambió (descripción, fecha, etc.).
- **Reportes:** Generación de informes de servicio filtrados por fecha, estado o técnico.

### 5.4. ANALÍTICA
Panel gráfico para la toma de decisiones.

- **Gráficos Interactivos:**
    - Distribución de equipos por Estado.
    - Distribución por Marca.
    - Carga de inventario por Dirección.
- Se actualizan en tiempo real con cada cambio en el inventario.

### 5.5. BITÁCORA
Sistema de auditoría avanzado.

- **Registro Detallado:** Captura quién hizo qué, cuándo y dónde.
- **Detalle de Cambios:** Para ediciones, muestra el valor anterior y el nuevo valor de los campos modificados.
- **Filtros:** Por usuario, módulo o fecha.
- **Exportación:** Descarga de logs para auditoría en Excel/PDF.

### 5.6. CONFIGURACIÓN
Panel personal y administrativo.

- **Perfil de Usuario:**
    - Cambio de usuario y contraseña.
    - **Validación de Seguridad:** Las contraseñas nuevas requieren al menos una mayúscula, un número y un carácter especial.
- **Seguridad Biométrica:**
    - **Configurar Facial:** Registre su rostro para iniciar sesión sin contraseña.
    - **Borrar:** Elimine sus datos biométricos si lo desea.
- **Zona de Peligro:** Opción para eliminar su propia cuenta (requiere confirmación y permisos si no es admin).
- **Administración de Usuarios (Solo Admin):**
    - Tabla compacta con lista de usuarios registrados.
    - Opciones para editar o eliminar otros usuarios del sistema.

---

## 6. REPORTES

El sistema incluye un potente generador de reportes accesible desde los módulos de Equipos y Mantenimientos.

**Formatos Soportados:**
- **PDF:** Reportes formales para imprimir.
- **Excel:** Hojas de cálculo para análisis de datos.
- **Word:** Documentos editables.

Todos los reportes generados quedan registrados en la bitácora con el nombre del archivo y el usuario que lo generó.

---

## 7. SEGURIDAD Y SOPORTE

- **Base de Datos:** Los datos se almacenan localmente. Se recomienda realizar copias de seguridad de la carpeta de datos periódicamente.
- **Cifrado:** Las contraseñas se almacenan con hash seguro.
- **Soporte Técnico:** Para fallos del sistema o dudas operativas, contacte a la Dirección de Informática interna.

---
© 2026 Dirección de Informática - SCEI.
