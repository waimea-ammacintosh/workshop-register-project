#===========================================================
# YOUR PROJECT TITLE HERE
# YOUR NAME HERE
#-----------------------------------------------------------
# BRIEF DESCRIPTION OF YOUR PROJECT HERE
#===========================================================

from flask import Flask, render_template, request, flash, redirect
import html

from app.helpers.session import init_session
from app.helpers.db      import connect_db
from app.helpers.errors  import init_error, not_found_error
from app.helpers.logging import init_logging
from app.helpers.time    import init_datetime, utc_timestamp, utc_timestamp_now


# Create the app
app = Flask(__name__)

# Configure app
init_session(app)   # Setup a session for messages, etc.
init_logging(app)   # Log requests
init_error(app)     # Handle errors and exceptions
init_datetime(app)  # Handle UTC dates in timestamps


#-----------------------------------------------------------
# Home page route
#-----------------------------------------------------------
@app.get("/")
def show_all_workshops():
    with connect_db() as client:
        # Get all the things from the DB
        sql = "SELECT id, name, date FROM workshop ORDER BY name ASC"
        params=[]
        result = client.execute(sql, params)
        workshops = result.rows

        # And show them on the page
        return render_template("pages/home.jinja", workshops=workshops)


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
                    "people".name AS p_name,
                    "people".phone AS phone,
                    "people".email AS email

                FROM
                    "people" AS people
                INNER JOIN workshop ON "people".workshop_id = workshop.id
                ORDER BY id ASC
                    """
        params=[]
        result = client.execute(sql, params)
        workshop = result.rows

    return render_template("pages/admin.jinja", registers=workshop)



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
    name  = request.form.get("name")
    phone = request.form.get("phone")
    email = request.form.get("email")
    

    # Sanitise the text inputs
    name = html.escape(name)

    with connect_db() as client:
        # Add the register to the DB
        sql = "INSERT INTO people (name, phone, email, workshop_id) VALUES (?, ?, ?, ?)"
        params = [name, phone, email, id]
        client.execute(sql, params)

        # Get the name of the workshop for the flash
        sql2 = "SELECT name FROM workshop WHERE id=?"
        params2 = [id]
        result = client.execute(sql2, params2)

        workshop = result.rows[0]

        # Go back to the home page
        flash(f"Registered for {workshop} workshop")
        return redirect(f"/workshop/{id}")


#-----------------------------------------------------------
# Route for deleting a thing, Id given in the route
#-----------------------------------------------------------
@app.get("/delete/<int:id>")
def delete_a_thing(id):
    with connect_db() as client:
        # Delete the thing from the DB
        sql = "DELETE FROM things WHERE id=?"
        params = [id]
        client.execute(sql, params)

        # Go back to the home page
        flash("Thing deleted", "success")
        return redirect("/things")

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
    time = request.form.get("time")

    

    # Sanitise the text inputs
    name = html.escape(name)

    with connect_db() as client:
        # Add the workshop to the DB
        sql = "INSERT INTO workshop (name, person, date, place, time) VALUES (?, ?, ?, ?, ?)"
        params = [name, person, date, place, time]
        client.execute(sql, params)

        # Get the name of the workshop for the flash
        sql2 = "SELECT name FROM workshop ORDER BY id DESC LIMIT 1"
        params2 = []
        result = client.execute(sql2, params2)

        workshop_name = result.rows[0]

        # Go back to the home page
        flash(f"Successfully added {workshop_name} workshop")
        return redirect("/admin")

