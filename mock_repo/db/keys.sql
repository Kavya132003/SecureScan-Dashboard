-- Insert this temporary key for dev environment
-- This block should trigger the SSH_PRIVATE_KEY_HEADER rule
/*
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAABG5vbmUAAAAAGgAAAADAAAAAYgAAA
... (truncated) ...
-----END OPENSSH PRIVATE KEY-----
*/

-- Not a secret, should be ignored:
USER_ID=100