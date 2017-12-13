# ftpy.py

# license placeholder here

"""
 What: The ftpy python module
  Why: Because we were forced to create sftpy.
       And ftplib's API isn't consistent with sftpy.
       This is an opportunity to use a single, consistent
       API across both ftp and sftp under python.

 Open Questions: 

   Is there a way to tell which API elements are
   supported by the external FTP client pexpect is using?

 Future:

   Transition from dependence on pexpect to using
   native C FTP library calls.

"""
import sys
import os
import pexpect
import re
import pprint
from distutils.spawn import find_executable
import errno

DEBUGGING = True

# session debugging constants
# determines what, if anything
SESSDBGN = 0   # show nothing
SESSDBGR = 1   # show reads
SESSDBGW = 2   # show writes
SESSDBGRW = 3  # show reads and writes

# file transfer modes
MODE_BINARY = 1  # binary is default
MODE_TEXT = 2

# path type indicator constants
PATH_TYPE_UNKNOWN  = 0
PATH_TYPE_FILEPART = 1
PATH_TYPE_DIRPART  = 2
PATH_TYPE_COMPOUND = 3

STATE_UNKNOWN = 0
STATE_START = 1
STATE_LOGGED_IN = 2

pp = pprint.PrettyPrinter(indent=4)

class Ftpy(object):
	""" 
	The Ftpy class

    Arguments: <host-identifier> <user-account-identifier>

     where 

      o <host-identifier> is an IPv4 or IPv6 address, hostname, or FQDN.
      o <user-account-identifer> is a user name

      For the sake of security, passwords should not appear in source code.

      Ftpy looks for password two places:

      1. environment variable named 'ftpypass_<host-identifier>'
      2. credentials file

      The credentials file should be located at ~/.ftpy/.creds
      Permissions on the credentials file must be set to 600.
      The format of the credentials file is:

      <host-identifier>:<user-identifier>:<password>

	"""
	def __init__(self, host, user):

		if DEBUGGING:
			print "host: %s" % (host)
			print "user: %s" % (user)

		"""
		Default values are documented here 
		goal: support all of the knobs exposed by pexpect 
		"""
		self.session_handle = None
		self.timeout = 15
		self.maxreadbuf = 4096
		self.password = None
		# valid values: None, SESSDBGR, SESSDBGW, SESSDBGRW
		self.debug_session = SESSDBGRW
		self.username_prompt = 'ame:*'
		self.password_prompt = 'assword:*'
		self.prompt = 'ftp> '
		self.mode = MODE_BINARY
		self.state = STATE_START

		self.host = host
		self.user = user
		if not self.locate_ftp_client_program():
			raise ValueError('failed to locate FTP client program')
			sys.exit(1)
		if not self.get_credentials():
			raise ValueError(
				"failed to find password;\n No env var '%s', no creds file at %s" \
				   % (self.credvarname, self.creds_filespec)
				)
		else:
			self.login()
	
	def __enter__(self):

		return self

	def __exit__(self, type, value, traceback):

		pass

	def __repr__(self):

		s = '\n'
		for k in self.__dict__:
			s += "%5s%20s: %s\n" % (' ',k, self.__dict__[k])

		return s

	def locate_ftp_client_program(self):
		""" 
		Track down the ftp client program 
		Raise exception if not found.
		"""
		self.program = find_executable('ftp')
		if not self.program:
			raise FileNotFoundError(
    			errno.ENOENT, 
    			os.strerror(errno.ENOENT), 
    			'ftp'
    			)
			return False
		return True

	def get_password_from_environment(self):
		""" 		
		  environment variable name:
		   'ftpypass_<host-identifier>'
		"""
		self.credvarname = 'ftpypass_%s' % (self.host)
		if self.credvarname in os.environ:
			self.password = os.environ[self.credvarname]
			if DEBUGGING:
				print "found password in environment"
			return True
		return False

	def get_password_from_creds_file(self):
		""" The credentials file should be located at ~/.ftpy/.creds """

 		hdir = os.path.expanduser("~")
		self.creds_filespec = '%s/.ftpy/.creds' % (hdir)
		try:
			with open(self.creds_filespec) as creds:
				""" 
				format of creds file is <host-identifier>:<user-identifier>:<password> 
				TODO: should strip spaces and use more robus searching/matching
				"""
				for line in creds.readlines():
					fields = ':'.split(line)
					if fields[0] == self.host and fields[1] == self.user:
						self.password = fields[3]
						if DEBUGGING:
							print "found password in creds file %s" \
							  % self.creds_filespec
						return True

		except IOError as e:
			print "Unable to locate a password for %s on %s (creds file not found)" \
			  % (self.user,self.host)

		return False

	def get_credentials(self):
		""" 
		A utility file for tracking down the password to use.
		Check for environment variable first.
		If found, use that.
		Otherwise, fall back on credentials file.
		If credentials file not found, raise exception.
		"""

		if self.get_password_from_environment():
			return True

		if self.get_password_from_creds_file():
			return True

		return False

	def login(self):

		# TODO: populate this call with all of the knobs
		program_args = [ self.host ]
		self.session_handle = pexpect.spawn( 
			self.program, 
			args=program_args, 
			maxread=self.maxreadbuf, 
			timeout=self.timeout 
			)

		if self.debug_session == SESSDBGRW:
			self.session_handle.logfile = sys.stdout

		# how do we catch and report authentication failures?
		# as it currently is, this is DREADFUL
		self.session_handle.expect(self.username_prompt)
		self.session_handle.sendline(self.user)
		self.session_handle.expect(self.password_prompt)
		self.session_handle.sendline(self.password)
		self.session_handle.expect(self.prompt)
		self.state = STATE_LOGGED_IN

		return

	def bye(self):

		self.session_handle.sendline('bye')
		self.session_handle.expect(pexpect.EOF)		

	def lcd(self, localpath):
		""" how can we verify the success of this? """

		# should validate that 
		self.session_handle.sendline('lcd %s' % localpath)
		self.session_handle.expect(self.prompt)

	def pwd(self):

		self.session_handle.sendline('pwd')
		self.session_handle.expect(self.prompt)

	def ls(self):

		self.session_handle.sendline('ls')
		self.session_handle.expect(self.prompt)

	def passive(self):
		""" WARNING! this command TOGGLES between active/passive! """

		self.session_handle.sendline('passive')
		self.session_handle.expect(self.prompt)	

	def rename(self, oldname, newname):

		self.session_handle.sendline('rename %s %s' % (oldname, newname))
		self.session_handle.expect(self.prompt)	

	def status(self):

		self.session_handle.sendline('status')
		self.session_handle.expect(self.prompt)

	def system(self):

		self.session_handle.sendline('system')
		self.session_handle.expect(self.prompt)

	def get(self, source_path):
		""" 
		we ought to do some validation of source_path 
		to prevent people from shooting themselves in the feet.
		"""
		self.session_handle.sendline('get %s' % (source_path))
		self.session_handle.expect(self.prompt)

	def mget(self, source_path):
		""" 
		raise warning if source_path doesn't look like 
		a filename pattern that contains asterisks
		"""
		self.session_handle.sendline('mget %s' % (source_path))
		self.session_handle.expect(self.prompt)

	def analyze_path(self, pathstr):
		""" 
		returns a dictionary containing
		 path_type - an integer constant
		 pathstr   - the original value
		 dirpart   - a (possibly empty) string
		 filepart  - a string devoid of slashes

		 if pathstr contains no slashes, it's assumed
		 that it is a filename pattern (i.e. filepart)
		"""

		result = {}
		result['pathstr'] = pathstr
		(result['dirpart'], result['filepart']) = os.path.split(pathstr)
		if dirpath:
			result['path_type'] = PATH_TYPE_COMPOUND
		else:
			"""
			empty dirpath means no slashes in pathstr,
			therefore pathstr is a filename pattern
			"""
			result['path_type'] = PATH_TYPE_FILEPART

		if DEBUGGING:
			pp.pprint(result)

		return result

	def beam_me_down(self, source_path):
		""" 
		'beam_me_down' fetches files with automatic get/mget detection 
		if the filepart of the path contains one or more wildcards ('*'),
		use mget. otherwise, use get.
		"""

		path_dict = self.analyze_path(source_path)

		# if dirpart is not empty, cd using dirpart first
		if path_dict['dirpart']:
			self.chdir(path_dict['dirpart'])

		filepart = path_dict['filepart']
		# I'd prefer to use substr here, re seems like overkill
		result = re.search(r'\*', filepart)
		if result is not None:
			self.mget(filepart)
		else:
			self.get(filepart)

	def set_xfer_mode(self, mode):

		modestr = None
		if mode == MODE_TEXT:
			modestr = 'text'
		elif mode == MODE_BINARY:
			modestr = 'binary'
		else:
			# check first to make sure 'mode' arg is even an integer!
			# raise value exception
			raise ValueError("Invalid mode constant: %d" % mode)

		self.session_handle.sendline('%s' % (modestr))
		self.session_handle.expect(self.prompt)

if __name__ == '__main__':

	with Ftpy('ftp_sftp_test_server','ftptest') as ftp:
		ftp.system()
		ftp.status()
		ftp.pwd()
		ftp.ls()
		ftp.bye()
