from website import config
# from flask_mail import Mail

app = config.create_app()
# mail = Mail(app)

if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host='192.168.43.233', debug=False)
