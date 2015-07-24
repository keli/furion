from .socks5 import AUTH_SUCCESSFUL, AUTH_ERR_USERNOTFOUND


class SimpleAuth:
    def __init__(self, path):
        self.users = {}
        for line in open(path):
            line = line.strip()
            if line:
                user, password = line.split(' ')
                self.users[user] = password
        
    def auth(self, username, password):
        if self.users.get(username, '') == password:
            return 0, AUTH_SUCCESSFUL
        else:
            return 0, AUTH_ERR_USERNOTFOUND

    def usage(self, member_id, bytes):
        pass
