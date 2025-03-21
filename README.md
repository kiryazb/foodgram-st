## **Технологический стек**
- **СУБД**: PostgreSQL
- **Backend**: Django 3.2.16, Django REST Framework 3.12.4
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
Проект будет доступ по адресу [localhost:80](http://localhost:80)
### **3. Django админка**
доступна прямо через gunicorn по адресу [localhost:8000/admin](http://localhost:8000/admin)

Для импорта продуктов из json-фикстуры
```sh
python manage.py fill_test_data
```
