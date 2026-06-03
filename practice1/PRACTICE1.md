# Практика 1 (9)

## Problem Statement:

Система «MOEX Price Alert» предназначена для инвесторов и трейдеров, желающих отслеживать изменение цен на акции Московской Биржи. Основные функции системы включают управление подписками через удобный интерфейс Telegram-бота, периодический сбор котировок с MOEX ISS API и асинхронную отправку уведомлений пользователю при изменении стоимости активов. 
Система построена на событийно-ориентированной микросервисной архитектуре и состоит из 5 независимых компонентов (API Gateway, Scheduler, Parser, Analyzer, Notifier), взаимодействующих через брокер сообщений Redis, с хранением состояния в PostgreSQL и управлением админом через веб-интерфейс с OpenAPI.

## Диаграмма Контекст

### Скриншот

![Диаграмма Контекста](./diagrams/context.png)

### Ссылка на соответствующий .puml файл

//www.plantuml.com/plantuml/png/ZP9HQzDG5CVVxwUuvgc5wYRkIKHMkk0ArPKcKdqASRreC4b3SelrhUa45SGg2FeWYlW5ujPkMRTrN-7SR-J9QQI9PJ1QajxJSt____dVknr9EvG3psKt77_V7VG4lzVOscXiMOs-ByLGtcUiLN-wzzYqkarprshf3_H7EvKgOz5Bnm_iqFRugz0EkavFlk1tDZSPauvq1OSla482Hsg4ptFy91pci80BDOOPp5MCxuHN6hUhTpdyWfGAC-hJ7kxfJtWxTFO5hxiYb1fZRH56VRyoY4HOunhyHDAP-W0d-3w4XBRYMil--mONM9iHSA56DOxFiOhX37kE8QN-Z-ez_ZebIzYMeai4uIgzfLN_YTazp_4puYUOeh4KkMGp6sd99htVS4b37gA32UgEkOeByonGHht5-WYN9pop1dzkGaf9O5MzmSAfYZDXPhoEfF0gGJQxPMUpeq8vdc8mL-Z39QfEyOdRO4xvfpMgOii1caceRNruZb-ghKrqGBwds7XEGMPHJ0gMBNqeArvV32qxS6hv4JODWzVRJNBv7HPa1fMMfjI4msSIFuO4IKMG5AvuZbShXvdvSWMZuut9nnJtOupafIDSQoU_98KChv-ILb8B0eGICxyBPIWDHKdGPQ0BSeGHObehiMLMCCl8kwRPDZQwubcExPGFkX0VVCNTn53lwCfUTM8hR4Stp9pRAdF_InD-NFk0r-ZRmkyDFFSl

./diagrams/context.puml
```plantuml
@startuml
!include <C4/C4_Context>

LAYOUT_WITH_LEGEND()

skinparam wrapWidth 300

title Диаграмма контекста (C1): Система "MOEX Price Alert"

Person(user, "Пользователь", "Инвестор, отслеживающий котировки.")
Person(admin, "Администратор", "Управляет системой через веб-интерфейс.")

System(price_alert, "Система Price Alert", "Управляет подписками, получает котировки и отправляет уведомления.")

System_Ext(moex_api, "MOEX ISS API", "Московская Биржа.")
System_Ext(telegram_api, "Telegram API", "Мессенджер.")

Rel_D(user, price_alert, "Управляет подписками", "Telegram App")
Rel_D(admin, price_alert, "Мониторинг и управление", "HTTPS/Web")
Rel_R(price_alert, moex_api, "Запрашивает котировки", "HTTPS/REST")
Rel_L(price_alert, telegram_api, "Отправляет уведомления", "HTTPS/REST")
@enduml
```

### Таблица

| Аспект | Что сгенерировал ИИ | Что исправлено вручную | Обоснование исправления |
| - | - | - | - |
| Импорт библиотеки | Внешняя ссылка !include https://... | Встроенный макрос !include <C4/C4_Context> | Предотвращение ошибок CORS и блокировок в онлайн-рендерерах. |
| Именование внешних систем | Использовалось непоследовательное название Telegram | Приведено к единому стандарту Telegram API | Обеспечение согласованности терминологии между всеми уровнями C4. |
| Направление связей | Использовались обычные стрелки Rel | Заменены на направленные стрелки Rel_D, Rel_R, Rel_U | Улучшение читаемости графа и предотвращение визуального пересечения линий. |
| Внешние акторы | Обобщенные понятия ("Интернет-магазины") | Заменено на конкретный API-провайдер ("MOEX ISS API") | Архитектура была пересмотрена в Практике 2: осуществлен пивот от парсинга HTML-страниц к работе с официальным API Московской биржи. |
| Интерфейс пользователя | Размытые связи REST-взаимодействия с пользователем | Явное указание интерфейса (Telegram App) | Пользователь взаимодействует с системой исключительно через мессенджер, что делает REST API скрытым от конечного юзера. |

### Вывод о пригодности ИИ для проектирования архитектуры. 

ИИ отлично справляется с генерацией базового каркаса контекстной диаграммы и быстрым переводом текстовых требований (Problem Statement) в код PlantUML. Однако он требует ручной корректировки для настройки визуального форматирования (направления стрелок), устранения технических проблем с импортом библиотек, устранения несогласованности по части имен составляющих архитектуры.

## Диаграмма Контейнер

### Скриншот

![Диаграмма Контейнеров](./diagrams/container.png)

### Ссылка на соответствующий .puml файл

//www.plantuml.com/plantuml/png/fLNVRnD747w_lsBh9rio6BKyeQh2SGn42i74fhHFfoMtJQwSxzoxjS2jAk6K5Y4ZGQjAbQh-K2fLVNL2J0w2B__2x7_KcTsxOycLL5LpIhHtkzyttynyixcSI1xByJ1mtlF3hM3i2VPXvsAhSz7jHA7aVYZYZnndlVtfZLi3z_RQu9gxthtQtLYjDnmdkUk78nxp8RiNyz5jtvCxx8CB5nn7-Z8G37w45ERmN3t0lw_ncJDu1HairIuiu2KiOO5R6HomUkVznYK6Uv2gAMtgixNhDxgVi5xiRmdM3aGiQuxJ4t4IXVLn8k8cgy7lY3vMJ-28M61EK7gldR771Y8GswZvVArHq75lw8U4UGQ763g5fH62wWYNgGV4YF8o-gQ-WKCw0QyOd23v8JwKo0jCBcszuQ00Jd-II35qLw9nwF5uKXzHEYwdTDn4xnbcEt4xvGRxoc7uKpR3Y7L7F1G1Gjlqngx4k2r2ZsHkH9uu_tdIP9k2Ryac-zYNGil_0Udtpq5gwezvFAGkg2bbCOSbbGTIXijtr02LrVkzTeFoEYLfvBlRN8fxV4AIUcligdbZBROIIOhUcyYT26jyXISI3pHPsu-e2wPLIBx0i1a5H047sAYdA76NRNRx0qQ4k8lVc7g8Hmi7BV7Zd97c3FQroVP9gvfHlmbkx8ObfQDgLhQ-ca6ojIEySQ1TrI_MRtJdXZhMJAanhNfiB7145SEuZwgiE1l6g3rSLFZsO9_AclEexoYZAWSFUJ3vKhEqzRB2yptYZ_GmJS-Xn0oU4o7CgrnX9FtFVCsrePSLhj-mi2Uwb0T4mTGK-QYwZqaTyhwiiAxUgNjSyZiy4SYmcYyrRvJ8xLZqRwvhxZ-9bqZ8PqH8JQKFIpLJtrPuRux5MDHZuVa9eg-B9E7RWgt4qLsZUfDsSj6FO95RA6Mcwarc2eSBdVL4s_RhSY2xzsLz68dxBdgtcLyrQ_q-UQqegXxfEQ8iYCmTbCCAGvMmNwWBQfgRymN9GW9dKmJkQd7Ds0EScpz3o6jpkp0p0_XhhWHgPKhSrmQ3NX_9SYwRf39_nfKdXbdDIdYBvgdae5lqD1X-VcjYoA8afsObQoLaGoqJm5-8CNvPj8mKdSqJJTFfjT0IfOfozDv9mKmPYlyM_q9IE0P-AWRJrEyByjCbROuIfjzip1z585EqAkPMYR7SGqKZZKPVfM7_7EfNEgjciCX7tuwOUxS4v-ysV0y3BT1XwNyai6jC75HKcdJ3OTNshE3Fu9Y0QjUEQUQiX9dBvd_0JiqQxBrz5QcdTf4lYz0R3uE_0G00

./diagrams/container.puml
```plantuml
@startuml
!include <C4/C4_Container>

LAYOUT_WITH_LEGEND()

skinparam wrapWidth 300

title Диаграмма контейнеров (C2): Система "MOEX Price Alert"

Person(user, "Пользователь", "Пользователь Telegram.")
Person(admin, "Администратор", "Сотрудник поддержки/Админ.")

System_Boundary(price_alert_system, "Система Price Alert") {
    Container(admin_panel, "Admin Frontend", "Node.js, React, Vite", "Веб-интерфейс панели администратора (SPA).")
    Container(api_gateway, "API Gateway / Bot", "Python, FastAPI, Aiogram", "Предоставляет REST API для фронтенда и обрабатывает команды Telegram.")
    Container(scheduler, "Scheduler", "Python", "Планировщик задач.")
    Container(parser, "Parser", "Python", "Сборщик цен.")
    Container(analyzer, "Analyzer", "Python", "Бизнес-логика.")
    Container(notifier, "Notifier", "Python", "Отправка сообщений.")
    ContainerDb(database, "Database", "PostgreSQL", "Хранилище данных.")
    ContainerQueue(redis, "Message Broker", "Redis", "Очереди (parse, analyze, notify).")
}

System_Ext(moex_api, "MOEX ISS API", "Биржа")
System_Ext(telegram_api, "Telegram API", "Мессенджер")

Rel_D(admin, admin_panel, "Просмотр статистики", "HTTPS")
Rel_D(admin_panel, api_gateway, "API запросы", "HTTPS/REST")
Rel_D(user, api_gateway, "Команды бота", "Telegram")

Rel_D(api_gateway, database, "Чтение/запись", "TCP/SQL")
Rel_D(scheduler, database, "Чтение тикеров", "TCP/SQL")
Rel_D(scheduler, redis, "Задачи", "queue:parse")
Rel_D(parser, redis, "Тикеры", "queue:parse")
Rel_U(parser, moex_api, "Котировки", "HTTPS")
Rel_D(parser, redis, "Новые цены", "queue:analyze")
Rel_D(analyzer, redis, "Свежие цены", "queue:analyze")
Rel_D(analyzer, database, "Сверка цен", "TCP/SQL")
Rel_D(analyzer, redis, "Алерты", "queue:notify")
Rel_D(notifier, redis, "Алерты", "queue:notify")
Rel_D(notifier, telegram_api, "Сообщения", "HTTPS")
@enduml
```

### Таблица

| Аспект | Что сгенерировал ИИ | Что исправлено вручную | Обоснование исправления |
| - | - | - | - |
| Детерминированность логики | Публикация задач в очередь была помечена как (опционально) | Зафиксирована жесткая связь без опциональности | Системный дизайн должен быть детерминированным и однозначно описывать потоки данных. |
| Паттерн взаимодействия с очередью | Стрелка направлена от воркера к очереди как прямой синхронный запрос | Уточнено направление и тип связи (воркер слушает брокер) | Точное отражение паттерна асинхронного взаимодействия Queue Consumer. |
| Согласованность компонентов | Отсутствовало указание протоколов взаимодействия на некоторых связях | Добавлены явные указания TCP/AMQP и TCP/SQL | Повышение технической точности архитектурного документа. |
| Декомпозиция системы | Монолитный "Background Worker", выполняющий все фоновые задачи | Воркер разбит на независимые микросервисы | Переход к истинной микросервисной архитектуре (Single Responsibility Principle) для независимого масштабирования узких мест (например, парсера биржи). |
| Очереди сообщений | Одна общая очередь "Task Queue" | Указаны 3 независимые событийные очереди (queue:parse, queue:analyze, queue:notify) | Событийно-ориентированная архитектура требует изоляции топиков для правильного роутинга между микросервисами. |
| Управление админом | Отсутствие пользовательского интерфейса для управления. | Добавлен контейнер Admin Frontend (React/Vite) и расширена роль API Gateway до полноценного REST-сервера на FastAPI. | Системе потребовалась административная панель для визуального контроля метрик и подписок, что потребовало внедрения паттерна SPA (Single Page Application). |

### Вывод о пригодности ИИ для проектирования архитектуры. 

На уровне контейнеров ИИ способен корректно определить основные системные блоки (API, БД, Воркер, Очередь), но склонен добавлять архитектурные неопределенности ("опциональные" связи) и иногда путает паттерны взаимодействия (например, pull/push для очередей). Ручной контроль необходим для фиксации жесткой архитектурной логики.

## Диаграмма Компонент

### Скриншот

![Диаграмма Компоненты](./diagrams/component.png)

### Ссылка на соответствующий .puml файл

//www.plantuml.com/plantuml/png/dLHTQnj757tVNp7rYoL8hD3cAPGIMHBzG4aKIoRqQLdjJgqbgvtjx6w3MWgMHPCMcnfAeQKFBeL-lCeVIpPIvVo5E_-ezzvTMJ6A7neRbj6TkNVEkUVSkHydZaxIOM2zvuTka7fIVDYuMslSjHjg6AbGXib7bjMkV_vejsS_-RJtYTrkVTnwsAnKBIj-weUHevsXUAQTw8dl9GFn_fqxbfNuII05_0mvJE7SxEFtN_oV2fZ19IvUutS16IpC0QxEHANnGVMUWDyeZA4CNj6ssHSRzT09HbzBlM5P3HKcZXzA_JYLgQnewVdnBR7nGCQnioV5jbPFyHn6TcY75d1YNb0PB7W1kO2NCCN5rBpOsgYkoZNx5Sz9dBuJIynfbalAxwWusTEo-xZDrVvY8WiaDOVS_02PO28N-CtD65SpghigR6-hDFGSFQeu9GlRNUxTMb4J3tnNgrZghtnNRbJ5DvR0F_vSIL2mfVGu7N8sDq6q_JYHOK6RZsmvyIXqVSM0_u2vcPZl4NHc3WHShhfXZiJcbrJXNWbjKr23ScpH6RBBO5OcVTPzz52OiO052MKEKRnScEUa7OkQ8-MtuOqqah4ZhLoKHsbg9aL4PndX_ewIWGePwj-56xZ3StD4rSsnW5E2n5uOtuOvGZY7dB1j2VZ9728VQlpS71S4Bo2ZP2mpAJ4IAynwNNeWMvt5chXnQhvZ1NEaScd6c7b4VJhWZ2dsOaPq9xYWTBBkdAddvlW6ubxVZf6Whq8oqxROaP6A_KJf4V54AzK3To278r4deRh5KTeYGkodEInAa6K_5cpS6JBAUMuMU30JtLQxrUZLTZlDUg_5tYRGpE8GvmoJCNBALdrEKecUx-A0K4UwQJzsjHybUFKDD9n0wiIEqdxWnuF2hXGHdJ9oW-F-nFltoHPctqoOG-IC0kLuWdGbzn4iKNac0rSDPQsmYJjmmZtfLGaRafWKi65Mbe0CPRyKSBRqRAWI_ulH9a7_rh9sP60trmQ4VwyFmUeDmBigVHsfg4h8UurEZTyDScYYN1LWyRTNNhSs_BwSg_8MCYND2qoHy57fnK9aL6_2kkQbNBY7aerPrLU2P-mbvUBz361dVPQkUGn-APMV8icSxYmXKAT91lCZ0w2BYmPV1rkEDftx_mYvG-i0rzq3l_BKa8LNte1pWiLmfhI5ID-qoJisRFVQ3BxnjCC_M9Md5x8QdC1fmHpcow08d3YnsLs-z6ocjJG7JkuLtpLwLsOxMJqT_DGidz3RY9TUcqFSfuigGPJ6WvkTPzsNePSEW_y0

./diagrams/component.png
```plantuml
@startuml
!include <C4/C4_Component>

LAYOUT_WITH_LEGEND()

skinparam wrapWidth 200

title Диаграмма компонентов (C3): Контейнер "Analyzer"

ContainerQueue(redis, "Message Broker", "Redis", "Очереди задач.")
ContainerDb(database, "Database", "PostgreSQL", "Хранилище подписок.")

Container_Boundary(analyzer_container, "Analyzer Microservice") {
    
    Component(redis_consumer, "Queue Listener", "redis.asyncio", "Слушает очередь 'queue:analyze' и извлекает JSON с новыми ценами.")
    
    Component(price_processor, "Price Processor", "Python", "Центральная бизнес-логика. Вычисляет дельту цен и определяет необходимость отправки уведомления.")
    
    Component(db_session, "DB Repository", "SQLAlchemy AsyncSession", "Выполняет транзакционные SELECT/UPDATE запросы к таблицам Ticker и Subscription.")
    
    Component(alert_publisher, "Alert Publisher", "redis.asyncio", "Формирует payload алерта (welcome/price_changed) и публикует его в 'queue:notify'.")
}

Rel_D(redis_consumer, redis, "Слушает задачи (brpop)", "TCP/Redis Protocol")
Rel_D(redis_consumer, price_processor, "Передает словарь цен", "Внутрипроцессный вызов")

Rel_R(price_processor, db_session, "Запрашивает старую цену и передает новую", "Внутрипроцессный вызов")
Rel_D(price_processor, alert_publisher, "Инициирует генерацию алерта", "Внутрипроцессный вызов")

Rel_U(db_session, database, "Чтение/Обновление last_notified_price", "TCP/SQL")
Rel_D(alert_publisher, redis, "Отправляет JSON-событие (lpush)", "TCP/Redis Protocol")

@enduml
```

### Таблица

| Аспект | Что сгенерировал ИИ | Что исправлено вручную | Обоснование исправления |
| - | - | - | - |
| Именование компонентов | Шаблонные названия (Репозиторий БД, Сервис уведомлений) | Доменные специфичные имена (Subscription Repository, Telegram Notifier) | Повышение точности декомпозиции и привязка к конкретной бизнес-логике. |
| Кросс-функциональные требования (CFR) | Отсутствие упоминаний отказоустойчивости и ограничений | Добавлены паттерны Retry, Rate Limiting, Ack/Nack в описания компонентов | Отражение нефункциональных требований к надежности (сетевые отказы, лимиты API). |
| Поток управления (Control Flow) | Разрозненные вызовы компонентов без явного центра | Централизация логики через Price Change Analyzer | Явное выделение компонента-оркестратора, управляющего бизнес-процессом. |
| Фокус рассмотрения | Рассматривалась архитектура устаревшего монолитного воркера | Фокус смещен на микросервис Analyzer как на ядро бизнес-логики | Так как парсинг и уведомления вынесены в отдельные сервисы, C3 диаграмма должна детально показывать флоу работы с БД и формирования алертов внутри анализатора. |
| Инструментарий | Указаны технологии BeautifulSoup / HTTP Clients | Заменены на Redis Pub/Sub и SQLAlchemy | Отражение реального стека Практики 2: анализатор не делает внешних запросов, а работает исключительно с брокером сообщений и СУБД. |

### Вывод о пригодности ИИ для проектирования архитектуры. 

ИИ отлично справляется с генерацией базового каркаса C4-диаграмм и быстро переводит текстовые требования в код PlantUML. Однако ИИ склонен к упрощению систем (предлагая монолитные воркеры вместо гранулярных микросервисов) и часто не видит потребности в разделении очередей сообщений. Построение качественной событийно-ориентированной архитектуры (Event-Driven) требует жестких корректировок со стороны архитектора-человека, но ИИ берет на себя всю рутину по написанию синтаксиса визуализации.
