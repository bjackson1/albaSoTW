from src import app

app.secret_key = '<]FGhTHfrbvJM,5T'
app.config['SESSION_TYPE'] = 'filesystem'

app.run(debug=True, host='0.0.0.0', threaded=True)
