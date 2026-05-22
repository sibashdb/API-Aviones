# ✈️ SkySpecs API

> Una API RESTful de alto rendimiento para la gestión de especificaciones técnicas, aviónica y catalogación relacional de aeronaves. 

SkySpecs API proporciona un catálogo centralizado para desarrolladores, entusiastas de la aviación y creadores de simuladores. Permite consultar desde plataformas VTOL y drones de vigilancia, hasta cazas militares y aviones comerciales, con un diseño de base de datos completamente normalizado.

## Documentación Interactiva (Live Demo)

La API está desplegada en la nube y lista para ser consumida. Puedes explorar, probar los endpoints y ver los esquemas de datos directamente desde la interfaz de Swagger:

🔗 **[Visitar SkySpecs API - Swagger UI](https://api-aviones.onrender.com/docs#/)**
🔗 **[Visitar SkySpecs API - ReDoc](https://api-aviones.onrender.com/redoc)**

---

## Tecnologías y Arquitectura

Este proyecto fue construido utilizando estándares modernos de desarrollo backend:

* **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12)
* **Base de Datos:** PostgreSQL alojada en [Supabase](https://supabase.com/)
* **ORM:** [SQLModel](https://sqlmodel.tiangolo.com/)
* **Almacenamiento Multimedia:** Supabase Storage (Buckets públicos)
* **Despliegue (CI/CD):** [Render](https://render.com/)

---

## Características Principales

* **Estructura Relacional Completa:** Gestión independiente de Fabricantes (Marcas), Especificaciones Técnicas y Etiquetas dinámicas.
* **Patrón List/Detail:** Rutas optimizadas que devuelven resúmenes ligeros de aeronaves con enlaces dinámicos (HATEOAS) hacia sus fichas técnicas detalladas.
* **Gestión Multimedia Avanzada:** Endpoints dedicados para la subida, actualización y eliminación de imágenes físicas en la nube, sincronizadas automáticamente con la base de datos PostgreSQL.
* **Autodocumentación:** Integración nativa con OpenAPI para generar esquemas de validación y ejemplos automáticos.

