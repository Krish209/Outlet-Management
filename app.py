from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from datetime import datetime
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'  # MySQL host
app.config['MYSQL_USER'] = 'root'   # MySQL username
app.config['MYSQL_PASSWORD'] = 'Krish@2092003'  # MySQL password
app.config['MYSQL_DB'] = 'outlet_management'  # MySQL database name

mysql = MySQL(app)

app.secret_key = "supersecretkey"


# Email configurations
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_email_password'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False


def send_email(subject, recipient, body):
    sender_email = app.config['MAIL_USERNAME']
    sender_password = app.config['MAIL_PASSWORD']
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    print("Attempting to send email...")
    print(f"Sender Email: {sender_email}")
    print(f"Recipient Email: {recipient}")
    print(f"Subject: {subject}")
    print(f"Body: {body}")
    
    try:
        server = smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {e}")
      
        
def get_stakeholder_id(email):
    cur = mysql.connection.cursor()
    cur.execute("SELECT stakeholder_id FROM stakeholder WHERE email = %s", (email,))
    result = cur.fetchone()
    cur.close()
    if result:
        return result[0]
    else:
        return None
    


@app.route("/")
def login():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login_user():
    email = request.form.get("username")
    password = request.form.get("password")
    user_type = request.form.get("userType")
    cur = mysql.connection.cursor()

    if user_type == "stakeholder":
        # cur.execute("SELECT * FROM stakeholder WHERE email = %s AND password = %s", (email, password))
        query = f"SELECT * FROM stakeholder WHERE email = '{email}' and password = '{password}'"
        # print(query)
        cur.execute(query)
        stakeholder = cur.fetchone()
        cur.close()
            
        if stakeholder:
            # Store user information in session
            session['email'] = email
            session['user_type'] = 'stakeholder'
            return """
            <script>
            alert("Successfully login to Stakeholder dashboard");
            window.location.href = "{}";
            </script>
            """.format(url_for("outlet_management"))
        
        else:
            return """
            <script>
            alert("Login Failed");
            window.location.href = "/";
            </script>
            """
        
    elif user_type == "student":
        cur.execute("SELECT * FROM student_credentials WHERE email = %s AND password = %s", (email, password))
        student = cur.fetchone()
        cur.close()
            
        if student:
            # Store user information in session
            session['email'] = email
            session['user_type'] = 'student'
            return """
            <script>
            alert("Successfully login to Student dashboard");
            window.location.href = "{}";
            </script>
            """.format(url_for("outlet_management"))
        else:
            return """
            <script>
            alert("Login Failed");
            window.location.href = "/";
            </script>
            """
    else:
        return """
        <script>
        alert("Invalid User Type");
        window.location.href = "/";
        </script>
        """


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form['fullname']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirmPassword']
        user_type = request.form['userType']

        # Check if passwords match
        if password != confirm_password:
            flash("Passwords do not match. Please try again.")
            return redirect(url_for("signup"))

        cur = mysql.connection.cursor()
        # Check if the email already exists
        cur.execute("SELECT * FROM student_credentials WHERE email = %s", (email,))
        existing_user = cur.fetchone()

        if existing_user:
            flash("Email already exists. Please use a different email.")
            return redirect(url_for("signup"))
        else:
            # Insert the new user into the student_credentials table
            cur.execute("INSERT INTO student_credentials (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
            mysql.connection.commit()
            
            print("New user registered. Sending confirmation email...")  # Add this line for debugging
            
            # Send confirmation email
            subject = "Welcome to Outlet Management System"
            body = f"Hello {name},\n\nYour account has been successfully created. You can now log in using your email and password.\n\nBest regards,\nOutlet Management Team"
            send_email(subject, email, body)
        
        cur.close()

        return """
        <script>
        alert("Signup successful. You can now login.");
        window.location.href = "{}";
        </script>
        """.format(url_for("login"))

    return render_template("signup.html")


@app.route("/outlet_management", methods=['GET', 'POST'])
def outlet_management():
    cur = mysql.connection.cursor()
    user_type = session.get('user_type','guest')
    # Check if it's a POST request to handle the search, otherwise display all records
    if request.method == 'POST':
        search_term = request.form['searchInput']
        query = f"SELECT Outlet_ID, Outlet_name, Location_name, Contact_No, timings, Ratings FROM Outlet WHERE Outlet_name LIKE '%{search_term}%'"
    else:
        query = "SELECT Outlet_ID, Outlet_name, Location_name, Contact_No, timings, Ratings FROM Outlet"
    cur.execute(query)
    outlets = cur.fetchall()
    cur.close()
    return render_template("outlet_management.html", user_type=user_type,outlets=outlets)


# RENAME FEATURE
@app.route("/rename_column", methods=["POST"])
def rename_column():
    new_column_name = request.json.get("newColumnName")
    if new_column_name:
        cur = mysql.connection.cursor()
        # First, rename the column
        cur.execute("ALTER TABLE outlet CHANGE COLUMN Outlet_name {} VARCHAR(50)".format(new_column_name))

        mysql.connection.commit()
        cur.close()
        return "Column renamed successfully"
    else:
        return "Invalid column name"
    
    
#INSERT FEATURE
@app.route('/insert_outlet', methods = ['POST'])
def insert_outlet():
    if request.method == "POST":
        name = request.form['name']
        Location = request.form['Location']
        Contact = request.form['Contact']
        Timings = request.form['Timings']
        Contact = request.form['Contact']
        Rating  = float(request.form['Rating'])
        # import random
        # stakeholder_id = random.randint(1, 15)
        stakeholder_id = session.get("stakeholder_id")
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO Outlet (Stakeholder_ID, Outlet_name, Location_name, Contact_No, timings, Ratings) VALUES (%s, %s, %s, %s, %s, %s)", (stakeholder_id, name, Location, Contact, Timings, Rating))
        mysql.connection.commit()
        return redirect(url_for('outlet_management'))


#DELETE FEATURE
    
# CASCADE Method
    
#DELETE FEATURE
@app.route('/delete/<string:id_data>', methods=['GET'])
def delete(id_data):
    flash("Record Has been Deleted Successfully")
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM Outlet WHERE Outlet_ID = %s", (id_data,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('outlet_management'))



# Temporarily disable foreign key constraints before deleting the record and then re-enable them afterward.
# It's working properly but not the CASCADE
    
# @app.route('/delete/<string:id_data>', methods=['GET'])
# def delete(id_data):
#     try:
#         # Disable foreign key checks
#         cur = mysql.connection.cursor()
#         cur.execute("SET FOREIGN_KEY_CHECKS = 0")
        
#         # Delete the record
#         cur.execute("DELETE FROM Outlet WHERE Outlet_ID = %s", (id_data,))
#         mysql.connection.commit()
#         cur.close()
        
#         # Re-enable foreign key checks
#         cur = mysql.connection.cursor()
#         cur.execute("SET FOREIGN_KEY_CHECKS = 1")
#         cur.close()
#     except Exception as e:
#         # If an error occurs, rollback the changes and re-enable foreign key checks
#         mysql.connection.rollback()
#         flash("Error deleting record: {}".format(str(e)))
#     return redirect(url_for('outlet_management'))


#UPDATE FEATURE
@app.route('/update_outlet', methods = ['POST', 'GET'])
def update():
    if request.method == "POST":
        id_data  = request.form['id']
        name = request.form['name']
        Location = request.form['Location']
        Contact = request.form['Contact']
        Timings = request.form['Timings']
        Contact = request.form['Contact']
        Rating  = float(request.form['Rating'])
        # import random
        # stakeholder_id = random.randint(1, 15)
        stakeholder_id = session.get("stakeholder_id")
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE Outlet SET Outlet_name=%s, Location_name=%s, Contact_No=%s, timings=%s, Ratings=%s
            WHERE Outlet_ID LIKE %s
            """, (name, Location, Contact, Timings, Rating, id_data))

        flash("Data Updated Successfully")
        mysql.connection.commit()
        return redirect(url_for('outlet_management'))

    

@app.route("/stakeholder_details", methods=['GET', 'POST'])
def  stakeholder_details():
    cur = mysql.connection.cursor()
    user_type = session.get('user_type','guest')
    if request.method == 'POST':
        search_term = request.form['searchInput']
        search_field = request.form['searchField']
        if search_field == 'name':
            query = f"SELECT * FROM stakeholder WHERE name LIKE '%{search_term}%'"
        elif search_field == 'position':
            query = f"SELECT * FROM stakeholder WHERE position LIKE '%{search_term}%'"
        else:
            query = "SELECT * FROM stakeholder"
    else:
        query = "SELECT * FROM stakeholder"
    cur.execute(query)  # Adjust 'stakeholders' to your table name
    data = cur.fetchall()
    cur.close()
    return render_template("stakeholder_details.html",user_type=user_type, data=data)


#INSERT stakeholder  FEATURE
@app.route('/insert_stakeholder', methods = ['POST'])
def insert_stakeholder():
    if request.method == "POST":
        name = request.form['name']
        Emailid = request.form['email']
        Position = request.form['position']
        Entrydate = request.form['entry_date']
        Exitdate = request.form['exit_date']
          # Convert string dates to Python datetime objects
        Entrydate = datetime.strptime(Entrydate, '%Y-%m-%d').date()
        Exitdate = datetime.strptime(Exitdate, '%Y-%m-%d').date()
        stakeholder_id = session.get("stakeholder_id")
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO stakeholder (name, email,position, entry_date, exit_date) VALUES (%s, %s, %s, %s, %s)",(name,Emailid,Position, Entrydate,Exitdate))
        mysql.connection.commit()
        return redirect(url_for('stakeholder_details'))
    

    
@app.route("/inventory_details", methods=['GET', 'POST'])
def inventory_details():
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        search_term = request.form['searchInput']
        query = """
        SELECT o.Outlet_name, i.Item_name, i.Price
        FROM Inventory i
        JOIN Outlet o ON i.Outlet_ID = o.Outlet_ID
        WHERE LOWER(i.Item_name) LIKE %s
        """
        cur.execute(query, [search_term])
    else:
        query = """
        SELECT o.Outlet_name, i.Item_name, i.Price
        FROM Inventory i
        JOIN Outlet o ON i.Outlet_ID = o.Outlet_ID
        """
        cur.execute(query)

    items = cur.fetchall()
    cur.close()
    return render_template("Inventory.html", items=items)



@app.route("/employee_details", methods=['GET', 'POST'])
def employee_details():
    cur = mysql.connection.cursor()

    # Check if it's a POST request to handle the search, otherwise display all records
    if request.method == 'POST':
        search_term = request.form['searchInput']
        column_name = request.form['searchColumn']

        query = f"""
        SELECT o.Outlet_name, e.Employee_name, e.Role, e.Mobile_number, e.Shift_time
        FROM Employees e
        JOIN Outlet o ON e.Outlet_ID = o.Outlet_ID
        WHERE {column_name} LIKE %s
        """
        cur.execute(query, ['%' + search_term + '%'])
    else:
        query = """
        SELECT o.Outlet_name, e.Employee_name, e.Role, e.Mobile_number, e.Shift_time
        FROM Employees e
        JOIN Outlet o ON e.Outlet_ID = o.Outlet_ID
        """
        cur.execute(query)

    employees = cur.fetchall()
    cur.close()
    return render_template("employees_details.html", employees=employees)


@app.route("/Customer_feedback", methods=['GET', 'POST'])
def Customer_feedback():
    cur = mysql.connection.cursor()
    
    # Check if it's a POST request to handle the search, otherwise display all records
    if request.method == 'POST':
        search_term = request.form['searchInput']
        query = """
        SELECT o.Outlet_name, cf.Customer_email, cf.Customer_rating
        FROM Customer_feedback cf
        JOIN Outlet o ON cf.Outlet_ID = o.Outlet_ID
        WHERE LOWER(o.Outlet_name) LIKE %s
        """
        cur.execute(query, ['%' + search_term + '%'])
    else:
        query = """
        SELECT o.Outlet_name, cf.Customer_email, cf.Customer_rating
        FROM Customer_feedback cf
        JOIN Outlet o ON cf.Outlet_ID = o.Outlet_ID
        """
        cur.execute(query)

    feedback_data = cur.fetchall()
    cur.close()
    return render_template("Customer_feedback.html", feedback_data=feedback_data)


@app.route("/Rent_details", methods=['GET', 'POST'])
def Rent_details():
    cur = mysql.connection.cursor()
    
    # Adjust the query based on whether it's a POST request (search operation) or not
    if request.method == 'POST':
        search_term = request.form['searchInput']
        search_mode = request.form['searchMode']  # Get the mode of payment search term
        query = """
        SELECT Rent_payment.Outlet_ID, Outlet.Outlet_name, Rent_payment.Mode_of_payment, 
               Rent_payment.Paid_amount, Rent_payment.Rent_from_date, Rent_payment.Rent_to_date, 
               Rent_payment.Due_amount
        FROM Rent_payment
        INNER JOIN Outlet ON Rent_payment.Outlet_ID = Outlet.Outlet_ID
        WHERE Outlet.Outlet_name LIKE %s
        AND Rent_payment.Mode_of_payment LIKE %s
        """
        cur.execute(query, ('%' + search_term + '%', '%' + search_mode + '%'))
    else:
        query = """
        SELECT Rent_payment.Outlet_ID, Outlet.Outlet_name, Rent_payment.Mode_of_payment, 
               Rent_payment.Paid_amount, Rent_payment.Rent_from_date, Rent_payment.Rent_to_date, 
               Rent_payment.Due_amount
        FROM Rent_payment
        INNER JOIN Outlet ON Rent_payment.Outlet_ID = Outlet.Outlet_ID
        """
        cur.execute(query)
    
    rent_payments = cur.fetchall()
    cur.close()
    return render_template("Rent_payment.html", rent_payments=rent_payments)


@app.route("/Survey_details", methods=['GET', 'POST'])
def Survey_details():
    cur = mysql.connection.cursor()
    user_type= session.get('user_type','guest')
    
    if request.method == 'POST':
        outlet_name = request.form.get('outletName', '')  #To avoid Key error exception hence used get too.
        warning_issued = request.form.get('warningIssued', '')  
        
        # Base query
        query = """
        SELECT s.Survey_ID, o.Outlet_name, s.Date_of_survey, st.name, s.Description, s.Warning_issued, s.Penalty_amount
        FROM Survey s
        JOIN Outlet o ON s.Outlet_ID = o.Outlet_ID
        JOIN Stakeholder st ON s.Stakeholder_ID = st.Stakeholder_ID
        WHERE 1=1
        """
        
        # Filtering conditions to avoid SQL injection hence DYnamic Query
        parameters = []
        if outlet_name:
            query += " AND o.Outlet_name LIKE %s"
            parameters.append('%' + outlet_name + '%')
        if warning_issued in ['Yes', 'No']:
            query += " AND s.Warning_issued = %s"
            parameters.append(warning_issued)
        
        cur.execute(query, parameters)
    else:
        # Initial page load without any filters
        query = """
        SELECT s.Survey_ID, o.Outlet_name, s.Date_of_survey, st.name, s.Description, s.Warning_issued, s.Penalty_amount
        FROM Survey s
        JOIN Outlet o ON s.Outlet_ID = o.Outlet_ID
        JOIN Stakeholder st ON s.Stakeholder_ID = st.Stakeholder_ID
        """
        cur.execute(query)

    surveys = cur.fetchall()
    cur.close()
    return  render_template("survey.html",user_type=user_type,surveys=surveys)

if __name__ == "__main__":
    app.run(debug=True)