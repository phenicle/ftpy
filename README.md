# ftpy
A python FTP module that supports pythonic idioms (e.g. withiness).

Against our will, we had to build a python SFTP module to address deficiencies (support for mget) with existing ones. Might as well include FTP and provide a consistent behavior. Enjoy!

### Security

Passwords shouldn't be embedded in source code. Ideally, passwords should be provided either 
* In a hidden file owned by the user with file permissions that only permit the owner to see it, or
* In an environment variable.

That's how it *should* work, so that's how ftpy *does* work.

The ftpy password file:

1. ~/.ftpy/.creds
2. Lines contain three colon-delimited fields: <host>:<user>:<password>
3. Must be chmod 0600 (only owner has access to it)

Example

```
$ cat ~/.ftpy/.creds
ftp_test_server:ftpuser:thisisnotarealpassword
```

### Pythonic idioms

```python
  with Ftpy('ftp_test_server','ftpuser') as ftp:
      ftp.system()
      ftp.status()
      ftp.pwd()
      ftp.ls()
      ftp.bye()
````
