from passlib.hash import sha512_crypt

class PasswordHash:
	def hash_password(self, pw):
		return sha512_crypt.encrypt(pw)
		
	def check_password(self, pw, stored_hash):
		return sha512_crypt.verify(pw, stored_hash)
