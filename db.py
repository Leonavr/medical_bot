import sqlite3

class SQLighter:
    def __init__(self, database_file, force: bool = False):
        self.connection = sqlite3.connect(database_file, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.connection.commit()
        if force:
            self.cursor.execute ('DROP TABLE IF EXISTS user_message')
        self.cursor.execute ("CREATE TABLE IF NOT EXISTS user_message (id INTEGER PRIMARY KEY, role TEXT not NULL, user_id INTEGER NULL, login TEXT NULL, password TEXT NULL)")
    
    def add_role (self, user_id, role:str):
        self.cursor.execute('INSERT INTO user_message (user_id, role) VALUES (?, ?)', (user_id, role))
        self.connection.commit()
    
    def add_login (self, login: str):
        self.cursor.execute("UPDATE user_message SET login = ? WHERE login is NULL",(login, ))
        self.connection.commit()
    
    def add_password (self, password: str):
        self.cursor.execute("UPDATE user_message SET password = ? WHERE password is NULL",(password, ))
        self.connection.commit()
    
    def user_exist (self, user_id: int):
        with self.connection:
            result = self.cursor.execute("SELECT * FROM user_message WHERE user_id = ?", (user_id, )).fetchall()
        return bool(len(result))
    
    def user_provider (self, user_id: int):
         with self.connection:
            result = self.cursor.execute("SELECT role FROM user_message WHERE user_id = ?", (user_id, )).fetchall()
            provider = result[0][0]
            return provider
    def pass_check(self, user_id:int):
        result = self.cursor.execute("SELECT password FROM user_message WHERE user_id = ?", (user_id, )).fetchall()
        password = result[0][0]
        return password
    def user_id(self, role:str):
        a = self.cursor.execute("SELECT user_id FROM user_message WHERE role = ?", (role, )).fetchall()
        res = a[0][0]
        return res
    def set_msg(self,message,user_id):
        self.cursor.execute("UPDATE user_message SET msg = ? WHERE user_id = ?",(message,user_id ))
        self.connection.commit()
    def msg_to_prov(self):
        msg = self.cursor.execute("SELECT msg FROM user_message WHERE role = 'Пацієнт'").fetchall()
        self.connection.commit()
        return msg[0][0]
    def close(self):
        self.connection.close()

