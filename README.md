## The Cube RPC protocal

### Message Type

There are four kinds of message:

*   Requset   (From client to server)
*   Answer  (From server to client)
*   Welcome (From server to client)
*   Close   (client to server, or server to client)

All the messages contain a header, but only `Requset` and `Answer` contain a body.

When the server receive a new connection, it must send the `Welcome` message to the client.

Only after the `Welcome` message has been recieved, the client can sent the `Request`.

##### disconnect gracefully

If the Server or the Client want to close the connection gracefully. It must send the `Close` message.

The other side will close the socket connection after recieve the `Close` message.

The sponser close the connection after detect the socket has been disconnected.

#### Header

The header is 4 or 8 bytes long.

    byte    "C"
    byte    "B"
    byte    version
    byte    message_type

    int32   body_size;               // little endian byte order, not network byte order

The header of Welcome and Close is 4 bytes long. does not have body_size.

##### Message Type

    MESSAGE_TYPE_WELCOME        = 0x01
    MESSAGE_TYPE_CLOSE          = 0x02
    MESSAGE_TYPE_QUEST          = 0x03
    MESSAGE_TYPE_ANSWER         = 0x04

### Body

#### Requset Body

    integer rid;
    string  service;
    string  method;
    dict    params;

#### Answer Body

    integer rid;
    integer status;
    dict    data;

If the answer is a normal response, status is 0, else status is none-zero and data must contain the following data:

|Key|Value type|description|
|---|---|---|
|exception    | string           | exception name|
|code         | int           | |
|message      | string           | |
|raiser       | string           | method*service @proto:host:port|
|detail       | dict      | |
