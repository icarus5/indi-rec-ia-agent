# INDI REC IA AGENT

## Descripción
Este proyecto implementa un agente conversacional basado en Azure Functions, Azure IA para el procesamiento de lenguaje natural y la gestión de conversaciones. El agente está diseñado para interactuar con usuarios a través de diferentes canales de comunicación, procesando y respondiendo a consultas de manera inteligente.

## Requisitos Previos
- Python 3.11.9
- Node.js 18+ (para Azure Functions Core Tools)
- Azure Functions Core Tools v4 (recomendado)
- Variables de entorno configuradas en `local.settings.json`

## Dependencias
El proyecto utiliza las siguientes dependencias principales:
- annotated-types==0.7.0
- anyio==4.9.0
- azure-ai-documentintelligence==1.0.2
- azure-core==1.35.0
- azure-functions==1.23.0
- azure-servicebus==7.14.2
- certifi==2025.7.14
- charset-normalizer==3.4.2
- colorama==0.4.6
- colorlog==6.9.0
- distro==1.9.0
- et_xmlfile==2.0.0
- greenlet==3.2.3
- h11==0.16.0
- httpcore==1.0.9
- httpx==0.28.1
- idna==3.10
- isodate==0.7.2
- jiter==0.10.0
- jsonpatch==1.33
- jsonpointer==3.0.0
- langchain==0.3.26
- langchain-core==0.3.69
- langchain-openai==0.3.28
- langchain-text-splitters==0.3.8
- langgraph==0.5.3
- langgraph-checkpoint==2.1.1
- langgraph-prebuilt==0.5.2
- langgraph-sdk==0.1.73
- langsmith==0.4.7
- numpy==2.3.1
- openai==1.97.0
- openpyxl==3.1.5
- orjson==3.11.0
- ormsgpack==1.10.0
- packaging==25.0
- pandas==2.3.1
- pydantic==2.11.7
- pydantic_core==2.33.2
- pyodbc==5.2.0
- python-dateutil==2.9.0.post0
- pytz==2025.2
- PyYAML==6.0.2
- redis==6.2.0
- regex==2024.11.6
- requests==2.32.4
- requests-toolbelt==1.0.0
- six==1.17.0
- sniffio==1.3.1
- SQLAlchemy==2.0.41
- tenacity==9.1.2
- tiktoken==0.9.0
- tqdm==4.67.1
- typing-inspection==0.4.1
- typing_extensions==4.14.1
- tzdata==2025.2
- urllib3==2.5.0
- xlrd==2.0.2
- xxhash==3.5.0
- zstandard==0.23.0

## Instalación
1. Clonar el repositorio
2. Instalar Azure Functions Core Tools (requerido para desarrollo local):
   ```bash
   npm install -g azure-functions-core-tools@4 --unsafe-perm true
   ```
3. Instalar driver odbc (requerido para desarrollo local):

   https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server?view=sql-server-ver16

4. Crear y activar entorno virtual:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   source .venv/Scripts/activate #Windows bash
   ```
5. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
   o para ejecutar el .toml
   ```bash
   pip install .
   ```
6. Configurar variables de entorno en `local.settings.json`

## Estructura del Proyecto
```
src/
├── ai/               # Lógica de IA, incluyendo prompts, herramientas y el grafo de LangGraph.
│   ├── prompts/      # Plantillas de prompts para el modelo de lenguaje.
│   └── tools/        # Herramientas y schemas que el agente puede utilizar.
├── api/              # Endpoints de la API expuestos por Azure Functions.
│   └── controllers/  # Controladores que manejan las solicitudes HTTP.
├── channels/         # Adaptadores para diferentes canales de comunicación (ej. Jelou).
├── config/           # Módulos de configuración para servicios externos.
├── domain/           # Lógica de negocio principal, modelos y repositorios.
│   ├── models/       # Modelos de datos y entidades del dominio.
│   ├── repositories/ # Abstracciones para el acceso a datos.
│   └── services/     # Lógica de negocio y orquestación de operaciones.
├── integrations/     # Integraciones con servicios de terceros (ej. Indi).
│   └── indi/         # Implementación específica para la integración con Indi.
└── utils/            # Utilidades y herramientas compartidas.
    ├── date/         # Funciones para el manejo de fechas.
    ├── ocr/          # Lógica para el reconocimiento óptico de caracteres.
    ├── requests/     # Utilidades para solicitudes HTTP.
    ├── storage/      # Clientes para servicios de almacenamiento (ej. Azure Blob Storage).
    └── tools/        # Herramientas de utilidad general.
```

## Endpoints API
- `POST /api/agent/query`: Endpoint principal para interactuar con el agente.
- `POST /api/memory/sync_clients`: Endpoint para sincronizar clientes.
- `POST /api/memory/sync_collections`: Endpoint para sincronizar colecciones.
- `POST /api/queue/payment_sheet`: Endpoint para procesar planillas de pago en cola.

## Ejecución Local
Para ejecutar la aplicación localmente:

```bash
# Asegúrate de estar en el directorio raíz del proyecto
# y tener el entorno virtual activado

# Iniciar las Azure Functions localmente
func start --port 7072
```

Esto iniciará el servidor local en el puerto 7072.

### Ejemplo de uso
```bash
curl --location 'http://localhost:7072/api/v1/agent/query' \
--header 'Content-Type: application/json' \
--data '{
    "data": {
        "type": "TEXT",
        "text": "Hola"
    },
    "sender": "+51935220229",
    "forceAnonymous": false
}'
```

## Arquitectura
El proyecto sigue una arquitectura limpia, separando la lógica de negocio de las implementaciones técnicas:

- **Domain Layer**: Contiene las entidades y reglas de negocio (`src/domain/`).
- **Application Layer**: Orquesta los casos de uso y la lógica de la aplicación (`src/domain/services/`).
- **Adapters/Interfaces Layer**: Adaptadores para la entrada/salida, como los controladores de API (`src/api/controllers/`) y los canales de comunicación (`src/channels/`).
- **Infrastructure/Integrations Layer**: Implementaciones técnicas e integraciones con servicios externos (`src/integrations/`, `src/config/`, `src/utils/storage/`).
- **AI Layer**: Lógica de inteligencia artificial y gestión de la conversación (`src/ai/`).

## Bot Conversacional
El bot está implementado como una Azure Function, utilizando LangChain y LangGraph para el procesamiento de lenguaje natural. El bot:
- Procesa mensajes entrantes a través de los endpoints de la API.
- Utiliza modelos de lenguaje para generar respuestas.
- Gestiona la memoria de conversaciones.
- Se integra con diversos servicios externos.

## Seguridad
- Validación de entrada de datos.
- Logging estructurado.

## Monitoreo
- Logs estructurados con colorlog.
- Métricas de rendimiento y uso.
- Integración con servicios de monitoreo de Azure.

## Contribución
1. Fork del repositorio
2. Crear rama feature (`git checkout -b feature/`)
3. Commit cambios (`git commit -m 'feat: INDI-MA-456 my super commit'`)
4. Push a la rama (`git push origin feature/INDI-MA-123-branch-feature-name`)
5. Abrir Pull Request

## Licencia
Este proyecto es privado y confidencial.