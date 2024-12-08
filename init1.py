#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect, flash
import pymysql.cursors
import uuid
import hashlib
import os
import base64

#for uploading photo:
from app import app
#from flask import Flask, flash, request, redirect, render_template
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


###Initialize the app from Flask
##app = Flask(__name__)
##app.secret_key = "secret key"

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       port = 3306,
                       user='root',
                       password='93400819',
                       db='p3db',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)


def allowed_image(filename):

    if not "." in filename:
        return False

    ext = filename.rsplit(".", 1)[1]

    if ext.upper() in app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        return True
    else:
        return False


def allowed_image_filesize(filesize):

    if int(filesize) <= app.config["MAX_IMAGE_FILESIZE"]:
        return True
    else:
        return False


#Define a route to hello function
@app.route('/')
def hello():
    # return ('hello world')
    return render_template('index.html')

#Define route for login
@app.route('/login')
def login():
    return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
    return render_template('register.html')

def encrypt_pass(password):
    algorithm = 'sha256'
    salt = base64.b64encode(os.urandom(4)).decode('utf-8')
    hash_obj = hashlib.new(algorithm)
    password_salted = salt + password
    hash_obj.update(password_salted.encode('utf-8'))
    password_hash = base64.b64encode(hash_obj.digest()).decode('utf-8')

    password_db_string = f"{algorithm}${salt}${password_hash}"
    return password_db_string

def verify_pass(hashed_password, input_password):
    algorithm, salt, stored_hash = hashed_password.split('$')
    hash_obj = hashlib.new(algorithm)
    password_salted = salt + input_password
    hash_obj.update(password_salted.encode('utf-8'))
    input_password_hash = base64.b64encode(hash_obj.digest()).decode('utf-8')
    password_db_string = f"{algorithm}${salt}${input_password_hash}"
    return password_db_string == hashed_password

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM Person WHERE userName = %s'
    cursor.execute(query, (username))
    #stores the results in a variable
    data = cursor.fetchone()
    print(data)
    #use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None
    if(data):
        # check if password is correct
        stored_password = data['password']
        if(verify_pass(stored_password,password)):
            # if password match, set the session
            session['username'] = username
            return redirect(url_for('home'))
        else:
            error = 'Invalid password'
            return render_template('login.html', error=error)
    else:
        #returns an error message to the html page
        error = 'Invalid login or username'
        return render_template('login.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #grabs information from the forms
    username = request.form['username']
    password = encrypt_pass(request.form['password'])
    print(password)
    fname = request.form['fname']
    lname = request.form['lname']
    email = request.form['email']
    role = request.form['role']
    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM Person WHERE username = %s'
    cursor.execute(query, (username))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    error = None
    if(data):
        #If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        ins = 'INSERT INTO person VALUES(%s, %s, %s, %s, %s)'
        ins_act = 'INSERT INTO Act VALUES(%s,%s)'
        cursor.execute(ins, (username, password, fname, lname, email))
        # update the act table with user-role
        cursor.execute(ins_act, (username, role))
        conn.commit()
        cursor.close()
        return render_template('index.html')


@app.route('/home')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    user = session['username']
    return render_template('home.html', username=user)

# task 2
@app.route('/find_single_item', methods=['GET', 'POST'])
def find_single_item():
    user = session['username']
    if not user:
        return redirect(url_for('login'))
    if(request.method == 'GET'):
        return render_template('find_single_item.html', locations = [])
    item_id = request.form['item_id']
    print(item_id)
    cursor = conn.cursor();

    item_query = "SELECT * FROM Item WHERE ItemID = %s"
    cursor.execute(item_query, (item_id,))
    item = cursor.fetchone()

    if not item:
        error = "This item does not exist in the database."
        return render_template('find_single_item.html', locations=[], error=error)

    query = """SELECT p.shelfNum, p.roomNum 
            FROM Piece as p
            Where p.ItemID = %s"""
    cursor.execute(query, (item_id,))
    location_list = cursor.fetchall()
    print(location_list)
    cursor.close()
    if not location_list:
        error = 'This item exist, but there is no data for piece locations'
        return render_template('find_single_item.html', locations=[], error=error)
    return render_template('find_single_item.html', locations = location_list)

# task 3
@app.route('/find_order_items', methods=['GET', 'POST'])
def find_order_items():
    user = session['username']
    if not user:
        return redirect(url_for('login'))
    if(request.method == 'GET'):
        return render_template('find_order_items.html',data = {})
    
    order_id = request.form['order_id']
    print(order_id)
    cursor = conn.cursor();
    query = """
    SELECT i.ItemID, p.roomNum, p.shelfNum
    FROM Piece as p Natural Join ItemIn as i
    WHERE i.orderID = %s
    """
    cursor.execute(query, (order_id))
    location_list = cursor.fetchall()
    cursor.close()
    item_dict = {}
    for piece in location_list:
        item_id = piece['ItemID']
        room_shelf = (piece['roomNum'], piece['shelfNum'])
        item_dict.setdefault(item_id, []).append(room_shelf)
    print(item_dict)
    if not item_dict:
        error = 'This order does not exist'
        return render_template('find_order_items.html', data = {}, error=error)
    return render_template('find_order_items.html', data = item_dict)

# task 4
@app.route('/accept_donation', methods=['GET', 'POST'])
def accept_donation():
    username = session['username']
    if not username:
        return redirect(url_for('login'))
    cursor = conn.cursor();
    # check if the user is staff
    # I assume a user cannot be staff and volunteer at the same time
    query = """SELECT roleID from Act as a
    WHERE a.userName = %s
    """
    cursor.execute(query, username)
    role = cursor.fetchone()
    print(role.get('roleID'))
    if not role or role.get('roleID') != "staff":
        error = 'Only staff could view accept donation page'
        return redirect(url_for('home'))

    if(request.method == 'GET'):
        return render_template('accept_donation.html', items_with_pieces={})

    if(role.get('roleID') == "staff"):
        donor_id = request.form['donor_id']
        cursor.execute("SELECT userName FROM Act WHERE userName = %s and roleID = 'donor'", (donor_id,))
        donor = cursor.fetchone()
        if not donor:
            error = "The provided donor ID is not valid or does not have the 'donor' role."
            return render_template('accept_donation.html', error=error)
        item_description = request.form['item_description']
        photo = request.form['photo']
        color = request.form['color']
        is_new = request.form['is_new'] == 'true'
        has_pieces = request.form['has_pieces'] == 'true'
        material = request.form.get('material')
        main_category = request.form['main_category']
        sub_category = request.form['sub_category']

        cursor.execute("""
            SELECT mainCategory, subCategory FROM Category
            WHERE mainCategory = %s AND subCategory = %s
        """, (main_category, sub_category))
        category = cursor.fetchone()

        if not category:
            cursor.execute("""
                INSERT INTO Category (mainCategory, subCategory, catNotes)
                VALUES (%s, %s, %s)
            """, (main_category, sub_category, "Automatically added from donation form."))
            conn.commit()

        cursor.execute("""
            INSERT INTO Item (iDescription, photo, color, isNew, hasPieces, material, mainCategory, subCategory)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (item_description, photo, color, is_new, has_pieces, material, main_category, sub_category))
        conn.commit()

        item_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO DonatedBy (ItemID, userName, donateDate)
            VALUES (%s, %s, CURDATE())
        """, (item_id, donor_id))
        conn.commit()

        cursor.close()

        return redirect(url_for('home'))

# task 10
@app.route('/update_orders', methods=['GET', 'POST'])
def update_orders():
    username = session['username']
    if not username:
        return redirect(url_for('login'))

    cursor = conn.cursor()

    if request.method == 'POST':
        order_id = request.form['order_id']
        cursor.execute("SELECT status FROM Delivered WHERE orderID = %s AND userName = %s", (order_id, username))
        current_status = cursor.fetchone()

        if current_status:
            new_status = 'shipped' 
            if current_status['status'] == 'shipped':
                new_status = 'not yet shipped'
            cursor.execute(
                "UPDATE Delivered SET status = %s WHERE orderID = %s AND userName = %s",
                (new_status, order_id, username)
            )
            conn.commit()

    query = """
        SELECT o.orderID, o.orderDate, o.orderNotes, d.status
        FROM Ordered AS o
        NATURAL JOIN Delivered AS d
        WHERE o.supervisor = %s
    """
    cursor.execute(query, (username,))
    orders = cursor.fetchall()
    cursor.close()

    return render_template('update_orders.html', orders=orders)

# task 11
@app.route('/year_report', methods=['GET'])
def year_report():
    username = session['username']
    if not username:
        return redirect(url_for('login'))
    cursor = conn.cursor()
    # calculate number of clients
    query = """
        SELECT COUNT(Distinct userName) as co
        FROM Person as p NATURAL JOIN ACT as c
        WHERE roleID = %s
    """
    cursor.execute(query, ("client",))
    client_num = cursor.fetchone()['co']

    # number of items each category donated
    query = """
        SELECT LOWER(mainCategory) AS mc, COUNT(*) AS donation_count
        FROM Item
        GROUP BY LOWER(mainCategory)
    """
    cursor.execute(query)
    category_count = cursor.fetchall()
    print(category_count)

    # number of small pieces (with both length and width less than 50)
    query = """
        SELECT COUNT(*) AS small_count
        FROM Piece
        WHERE length < 50 AND width < 50;
    """
    cursor.execute(query)
    small = cursor.fetchall()
    print(category_count)

    # the most popular role
    query = """
        WITH r_count AS (
            SELECT roleID, COUNT(*) AS c
            FROM Act
            GROUP BY roleID
        )
        SELECT roleID, c
        FROM r_count
        WHERE c = (SELECT MAX(c) FROM r_count)
    """
    cursor.execute(query)
    popular = cursor.fetchall()
    cursor.close()
    return render_template('year_report.html', client_num = client_num, category_count = category_count, small = small, popular = popular)
    


@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')
        
app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
