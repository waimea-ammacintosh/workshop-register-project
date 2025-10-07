#===========================================================
# YOUR PROJECT TITLE HERE
# YOUR NAME HERE
#-----------------------------------------------------------
# BRIEF DESCRIPTION OF YOUR PROJECT HERE
#===========================================================

from flask import Flask, render_template, request, flash, redirect, session
import html

from app.helpers.session import init_session
from app.helpers.db      import connect_db
from app.helpers.errors  import init_error, not_found_error
from app.helpers.logging import init_logging
from app.helpers.dates   import init_datetime, utc_datetime_str, utc_date_str, utc_time_str
from os import getenv

# Create the app
app = Flask(__name__)

# Configure app
init_session(app)   # Setup a session for messages, etc.
init_logging(app)   # Log requests
init_error(app)     # Handle errors and exceptions
init_datetime(app)  # Handle UTC dates in timestamps


# get the admin password and username form the env
ADMIN_P = getenv("ADMIN_P")
ADMIN_U = getenv("ADMIN_U")

#-----------------------------------------------------------
# Home page route
#-----------------------------------------------------------
@app.get("/")
def show_all_workshops():
    with connect_db() as client:
        # Get all the things from the DB
        sql = "SELECT id, name, date FROM workshop WHERE date >= DATE('now') ORDER BY name ASC"
        params=[]
        result = client.execute(sql, params)
        workshops = result.rows

        # And show them on the page
        return render_template("pages/home.jinja", workshops=workshops)

#-----------------------------------------------------------
# Login page route
#-----------------------------------------------------------
@app.get("/log-in/")
def show_login():
    return render_template("pages/log-in.jinja")


#-----------------------------------------------------------
# Route for signing into admin, checks username and password
#-----------------------------------------------------------
@app.post("/log-in/")
def login():
    # Get the data from the form
    username  = request.form.get("username")
    password = request.form.get("password")

        
    if password == ADMIN_P and username == ADMIN_U:
        session["logged_in"] = True
        # Go to admin page
        flash("Log in successful")
        return redirect("/admin/")
    
    else:
        # Ask to try again
        flash("Log in unsuccessful, please try again")
        return redirect("/log-in/")


#-----------------------------------------------------------
# Route for logging out of admin, checks username and password
#-----------------------------------------------------------
@app.get("/log-out/")
def logout():
    session.clear()
    flash("Logged out!")
    return redirect("/")


#-----------------------------------------------------------
# Admin page route
#-----------------------------------------------------------
@app.get("/admin/")
def admin():
    with connect_db() as client:
        # Get all the things from the DB
        sql = """SELECT
                    workshop.id AS id,
                    workshop.name AS w_name,
                    people.name AS f_name,
                    people.last_name AS l_name,
                    people.phone AS phone,
                    people.email AS email

                FROM
                    people AS people
                FULL JOIN workshop ON people.workshop_id = workshop.id

                WHERE workshop.date >= DATE('now')

                ORDER BY id, l_name ASC
                    """
        params=[]
        result = client.execute(sql, params)
        workshop = result.rows

        sql2 = "SELECT name FROM workshop WHERE workshop.date < DATE('now')"
        params2=[]
        old_workshops = client.execute(sql2, params2)



    return render_template("pages/admin.jinja", registers=workshop, old=old_workshops)



#-----------------------------------------------------------
# Workshop page route - Show details of a single workshop
#-----------------------------------------------------------
@app.get("/workshop/<int:id>")
def show_one_workshop(id):
    with connect_db() as client:
        # Get the thing details from the DB
        sql = "SELECT * FROM workshop WHERE id=?"
        params = [id]
        result = client.execute(sql, params)

        # Did we get a result?
        if result.rows:
            # yes, so show it on the page
            workshop = result.rows[0]
            return render_template("pages/workshop.jinja", workshop=workshop)

        else:
            # No, so show error
            return not_found_error()


#-----------------------------------------------------------
# Register page route
#-----------------------------------------------------------
@app.get("/register/<int:id>")
def show_register(id):
    return render_template("pages/register.jinja", id=id)


#-----------------------------------------------------------
# Route for registering a person, using data posted from a form
#-----------------------------------------------------------
@app.post("/register/<int:id>")
def register_a_person(id):
    # Get the data from the form
    name  = request.form.get("f_name")
    l_name = request.form.get("l_name")
    phone = request.form.get("phone")
    email = request.form.get("email")
    

    # Sanitise the text inputs
    name = html.escape(name)

    with connect_db() as client:
        # Add the register to the DB
        sql = "INSERT INTO people (name, last_name, phone, email, workshop_id) VALUES (?, ?, ?, ?, ?)"
        params = [name, l_name, phone, email, id]
        client.execute(sql, params)

        # Get the name of the workshop for the flash
        sql2 = "SELECT name FROM workshop WHERE id=?"
        params2 = [id]
        result = client.execute(sql2, params2)

        workshop = result.rows[0]
        cleaned_name = (''.join(workshop))

        # Go back to the home page
        flash(f"You are Now Registered for {cleaned_name} workshop")
        return redirect(f"/workshop/{id}")


#-----------------------------------------------------------
# delete page route
#-----------------------------------------------------------
@app.get("/delete/")
def show_delete():
    with connect_db() as client:
        # Get all the things from the DB
        sql = "SELECT id, name FROM workshop ORDER BY name ASC"
        params=[]
        result = client.execute(sql, params)
        workshops = result.rows
    return render_template("pages/delete.jinja", workshops=workshops)


#-----------------------------------------------------------
# Route for deleting a workshop, Id given in the route
#-----------------------------------------------------------
@app.get("/delete/<int:id>")
def delete_a_thing(id):
    with connect_db() as client:
        # Get name for flash
        sql = "SELECT name FROM workshop WHERE id=?"
        params = [id]
        result = client.execute(sql, params)
        workshop = result.rows[0]
        cleaned_name = (''.join(workshop))

        # Delete the thing from the DB
        sql2 = "DELETE FROM workshop WHERE id=?"
        params2 = [id]
        client.execute(sql2, params2)

        # Go back to the home page
        flash(f"{cleaned_name} workshop deleted", "success")
        return redirect("/delete")

#-----------------------------------------------------------
# New Workshop page route
#-----------------------------------------------------------
@app.get("/new")
def show_new_workshop_form():
    return render_template("pages/new.jinja")


#-----------------------------------------------------------
# Route for adding a new workshop, using data posted from a form
#-----------------------------------------------------------
@app.post("/workshop")
def add_a_workshop():
    # Get the data from the form
    name  = request.form.get("name")
    person = request.form.get("person")
    date = request.form.get("date")
    place = request.form.get("place")
    start_time = request.form.get("start_time")
    end_time = request.form.get("end_time")

    

    # Sanitise the text inputs
    name = html.escape(name)

    with connect_db() as client:
        # Add the workshop to the DB
        sql = "INSERT INTO workshop (name, person, date, place, start_time, end_time) VALUES (?, ?, ?, ?, ?, ?)"
        params = [name, person, date, place, start_time, end_time]
        client.execute(sql, params)

        # Get the name of the workshop for the flash
        sql2 = "SELECT name FROM workshop ORDER BY id DESC LIMIT 1"
        params2 = []
        result = client.execute(sql2, params2)

        workshop_name = result.rows[0]
        cleaned_name = (''.join(workshop_name))

        # Go back to the home page
        flash(f"Successfully added {cleaned_name} workshop")
        return redirect("/admin/")

