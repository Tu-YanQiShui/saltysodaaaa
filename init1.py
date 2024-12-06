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
                       db='proj_db',
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
    user = session['username']
    #cursor = conn.cursor();
    #query = 'SELECT ts, blog_post FROM blog WHERE username = %s ORDER BY ts DESC'
    #cursor.execute(query, (user))
    #data = cursor.fetchall()
    #cursor.close()
    return render_template('home.html', username=user)

# task 2
@app.route('/find_single_item', methods=['GET', 'POST'])
def find_single_item():
    user = session['username']
    if(request.method == 'GET'):
        return render_template('find_single_item.html')
    item_id = request.form['item_id']
    cursor = conn.cursor();
    query = """SELECT p.shelfNum, p.roomNum 
            FROM Piece as p
            Where p.ItemID = %s"""
    cursor.execute(query, (item_id))
    location_list = cursor.fetchall()
    print(location_list)
    cursor.close()
    return render_template('find_single_item.html', locations = location_list)

# task 3
@app.route('/find_order_items', methods=['GET', 'POST'])
def find_order_items():
    user = session['username']
    if(request.method == 'GET'):
        return render_template('find_order_items.html')
    order_id = request.form['order_id']
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
    return render_template('find_order_items.html', data = item_dict)

@app.route('/post', methods=['GET', 'POST'])
def post():
    username = session['username']
    cursor = conn.cursor();
    blog = request.form['blog']
    query = 'INSERT INTO blog (blog_post, username) VALUES(%s, %s)'
    cursor.execute(query, (blog, username))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

@app.route('/select_blogger')
def select_blogger():
    #check that user is logged in
    #username = session['username']
    #should throw exception if username not found
    
    cursor = conn.cursor();
    query = 'SELECT DISTINCT username FROM blog'
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('select_blogger.html', user_list=data)

@app.route('/show_posts', methods=["GET", "POST"])
def show_posts():
    poster = request.args['poster']
    cursor = conn.cursor();
    query = 'SELECT ts, blog_post FROM blog WHERE username = %s ORDER BY ts DESC'
    cursor.execute(query, poster)
    data = cursor.fetchall()
    cursor.close()
    return render_template('show_posts.html', poster_name=poster, posts=data)


def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
	
@app.route('/')
def upload_form():
	return render_template('upload.html')

@app.route('/', methods=['POST'])
def upload_file():
	if request.method == 'POST':
        # check if the post request has the file part
		if 'file' not in request.files:
			flash('No file part')
			return redirect(request.url)
		file = request.files['file']
		if file.filename == '':
			flash('No file selected for uploading')
			return redirect(request.url)
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			flash('File successfully uploaded')
			return redirect('/')
		else:
			flash('Allowed file types are txt, pdf, png, jpg, jpeg, gif')
			return redirect(request.url)


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
