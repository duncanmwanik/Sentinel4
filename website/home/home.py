from flask import Flask, render_template, url_for, redirect, request, Response, Blueprint, session
# from flask_mail import Message
# from main import *

home = Blueprint('home',__name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='home.static')

@home.route('/')
@home.route('/home')
def home_page():

    session.permanent = True
    return render_template('home.html', scroll='')


@home.route('/goto_console')
def goto_console():
    if 'usd' in session:
        return redirect(url_for('console.console_page', user_id=session['usd']))
    else:
        return redirect(url_for('auth.logup', page='console'))


@home.route('/goto_tendy')
def goto_tendy():
    if 'usd' in session:
        return redirect(url_for('tendy.tendy_page', user_id=session['usd']))
    else:
        return redirect(url_for('auth.logup', page='tendy'))


@home.route('/goto_counter')
def goto_counter():
    if 'usd' in session:
        return redirect(url_for('counter.counter_page', user_id=session['usd']))
    else:
        return redirect(url_for('auth.logup', page='counter'))

# @home.route('/send_email',methods=['POST', 'GET']) # --- Route to Update a Channel
# def send_email():
#     if request.method == 'POST':
#         name = request.form['name']
#         email = request.form['email']
#         message = request.form['message']

#         if name!='' and email!='' and message!='':
#             try:
#                 msg = Message("Hello",
#                   sender="from@example.com",
#                   recipients=["to@example.com"])
#                 mail.send(msg)
#                 return redirect(url_for('home.home_page'))

#             except Exception as e:
#                 return ('', 204)
