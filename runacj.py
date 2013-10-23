from acj import app
import os

ip = os.getenv('IP', '0.0.0.0')
port = os.getenv('PORT', 8080)
#app.run(debug=True)
app.run(ip, int(port), debug=True)
#app.run(ip, int(port))
