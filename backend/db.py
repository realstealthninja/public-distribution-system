import csv

import click
from flask import current_app, g
from oracledb import Connection, connect
from werkzeug.security import generate_password_hash


def get_db() -> Connection:
    if "db" not in g:
        g.db = connect(
            user="rationer",
            password="password",
            host="localhost",
        )

    return g.db


def insert_csv_data(file, query, cursor):
    data = list(map(tuple, list(csv.reader(file))[1:]))

    cursor.executemany(query, data)


def run_sql_script(file, cursor):
    statement_parts = []
    for line in file.readlines():
        if line.strip() == "/":
            statement = "".join(statement_parts).strip()
            if statement:
                try:
                    cursor.execute(statement)
                except:
                    print(f"Failed to execute SQL file({file.name}):", statement)
                    raise
            statement_parts = []
        else:
            statement_parts.append(line)


def init_db():
    db = get_db()

    with (
        current_app.open_resource("sql/schema.sql", "r") as schema,
        current_app.open_resource("sql/data/states.csv", mode="r") as states,
        current_app.open_resource("sql/data/districts.csv", "r") as districts,
        current_app.open_resource("sql/data/addresses.csv", "r") as addresses,
        current_app.open_resource("sql/data/distributors.csv", "r") as distributors,
        db.cursor() as cursor,
    ):
        run_sql_script(schema, cursor)

        insert_csv_data(states, "INSERT INTO state(state_name) VALUES(:state)", cursor)

        insert_csv_data(
            districts,
            "INSERT INTO district(district_name, state_id) VALUES(:district, (SELECT state_id FROM state WHERE state_name = :state))",
            cursor,
        )

        insert_csv_data(
            addresses,
            "INSERT INTO address(pincode, district_id) VALUES(:pincode, (SELECT district_id FROM district WHERE district_name = :district))",
            cursor,
        )

        insert_csv_data(
            distributors,
            "INSERT INTO distributor(distributor_name, address_id) VALUES(:distributor_name, (SELECT address_id FROM address WHERE pincode = :pincode))",
            cursor,
        )
        db.commit()


def drop_tables():
    db = get_db()
    with current_app.open_resource("sql/drop.sql", "r") as file, db.cursor() as cursor:
        run_sql_script(file, cursor)
        db.commit()


def create_admin(username, password):
    db = get_db()

    with db.cursor() as cursor:
        cursor.execute(
            "INSERT INTO admin(username, password) VALUES(:username, :password)",
            (
                username,
                generate_password_hash(password),
            ),
        )
        db.commit()


@click.command
def init_db_command():
    init_db()
    click.echo("Initialised the database.")


@click.command
def drop_tables_command():
    drop_tables()
    click.echo("Dropped all tables.")


@click.command()
@click.argument("username")
@click.argument("password")
def create_admin_command(username, password):
    create_admin(username, password)
    click.echo("Added admin user")


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(drop_tables_command)
    app.cli.add_command(create_admin_command)
