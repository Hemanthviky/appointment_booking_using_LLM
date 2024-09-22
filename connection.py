import pyodbc
pyodbc.drivers()

class Conn:
    connection = pyodbc.connect('DRIVER={MySQL ODBC 8.3 Unicode Driver};'
                                'SERVER=127.0.0.1;'
                                'PORT=3306;'
                                'DATABASE=Booking_system;'
                                'USER=root;'
                                'PASSWORD=;'
                                'TRUSTED_CONNECTION=Yes;')
    cursor = connection.cursor()
