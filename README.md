## AI-Insights

This repository contains the backend code for the AI-Insights project. 

### Dependencies

To install the dependencies:

```bash
pip install -r requirements.txt
```

To add the dependency into requirements.txt:
```bash
pip freeze > requirements.txt
```

## Setup and Configuration

* Create a `.env` file in the project root directory with the keys just like 
shown in `.env.dev`
* Fill the values for each environment variable

## Data configuration
* Add all the data files `(.json)` inside `app/data` folder. 

## Use the project
* First, Install poetry using command `pip install poetry`
* Then run `poetry install` followed by `poetry shell`
* While in activated virtual environment, run the following command: `docker-compose up --remove-orphans -d`
* To run the project use command `poetry run run-app`


#### Database Migrations

The migrations are handled by Alembic. The migrations are stored in the `alembic` directory. To create a new migration, you can run the following command:

```bash
alembic revision --autogenerate -m "message"
```

This command will create a new migration file in the `alembic` directory. Run the migrations using the following command:

```bash
alembic upgrade head
```

If you need to downgrade the database or reset it. You can use `alembic downgrade -1` and `alembic downgrade base` respectively.

## If Docker taking more space?
Use:
`docker system prune -a`

