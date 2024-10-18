# ISA-mock-server

run the server with `sudo python3 mock_server.py test_case_num`

connect to the server `./imapcl 127.0.0.2 -a login.txt -o msgs`

## Test cases
1. Send 3 emails, client should behave normally
2. Send 3 emails but the UIDValidity of the mailbox changed, client should download all emails again
3. Spam the client with unsolicited messages, client should behave normally
4. Don't respond to client for 15 seconds, client should time-out
