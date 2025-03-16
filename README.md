## **Технологический стек**
- **Backend**: Django 3.2.16, Django REST Framework 3.12.4
- **Database**: PostgreSQL
- **Authentication**: Djoser 2.3.1 (JWT)
- **Infrastructure**: Docker, Docker Compose, Nginx, Gunicorn
- **CI/CD**: GitHub Actions, Docker Hub


## **Запуск проекта локально**

### **1. Клонировать репозиторий**
```sh
git clone https://github.com/kiryazb/foodgram.git
```
### **2. Переменные окружения**
Проект читает
```ini
DEBUG
SECRET_KEY
DB_NAME
DB_USER
DB_PASSWORD
DB_HOST
DB_PORT
DOCKER_USERNAME # Необходим для загрузки образов бекенда и фронтенда, можно указать мой (kiryazb)
```
### **3. Запустить проект в Docker**
```sh
docker-compose up -d --build
```
Проект будет доступ по адресу localhost:80
### **3. Django админка**
доступна прямо через gunicorn по адресу localhost:8000/admin

## **Docker Hub**
https://hub.docker.com/repository/docker/kiryazb/foodgram-backend
https://hub.docker.com/repository/docker/kiryazb/foodgram-frontend

## **Тестовые данные**
TEST_USERS = [
    {
        "email": "admin@example.com",
        "username": "admin",
        "password": "adminpass",
        "is_superuser": True,
        "is_staff": True,
    },
    {"email": "user1@example.com", "username": "user1", "password": "userpass"},
    {"email": "user2@example.com", "username": "user2", "password": "userpass"},
]

TEST_INGREDIENTS = [
    {"name": "Сахар", "measurement_unit": "г"},
    {"name": "Молоко", "measurement_unit": "мл"},
    {"name": "Яйцо", "measurement_unit": "шт"},
    {"name": "Мука", "measurement_unit": "г"},
]

TEST_RECIPES = [
    {"name": "Блины", "text": "Вкусные домашние блины", "cooking_time": 15},
    {"name": "Каша", "text": "Овсяная каша на молоке", "cooking_time": 10},
    {"name": "Омлет", "text": "Классический омлет с молоком", "cooking_time": 7},
]

## **CI/CD в проекте**

### **Тестирование Backend**
- 🔄 **Клонирование репозитория**
- 🛠 **Установка Python и зависимостей**
- 📏 **Проверка PEP8 (flake8)**
- 🧪 **Запуск тестов Django**

### **Сборка Docker**
- 🏗 **Сборка Backend-контейнера**
- 🎨 **Сборка Frontend-контейнера**
