# Análisis de rendimiento en un videojuego MOBA en base al historial de juego

Este proyecto se trata de mi **Trabajo Final de Grado**. Consiste en un proyecto full-stack en el que he utilizado al conocido videojuego League of Legends, perteneciente al género MOBA, como fuente de la que extraer datos de los jugadores para analizar su rendimiento dentro del propio videojuego. La relevancia de este videojuego lo convierte en un tema atractivo para el ámbito del análisis de datos.

# Objetivo

El principal objetivo de este proyecto ha sido crear una herramienta que procese y muestre los datos de rendimiento de un usuario del videojuego y le permita visualizarlos y darle una interpretación sencilla con el fin de mejorarlo. Para ello:
- Se han utilizado metodologías ágiles como Kanban para la planificación del proyecto.
- Se ha ofrecido una visualización web sencilla e intuitiva de los datos analizados.
- Se ha desarrollado un proyecto de recopilación masiva y continuada de los datos.

# Fases de desarrollo

- Recopilación de datos a través de la API oficial de Riot Games, empresa creadora del videojuego.
- Almacenamiento de los mismos en una base de datos no relacional, llegando a acumular +50GB en ficheros localmente.
- Consulta de funcionalidad relevante con un jugador profesional > [LADYBUG](https://lol.fandom.com/wiki/LADYBUG)
- Desarrollo de la lógica de negocio que procesa los datos por apartados y los analiza.
- Creación de una interfaz web desde cero para permitir la visualización de los datos analizados.

# Tecnologías utilizadas

- Python 3.10.11
- Librerías como NumPy, Pandas o Seaborn
- PyCharm y Visual Studio Code como IDEs
- MongoDB para BBDD no relacional
- React como librería de desarrollo web
- Flask para comunicación entre el programa analítico y el cliente web
- Jira Software para la planificación de las fases del desarrollo

# Funcionamiento
![Pantalla principal](https://github.com/user-attachments/assets/1d9142d0-e047-4ff5-bb04-fe5f6eec4041)
La pantalla principal de la web, con unas sencillas barras de búsqueda para encontrar a los usuarios.

![Error de búsqueda](https://github.com/user-attachments/assets/62fa50b4-cb61-4144-baa2-52f5d62a9542)
Se contemplaron varias posibilidades de errores en la búsqueda como nombre vacío, nombre inexistente, código Riot erróneo, etc.

![Pantalla principal](https://github.com/user-attachments/assets/2a16429a-23d0-446a-a5d3-7630a5ab9d6c)
Pantalla principal con la información básica de un usuario y los apartados analizados.

![Panel de ayuda y botones interactivos](https://github.com/user-attachments/assets/c10d3f6a-f1cf-42f6-b353-81889fe0ee99)
Para cada posible ventana, se incluyó un panel explicativo. Además, todos los botones son interactivos y reaccionan al cursor.

![Ejemplos de gráficas](https://github.com/user-attachments/assets/cf96d919-943b-4162-8ec0-d5865e987f21)
Algunos ejemplos de las múltiples gráficas añadidas como analíticas al proyecto. Visualización muy simple, información directa.

# Objetivos prácticos
El principal objetivo práctico que pretendí llevar con este trabajo es el de desarrollar un proyecto full-stack desde cero, abarcando la obtención de requisitos de usuario, la recopilación, almacenamiento y gestión eficiente de datos a gran escala, desarrollo de una lógica analítica como back-end y de una interfaz web de visualización como front-end, además de priorizar el análisis de datos como temática principal del proyecto.
