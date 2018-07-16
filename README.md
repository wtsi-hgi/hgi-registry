# Human Genetics Programme Group Registry

[![Build Status](https://travis-ci.org/wtsi-hgi/hgi-registry.svg?branch=master)](https://travis-ci.org/wtsi-hgi/hgi-registry)
[![Test Coverage](https://codecov.io/gh/wtsi-hgi/hgi-registry/branch/master/graph/badge.svg)](https://codecov.io/gh/wtsi-hgi/hgi-registry)

A simple web interface that provides an overview of project and team
groups within the Human Genetics Programme.

# Installation

Just pull and run the Docker container:

    docker run -dp 80:5000 \
               -e LDAP_URI=ldap://my.ldap.host:389 \
               mercury/hgi-registry

Inside the container, the service runs under `0.0.0.0:5000`, by
default, which you may map to the host however you wish. The service
otherwise takes its cues from the following environment variables:

* `LDAP_URI` The URI of your LDAP server, consisting of the schema,
  hostname and port. This must be supplied.

* `EXPIRY` The duration (in seconds) before in-memory LDAP entities are
  refreshed from the LDAP server. This value is optional and defaults to
  3600 (i.e., one hour).

* `API_URI` The URI that the service will run under, consisting of the
  schema (which must be `http://`), hostname and port. This value is
  optional and defaults to `http://0.0.0.0:5000`.

# RESTful API

The data returned from the API is rendered from an internal cache, which
is first populated when a requested entry does not exist. Therefore, the
data returned may be stale and not reflect the true state at any given
time. However, cache entries will be refreshed periodically to minimise
this effect.

## Hypermedia

JSON values that represent links within the graph will be a JSON object
with:

* An `href` entity, containing the URI of the linked resource;
* A `rel` or `rev` (or both) entity, describing the link and reverse
  link relation, respectively;
* An optional `value` entity, that contains further semantic information
  about the link target, without the need for dereferencing.

### Relations

The following relations are used:

Relation | Semantics
:------- | :------------------------------------------------------------
`self`   | Itself
`items`  | Subordinate entries
`group`  | Human Genetics Programme group
`person` | Person, human or otherwise
`member` | Member of a group
`owner`  | Owner of a group
`pi`     | Principal investigator of a group
`photo`  | Photo of a person

## Endpoints

### `/groups`

Method | Content Type       | Behaviour
:----- | :----------------- | :-----------------------------------------
`GET`  | `application/json` | Return the identities of every project and team group in the Human Genetics Programme.

#### Schema

Array of group [hypermedia entities](#hypermedia), with their POSIX
names dereferenced.

### `/groups/<GROUP>`

Method | Content Type       | Behaviour
:----- | :----------------- | :-----------------------------------------
`GET`  | `application/json` | Return the details of the specific group given by `<GROUP>`.

#### Schema

* `id` [Hypermedia entity](#hypermedia) of itself, with its POSIX group
  ID dereferenced;
* `active` Predicate of whether this is an active group;
* `description` Group description, `null` for unknown;
* `prelims` Array of prelim IDs;
* `pi` [Hypermedia entity](#hypermedia) for the group's PI, with their
  full name dereferenced;
* `owners` Array of [hypermedia entities](#hypermedia) of the group's
  owners, with their full names dereferenced;
* `members` Array of [hypermedia entities](#hypermedia) of the group's
  members, with their full names dereferenced;
* `last_updated` The timestamp of the last update for this record (in
  ISO8601 format).

### `/people`

Method | Content Type       | Behaviour
:----- | :----------------- | :-----------------------------------------
`GET`  | `application/json` | Return the identities of every user account.

#### Schema

Array of person [hypermedia entities](#hypermedia), with their full names
dereferenced.

### `/people/<USER_ID>`

Method | Content Type       | Behaviour
:----- | :----------------- | :-----------------------------------------
`GET`  | `application/json` | Return the details of the specific user given by `<USER_ID>`.

#### Schema

* `id` [Hypermedia entity](#hypermedia) of themself, with their POSIX
  user ID dereferenced;
* `name` Person's full name;
* `mail` Person's e-mail address;
* `title` Person's job title, `null` for unknown;
* `human` Predicate of whether this is a real (i.e., human) person;
* `active` Predicate of whether this is an active account;
* `photo` [Hypermedia entity](#hypermedia) of person's photo, if they
  have one;
* `involvement` Array of group [hypermedia entities](#hypermedia) for the
  groups in which the person is involved and their capacity therein,
  with said groups' POSIX group IDs dereferenced;
* `last_updated` The timestamp of the last update for this record (in
  ISO8601 format).

### `/people/<USER_ID>/photo`

Method | Content Type       | Behaviour
:----- | :----------------- | :-----------------------------------------
`GET`  | `image/jpeg`       | Return the photo of the specific user given by `<USER_ID>` if it exists. If said user has no photo, then a 404 Not Found error will be returned.

## Errors

HTTP client and server errors are returned as a JSON object with the
following entities:

* `status` HTTP status code;
* `reason` HTTP status reason;
* `description` Description of the error

# Frontend

Currently, a *very* rudimentary frontend exists, that expects the API
server to be available at `http://localhost:5000`. It cannot be
emphasised enough just how basic this frontend is!
