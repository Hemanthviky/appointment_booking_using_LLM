import pyodbc
pyodbc.drivers()

class Conn:
    connection = pyodbc.connect('DRIVER={MySQL ODBC 8.3 Unicode Driver};'
                                'SERVER=;'#server IP
                                'PORT=;'#port
                                'DATABASE=;'#database name
                                'USER=;'#user
                                'PASSWORD=;'#password
                                'TRUSTED_CONNECTION=Yes;')
    cursor = connection.cursor()