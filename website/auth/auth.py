from flask import Flask, render_template, url_for, redirect, request, Response, Blueprint, flash, session, escape
import pyrebase
from getpass import getpass


auth = Blueprint('auth', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='auth.static')

# ---------------- Firebase Initializations --------------------------------
firebaseconfig = {
    "apiKey": "AIzaSyCVEt5pXbBBWayikudil_YZDMX5GoA5Wos",
    "authDomain": "sentinel-b625c.firebaseapp.com",
    "databaseURL": "https://sentinel-b625c-default-rtdb.firebaseio.com",
    "projectId": "sentinel-b625c",
    "storageBucket": "sentinel-b625c.appspot.com",
    "messagingSenderId": "115615795651",
    "appId": "1:115615795651:web:107d63b8eefec5d4859576",
    "measurementId": "G-C4LP5G2GNS",
    "serviceAccount": "firebase/sentinel.json"
   } #------ Firebase Credentials Dictionary

firebase = pyrebase.initialize_app(firebaseconfig)
authorize = firebase.auth()
ref = firebase.database()
# -------------------------------------------------------------------------

@auth.route('/logup/<page>') # --- Main Route
def logup(page):
    return render_template('logup.html', page=page)

@auth.route('/payment') # --- Route to Add Payment Option
def payment():
    return render_template('payment.html')

@auth.route('/signup',methods=['POST', 'GET']) # --- Route to Sign Up New User
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        password2 = request.form['password2']
        page = request.form['page-input-signup']

        user_id = email.translate ({ord(c): "_" for c in "!@#$%^&*()[]{};:,./<>?\|`~-=_+"})
        path = user_id + '/details/'
        data = {'username': username, 'email': email, 'phone': phone, 'user_id': user_id}

        if password==password2:
            try:
                user = authorize.create_user_with_email_and_password(email, password) # Sign up user using firebase auth
                print('Success! Signed Up '+ email + ';' + password)
                ref.child(path).update(data) # Add user details to RTDB
                print('Success Adding New User To Database!')
                session.permanent = True
                session['usd'] = user_id # Add user id to cookies
                session['username'] = username # Add user id to cookies

                # Go to specific page
                if page == 'console':
                    return redirect(url_for('console.console_page', user_id=user_id))
                if page == 'tendy':
                    return redirect(url_for('tendy.tendy_page', user_id=user_id))
                if page == 'counter':
                    return redirect(url_for('counter.counter_page', user_id=user_id))
                if page == 'services':
                    return redirect(url_for('home.home_page'))
                    
            except Exception as e:
                print('Signed Up with ERROR!\n' + str(e))
                return ('', 204)


@auth.route('/login',methods=['POST', 'GET']) # --- Route to Log In Existing User
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        page = request.form['page-input-login']
        print(email + ':' + password)
        user_id = email.translate ({ord(c): "_" for c in "!@#$%^&*()[]{};:,./<>?\|`~-=_+"})

        try:
            user = authorize.sign_in_with_email_and_password(email, password) # Log in user using firebase auth
            print('Success! Logged In '+ email + ';' + password)
            username_path = "/" + user_id +"/details/"
            username = ref.child(username_path).child('username').get().val() # --- Get the Username
            session.permanent = True
            session['usd'] = user_id # Add user id to cookies
            session['username'] = username # Add user id to cookies

            if page == 'console':
                return redirect(url_for('console.console_page', user_id=user_id))
            if page == 'tendy':
                return redirect(url_for('tendy.tendy_page', user_id=user_id))
            if page == 'counter':
                return redirect(url_for('counter.counter_page', user_id=user_id))
            if page == 'services':
                return redirect(url_for('home.home_page', user_id=user_id))
        except Exception as e:
            print('Error Loging In!\n' + str(e))
            return ('', 204)


@auth.route('/logout')
def logout():
    return 'Logout'

