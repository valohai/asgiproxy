asgiproxy
=========

Tools for building HTTP and Websocket proxies for the asynchronous ASGI protocol. 

## Usage

### Command line usage

`asgiproxy` includes a small command-line tool that transparently (aside from rewriting the "Host" header)
proxies all HTTP and WebSocket requests to another endpoint.

It may be useful on its own, and also serves as a reference on how to use the library.

While the library itself does not require Uvicorn, the CLI tool does.

```bash
$ python -m asgiproxy http://example.com/
```

starts a HTTP server on http://0.0.0.0:40404/ which should show you the example.com content.

### API usage

Documentation forthcoming. For the time being, see `asgiproxy/__main__.py`.

### Running tests

Tests are run with Py.test.

```bash
py.test 
```
