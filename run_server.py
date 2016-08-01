from src import app
import logging

app.secret_key = '<]FGhTHfrbvJM,5T'
app.config['SESSION_TYPE'] = 'filesystem'

log = logging.getLogger('sotw')
log.setLevel(logging.DEBUG)
fh = logging.FileHandler('spam.log')
fh.setLevel(logging.DEBUG)
log.addHandler(fh)
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
fh.setFormatter(formatter)
log.info("Run server started")

app.run(debug=True, host='0.0.0.0', threaded=True)
