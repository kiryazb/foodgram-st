# 🍽️ Foodgram – API сервиса

---

## ⚙️ Стек технологий
| **Компонент**      | **Технология** |
|-------------------|--------------|
| Backend          | Python 3.9, Django 3.2, Django REST Framework |
| Auth            | Djoser, Simple JWT |
| БД              | PostgreSQL |
| Контейнеризация | Docker, Docker Compose |
| CI/CD           | GitHub Actions, Nginx |

---

# 📌 Гайд по установке Foodgram

## 🌍 Переменные окружения
Сервис использует следующие переменные среды для настройки подключения к базе данных:
```env
DB_NAME
DB_USER
DB_PASSWORD
DB_HOST
DB_PORT
```

## Запуск сервиса
```bash
docker compose build
docker compose up
```


