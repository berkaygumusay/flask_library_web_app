
from multiprocessing import connection
import pstats
from sys import set_coroutine_origin_tracking_depth
from click import confirm
from flask import Flask,render_template,flash,redirect, render_template_string,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators,fields
from passlib.hash import sha256_crypt
from functools import wraps



class registerForm(Form):
    name = StringField("Name & Surname :",[validators.DataRequired()] )
    username = StringField("Username :",[validators.DataRequired()])
    email = StringField("Email Adress ",[validators.DataRequired()])
    password = PasswordField("Password :",[validators.DataRequired(),validators.EqualTo(fieldname= "confirm",message="Passwords Don't Match")])
    confirm = PasswordField("Repeat Password :")

class loginForm(Form):
    username = StringField("Username :")
    password = PasswordField("Password :")

class addbookForm(Form):
    title = StringField("Title Of The Book",[validators.DataRequired()])
    author = StringField("Author Of The Book",[validators.DataRequired()])
    content = TextAreaField("Content Of The Book",[validators.DataRequired()])
    genre = StringField("Genre Of The Book",[validators.DataRequired()])

app = Flask(__name__)

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "blogprojectusers"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
app.secret_key = "my super secret key"

mysql = MySQL(app)

#Login Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Please Log In","danger")
            return redirect(url_for("logIn"))
            
    return decorated_function

#Home Page
@app.route("/")
def mainPage():
    return render_template("index.html")

#Registration Page
@app.route("/signup",methods = ["GET","POST"])
def signUp():
    form = registerForm(request.form)
    if request.method == "POST" and form.validate():

        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()

        query = "Insert into users(name,username,email,password) VALUES(%s,%s,%s,%s)"

        cursor.execute(query,(name,username,email,password))

        mysql.connection.commit()

        cursor.close()

        flash("Signed Up Successfully","success")

        return redirect(url_for("logIn"))
    else:
        return render_template("register.html",form = form)

#Login Page
@app.route("/login",methods = ["GET","POST"])
def logIn():
    form = loginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password = form.password.data

        cursor = mysql.connection.cursor()

        query = "Select * From users where username = %s"

        result = cursor.execute(query,(username,))

        if result > 0 :
            data = cursor.fetchone()
            truePassword = data["password"]
            name = data["name"]
            if sha256_crypt.verify(password,truePassword):
                flash(" Welcome {} ".format(name),"success")
                
                session["logged_in"] = True
                session["username"] = username

                return redirect(url_for("mainPage"))
            else:
                flash(" Wrong Password ","danger")
                return redirect(url_for("logIn"))
        else:
            flash(" There Is No Such User ","danger")
            return redirect(url_for("logIn"))
    else:
         return render_template("login.html",form = form)

#Logout Page
@app.route("/logout")
def logOut():
    session.clear()
    flash(" Successfully Logged Out","success")
    return redirect(url_for("mainPage"))

#Dashboard Page
@app.route("/dashboard")
@login_required
def dashboardPage():
    return render_template("dashboard.html")

#Addbook Page
@app.route("/addbook",methods = ["GET","POST"])
@login_required
def addbookPage():
    form = addbookForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        author = form.author.data
        content = form.content.data
        genre = form.genre.data
        user = session["username"]

        cursor = mysql.connection.cursor()

        query = "Insert into books(title,author,content,genre,user) VALUES(%s,%s,%s,%s,%s)"

        cursor.execute(query,(title,author,content,genre,user))

        mysql.connection.commit()

        cursor.close()
        
        flash("Book Successfully Added","success")
    
        return redirect(url_for("dashboardPage"))
    else:
        return render_template("addbook.html",form = form)

#Findbook Page
@app.route("/books")
@login_required
def booksPage():
    cursor = mysql.connection.cursor()

    query = "Select * from books"

    result = cursor.execute(query)

    if result > 0:
        books = cursor.fetchall()
        return render_template("books.html",books = books)
    else:
        return render_template("books.html")

#Mybooks Page
@app.route("/mybooks")
@login_required
def mybooksPage():
    cursor = mysql.connection.cursor()

    query = "Select * from books where user = %s"

    result = cursor.execute(query,(session["username"],))

    if result > 0:
        books = cursor.fetchall()
        return render_template("mybooks.html",books = books)
    else:
        return render_template("mybooks.html")

#Content Page
@app.route("/book/<string:id>")
@login_required
def contentPage(id):
    cursor = mysql.connection.cursor()

    query = "Select * from books where id = %s"

    result = cursor.execute(query,(id,))

    if result > 0:
        book = cursor.fetchone()
        return render_template("content.html",book = book)
    else:
        return render_template("content.html")

#Deletebook Page
@app.route("/delete/<string:id>")
@login_required
def deletebookPage(id):
    cursor = mysql.connection.cursor()

    query = "Select * from books where user = %s and id = %s"

    result = cursor.execute(query,(session["username"],id))

    if result > 0 :
        query2 = "Delete from books where id = %s"
        cursor.execute(query2,(id,))
        mysql.connection.commit()

        return redirect(url_for("dashboardPage"))
    else:
        flash("You are not authorized for this operation","danger")
        return redirect(url_for("mainPage"))    

#Editbook Page
@app.route("/edit/<string:id>",methods=["GET","POST"])
@login_required
def editbookPage(id):
    #GET request part
    if request.method == "GET":
        cursor = mysql.connection.cursor()

        query = "Select * from books where id = %s and user = %s"
        result = cursor.execute(query,(id,session["username"]))
        
        if result == 0:
            flash("You are not authorized for this operation","danger")
            return redirect(url_for("mainPage"))
        else:
            book = cursor.fetchone()
            form = addbookForm()
            form.title.data = book["title"]
            form.content.data = book["content"]
            form.genre.data = book["genre"]
            form.author.data = book["author"]
            return render_template("edit.html",form=form)
    #POST request part
    else:
        form = addbookForm(request.form)
        updatedTitle = form.title.data
        updatedContent = form.content.data
        updatedAuthor = form.author.data
        updatedGenre = form.genre.data

        query2 = "Update books Set title = %s,content = %s,author = %s,genre = %s where id = %s"
        cursor = mysql.connection.cursor()
        cursor.execute(query2,(updatedTitle,updatedContent,updatedAuthor,updatedGenre,id))
        mysql.connection.commit()
        
        flash("Book Updated Successfully","success")
        return redirect(url_for("mybooksPage"))

#Search Page
@app.route("/search",methods=["GET","POST"])
@login_required
def searchPage():
    if request.method == "GET":
        flash("You are not authorized for this operation","danger")
        return redirect(url_for("mainPage"))
    else:
        keyword = request.form.get("keyword")
        keyword = str(keyword)
        cursor = mysql.connection.cursor()

        query = "Select * from books where title like '%"+ keyword +"%'"

        result = cursor.execute(query)

        if result == 0:
            flash("There is no such book in the system","danger")
            return redirect(url_for("booksPage"))
        else:
            books = cursor.fetchall()
            return render_template("books.html",books=books)
            


if __name__ == "__main__":
    app.run(debug=True)
