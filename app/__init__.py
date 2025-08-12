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
        sql = "SELECT id, name, date FROM workshops ORDER BY name ASC"
        result = client.execute(sql)
        workshops = result.rows

        # And show them on the page
        return render_template("pages/home.jinja", workshops=workshops)


#-----------------------------------------------------------
# Admin page route
#-----------------------------------------------------------
@app.get("/admin/")
def about():
    return render_template("pages/admin.jinja")


#-----------------------------------------------------------
# Things page route - Show all the things, and new thing form
#-----------------------------------------------------------
@app.get("/things/")
def show_all_things():
    with connect_db() as client:
        # Get all the things from the DB
        sql = "SELECT id, name FROM things ORDER BY name ASC"
        params = []
        result = client.execute(sql, params)
        things = result.rows

        # And show them on the page
        return render_template("pages/things.jinja", things=things)


#-----------------------------------------------------------
# Thing page route - Show details of a single thing
#-----------------------------------------------------------
@app.get("/workshop/<int:id>")
def show_one_workshop(id):
    with connect_db() as client:
        # Get the thing details from the DB
        sql = "SELECT id, name, person, date FROM workshops WHERE id=?"
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
# Route for adding a thing, using data posted from a form
#-----------------------------------------------------------
@app.post("/register")
def add_a_thing(id):
    # Get the data from the form
    name  = request.form.get("name")
    phone = request.form.get("phone")
    email = request.form.get("email")
    

    # Sanitise the text inputs
    name = html.escape(name)

    with connect_db() as client:
        # Add the thing to the DB
        sql = "INSERT INTO people (name, phone, email, workshop_id) VALUES (?, ?, ?, ?)"
        params = [name, phone, email, id]
        client.execute(sql, params)

        # Get the name of the workshop for the flash
        sql2 = "SELECT name FROM workshops WHERE id=?"
        params2 = [id]
        result = client.execute(sql2, params2)

        workshop = result.name

        # Go back to the home page
        flash(f"Registered for {workshop} workshop")
        return redirect("/workshop")


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


