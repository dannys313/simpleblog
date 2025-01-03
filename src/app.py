# Route for handling the login page logic
from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
import os
import fileprocessing
import secrets
import time

print("starting up")

app = Flask(__name__, static_url_path='/static')
bootstrap = Bootstrap5(app)

# (user, key, time created)
authorized_cookies = []

#check cookie to see if user is logged in
def checkAuth(cookie):
    auth = False
    if (not (cookie == None)):
        #loop though cookies to see if one matches
        for c in authorized_cookies:
            if cookie == c[1]:
                auth = c[0]
                print("authenticated "+auth+" with cookie")
                break
    if auth == False:
        print("cookie invalid")
    return auth #return user

print("creating routes")

#root route
@app.route("/")
def root():
    #if no users exist prompt to create one
    if fileprocessing.noUsers():
        return redirect("/newuser", code=302)
    else:
        #check if signed in
        cookie = request.cookies.get('authcookie')
        auth = checkAuth(cookie)
        if not auth == False:
            #we are signed in
            return render_template('dash.html', data=fileprocessing.displayAllUsers(str(auth)), username=str(auth), showAdminCheck=fileprocessing.checkAdmin(auth))
        else:
            #login please
            return redirect("/login", code=302)


@app.route('/login', methods=['GET', 'POST'])
def login():
    #if we are logged in go to root
    if checkAuth(request.cookies.get('authcookie')) == False:
        #new user redirect on first run
        if not fileprocessing.noUsers():
            if request.method == 'POST':
                if(fileprocessing.login(request.form['username'], request.form['password']) == 0):
                    print("authentication successful for "+request.form['username'])
                    authkey = str(secrets.randbits(512))
                    authorized_cookies.append((request.form['username'], authkey, time.time()))
                    resp = redirect("/", code=302)
                    resp.set_cookie('authcookie', authkey)
                    print("set cookie for "+request.form['username'])
                    return resp
                else:
                    errorReturned = 'Invalid Credentials. Please try again.'
                return render_template('login.html', errorReturned=errorReturned)
            else:
                #this is a GET
                return render_template('login.html')
        else:
            return redirect("/newuser", code=302)
    else:
        print("logged in")
        return redirect("/", code=302)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    #find cookie and then delete it
    print("logging out")
    cookie = request.cookies.get('authcookie')
    if cookie:
        for i,c in enumerate(authorized_cookies):
            if c[1] == cookie:
                del(authorized_cookies[i])
                print("logged out")
    resp = redirect("/login", code=302)
    resp.set_cookie('authcookie', "", expires=0)
    return resp


@app.route('/newuser', methods=['GET', 'POST'])
def newuser():
    #only allow user creation if no users exist or logged in
    cookie = request.cookies.get('authcookie')
    auth = checkAuth(cookie)
    #no users is true on first run
    noUsers = fileprocessing.noUsers()
    #check if allowed
    if not auth == False or noUsers:
        #check for admin
        isAdmin = fileprocessing.checkAdmin(auth)
        #should we show the admin options
        showAdminCheck = (not noUsers) and (isAdmin)
        if request.method == 'POST':
            #delete checkmark
            if "deletecheck" in request.form:
                #only allow admins
                if isAdmin:
                    #don't delete ourselves'
                    if request.form['username2'] != auth:
                        result = fileprocessing.deleteUser(request.form['username2'])
                    else:
                        result = "You can not delete yourself"
                else:
                    result = "You do not have permition to delete users"
            else:
                if showAdminCheck:
                    if "admincheck" in request.form:
                        result = fileprocessing.newUser(request.form['username2'], request.form['password2'], request.form['passwordCheck'], True, auth)
                    else:
                        result = fileprocessing.newUser(request.form['username2'], request.form['password2'], request.form['passwordCheck'], False, auth)
                else:
                    result = fileprocessing.newUser(request.form['username2'], request.form['password2'], request.form['passwordCheck'], None, auth)
            return render_template('newUser.html', error=result ,showAdminCheck=showAdminCheck)

        elif request.method == "GET":
            return render_template('newUser.html', showAdminCheck=showAdminCheck)
    else:
        return redirect("/login", code=302)

#save
@app.route('/save', methods=['POST'])
def handle_post():
    if request.method == 'POST':
        cookie = request.cookies.get('authcookie')
        auth = checkAuth(cookie)
        if not auth == False:
            body = request.json
            print(body)
            return "saved"


if __name__ == '__main__':
    app.run()
