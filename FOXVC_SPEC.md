# FoxVC Language & Runtime Specification (Version 0.4.0)

FoxVC is a deterministic programming language featuring two unified native models:
1. **Relational Entity Space (RES):** 2D visual worlds governed by topological anchors, composition, and semantic relations instead of coordinate-based drawing commands.
2. **In-Memory Web Architecture:** Structural document models (FWEB), cascading visual rules (FSKIN), and reactive logic (FLOGIC) served in-memory over HTTP.

## 2D Relational Entity Space

### Directives:
* `space <Identifier>`: Defines an unbounded metric visual reference plane.
* `entity <Identifier>`: Declares a semantic visual unit with an intrinsic `form` (`circle`, `rect`, `polygon`, `arc`).
* `anchor <name> at <cardinal> [offset <x>, <y>]`: Declares custom points of interface relative to standard cardinal landmarks.
* `inside <Target> [at <Anchor>]`: Containment relation.
* `anchored_to <Target.Anchor> [at <Anchor>]`: Topological contact point alignment.
* `beside <Target> [direction <cardinal>] [spacing <N>]`: Cardinal proximity relation.
* `around <Target> distance <D> [bearing <Angle>]`: Polar orbital relationship.
* `connect <Name> from <A.anchor> to <B.anchor>`: Geometric connection spanning between two anchors.
* `replicate <N> of entity <Name> distributed [linear | radial | field]`: Generative spatial replication.

## Outbound HTTP & Networking (Standard Shelf)

FoxVC provides native network communication primitives for interacting with REST APIs, Webhooks, and external services:

* `httpGet(url, [headers, timeout])`: Performs an HTTP/HTTPS GET request. Returns a `pack` with `status`, `ok`, `body`, `headers`, and `json`.
* `httpPost(url, [body, headers, timeout])`: Performs an HTTP/HTTPS POST request. Automatically encodes JSON payloads if a pack is provided.
* `httpPut(url, [body, headers, timeout])`: Performs an HTTP/HTTPS PUT request.
* `httpDelete(url, [headers, timeout])`: Performs an HTTP/HTTPS DELETE request.
* `fetch(url, [options])`: General fetch interface accepting options pack (`method`, `body`, `headers`, `timeout`).
* `urlEncode(params)`: Encodes a pack/dictionary of parameters into a URL query string.
* `urlDecode(string)`: Decodes a URL-encoded string.

## Embedded Database Engine (SQLite)

FoxVC provides native persistent data storage powered by SQLite:

* `dbOpen(path)`: Opens a SQLite database connection (or `":memory:"`). Returns a `pack` with `handle`, `path`, and `ok`.
* `dbExecute(db, sql, [params])`: Executes a data definition or modification query (`CREATE`, `INSERT`, `UPDATE`, `DELETE`). Returns a `pack` with `ok`, `rows_affected`, and `last_id`.
* `dbQuery(db, sql, [params])`: Executes a `SELECT` query and returns a `list` of `pack` row objects with named column properties.
* `dbClose(db)`: Closes the active database connection.

## Production HTTP Web Server & REST API Framework

FoxVC supports running web services and microservices directly from FoxVC code:

* `httpServer(port, [host])`: Creates a new HTTP server instance bound to `host:port` (use `0` for ephemeral port).
* `httpRoute(server, method, path, handler)`: Registers a request handler for a specific HTTP method (`GET`, `POST`, `PUT`, `DELETE`, `*`) and route path.
* `httpResponse(body_or_json, [status, headers])`: Helper creating a structured response pack with status code and headers.
* `httpStart(server)`: Spawns the web server in a background thread.
* `httpStop(server)`: Gracefully stops the web server.

## Security, Cryptography & Auth

* `hashSha256(data)`: Computes the SHA-256 hex digest.
* `hashSha512(data)`: Computes the SHA-512 hex digest.
* `hashMd5(data)`: Computes the MD5 hex digest.
* `hmacSha256(key, message)`: Computes HMAC-SHA256 signature for API signing and webhooks.
* `uuid()` / `uuid4()`: Generates a cryptographically random RFC 4122 v4 UUID string.
* `secureToken([bytes])`: Generates a cryptographically secure hex token for sessions or API keys.
* `base64Encode(data)`: Encodes string to Base64.
* `base64Decode(data)`: Decodes Base64 to string.
* `hexEncode(data)` & `hexDecode(hex)`: Hexadecimal encoders.

## System, Environment & Process Execution

* `getEnv(key, [default])`: Reads environment variables.
* `setEnv(key, value)`: Sets environment variables.
* `listEnv()`: Returns all environment variables as a `pack`.
* `execCmd(command, [timeout])`: Executes a shell command and returns `pack { ok, exit_code, stdout, stderr }`.
* `platform()`: Returns host OS platform (e.g. `"linux"`, `"darwin"`, `"win32"`).
* `cpuCount()`: Returns number of available logical CPU cores.
* `makeDir(path)` & `removeDir(path)`: Recursive directory creation and removal.
* `absPath(path)`: Resolves absolute path.
* `fileSize(path)`: Returns file size in bytes.

## Concurrency & Background Tasks

* `spawn(fn, ...args)`: Dispatches a function or act to execute asynchronously in the background thread pool.
* `awaitTask(task_handle, [timeout])`: Awaits task completion and returns the result value.



