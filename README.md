# expert-system-for-diagnosing-ophthalmological-diseases

## Интеллектуальная информационная платформа поддержки принятия врачебных решений в области офтальмологии.

### Установка и запуск системы:

#### 1. Установка и настройка Docker

https://www.docker.com/products/docker-desktop/

##### Проверка установки:
```docker --version```<br>
```docker-compose --version```

#### 2. Получение исходного кода
```git clone https://github.com/517ANT39/expert-system-for-diagnosing-ophthalmological-diseases.git```

#### 3. Запуск системы и в контейнерах Docker
```docker-compose up --build```

#### 4. Проверка работоспособности (доступ к web-интерфейсу)
http://localhost:5000

#### 5. Остановка системы
```docker-compose down```<br>

***Примечание**: Для полной очистки системы с удалением образов используйте ```docker-compose down --rmi all```