from acj import app
import os

port = os.getenv('PORT', 8080)
#app.run(debug=True)
app.run('0.0.0.0',port,debug=True)
#app.run('0.0.0.0',8080)