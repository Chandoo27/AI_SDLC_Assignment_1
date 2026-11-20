# Feature Specification: Smart Todo API

**Feature Branch**: `not created (no branch hook configured)`

**Created**: 2026-11-14

**Status**: Draft

**Input**: User description: "Build a Smart Todo API application supporting task creation, updates, deletion, viewing, completion, tag filtering, priority sorting, and local JSON persistence."

## Clarifications

### Session 2026-11-14

- Q: When a user filters tasks by multiple tags, should the results include tasks matching any requested tag or only tasks matching all requested tags? → A: Include a task if it matches any requested tag.
- Q: When tasks are sorted by priority, should High-priority tasks appear before Low-priority tasks, or should Low-priority tasks appear first? → A: Sort High, then Medium, then Low.
- Q: Should a task that has been marked Completed be allowed to return to Pending? → A: Allow users to reopen a Completed task as Pending.
- Q: If two update requests for the same task arrive at the same time, should both be applied in sequence or should the later conflicting update be rejected? → A: Apply updates sequentially; the later value wins for fields both change.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Manage Tasks (Priority: P1)

A user can create a task, view all tasks or one task by ID, update task details, and delete a
task. A task records its title, description, priority, tags, status, and creation date.

**Why this priority**: Task lifecycle operations are the minimum useful todo experience and
provide the base data used by the other stories.

**Independent Test**: Create a task, retrieve it by ID and in the task list, update its details,
then delete it and verify it is no longer retrievable.

**Acceptance Scenarios**:

1. **Given** valid task details, **When** the user creates a task, **Then** the response
   contains a unique ID, the supplied details, Pending status, and a creation date.
2. **Given** an existing task, **When** the user requests it by ID, **Then** its complete
   current representation is returned.
3. **Given** an existing task, **When** the user updates one or more editable fields,
   **Then** those fields change and all omitted or immutable fields remain unchanged.
4. **Given** an existing task, **When** the user deletes it, **Then** deletion succeeds and a
   later lookup returns not found.
5. **Given** an unknown task ID, **When** the user retrieves, updates, completes, or deletes
   it, **Then** the API returns a consistent not-found response.

---

### User Story 2 - Organize and Find Tasks (Priority: P2)

A user can label tasks with tags, filter the task list by tags, and sort the list by priority
to find the tasks that matter most.

**Why this priority**: Filtering and ordering make a growing task list easier to use after
basic task management is available.

**Independent Test**: Create tasks with different tags and priorities, request a tag-filtered
list, and request a priority-sorted list; verify membership and order.

**Acceptance Scenarios**:

1. **Given** tasks with different tags, **When** the user filters by one or more tags,
   **Then** only tasks matching the requested tag criteria are returned.
2. **Given** tasks with different priorities, **When** the user sorts by priority,
   **Then** High tasks precede Medium tasks, which precede Low tasks.
3. **Given** a tag filter and a priority sort in one request, **When** the user lists tasks,
   **Then** the matching tasks are returned in the requested priority order.
4. **Given** no tag filter, **When** the user lists tasks, **Then** all tasks are returned.

---

### User Story 3 - Complete Tasks and Keep Their Data (Priority: P3)

A user can mark a task Completed, reopen it as Pending, and rely on saved tasks and their
status being available after the application restarts.

**Why this priority**: Completion communicates progress, and persistence makes task tracking
useful across application sessions.

**Independent Test**: Mark a task completed, reopen it, restart the application, and verify
that the task and its Pending status are still available.

**Acceptance Scenarios**:

1. **Given** a Pending task, **When** the user marks it completed, **Then** its status becomes
   Completed.
2. **Given** a Completed task, **When** the user marks it completed again, **Then** it remains
   Completed and the operation succeeds.
3. **Given** a Completed task, **When** the user reopens it, **Then** its status becomes
   Pending.
4. **Given** a Pending task, **When** the user reopens it again, **Then** it remains Pending
   and the operation succeeds.
5. **Given** saved tasks, **When** the application restarts, **Then** all saved task fields
   retain their values.
6. **Given** no data file exists on first use, **When** the application starts, **Then** the
   task list is empty and task creation is available.

### Edge Cases

- An empty or whitespace-only title is rejected; a title longer than 200 characters is rejected.
- A description longer than 5,000 characters after trimming is rejected.
- A priority other than High, Medium, or Low is rejected.
- A tag that is empty after trimming, longer than 32 characters, or beyond the 20-tag limit is
  rejected; case-insensitive duplicate tags in one task are stored once, retaining the first
  spelling.
- Reopening a Pending task succeeds without changing its status.
- Concurrent updates to different fields of the same task preserve both changes; when both
  updates change the same field, the last serialized update determines its value.
- Invalid task IDs and unknown task IDs produce the documented client error response.
- A malformed or unreadable local data file produces a consistent server error and MUST NOT
  be silently replaced with an empty task list.
- Equal-priority tasks have deterministic order: earlier creation dates first, then IDs in
  ascending lexical order.
- A tag filter with no matching tasks returns an empty list rather than an error.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST allow a user to create a task with a required title and optional
  description, priority, and tags. If omitted, description and tags default to empty,
  priority defaults to Medium, and status defaults to Pending. Titles MUST contain 1-200
  characters after trimming; descriptions MUST contain 0-5,000 characters after trimming;
  tasks MUST have at most 20 unique tags of 1-32 characters each after trimming. Tag
  uniqueness MUST be case-insensitive, retaining the first spelling.
- **FR-002**: The system MUST assign each created task a unique ID and a creation date in
  UTC ISO 8601 format. Users MUST NOT be able to change an existing task's ID or creation
  date.
- **FR-003**: The system MUST allow a user to retrieve all tasks and retrieve a task by ID.
- **FR-004**: The system MUST allow partial updates to a task's title, description, priority,
  and tags. An update MUST contain at least one editable field. Fields omitted from an update MUST remain unchanged; ID and creation date MUST
  remain immutable. Concurrent updates MUST be applied sequentially to the latest task state;
  changes to different fields MUST both persist, and the last serialized update MUST win for
  any field changed by both requests.
- **FR-005**: The system MUST allow a user to delete a task. A later retrieval of a deleted
  task MUST report that the task does not exist.
- **FR-006**: The system MUST allow a user to mark a task Completed and reopen it as Pending.
  Repeating either action when the task is already in its target status MUST succeed without
  changing its status.
- **FR-007**: The system MUST allow tasks to be filtered by one or more tags. Multi-tag
  filtering MUST return tasks matching any requested tag, using case-insensitive
  exact tag comparison. A request without tags MUST return all tasks.
- **FR-008**: The system MUST sort tasks by priority with High first, then Medium, then Low.
  Equal-priority tasks MUST sort by creation date ascending, then ID ascending. Filtering and
  sorting MUST be usable together.
- **FR-009**: The system MUST persist tasks in a local JSON file and preserve all task fields
  across application restarts. A missing file MUST be treated as an empty task collection.
- **FR-010**: The system MUST validate all request-provided values. Invalid input MUST return
  HTTP 422, a well-formed but unknown task ID MUST return HTTP 404, successful creation MUST
  return HTTP 201, successful retrieval, update, completion, or reopening MUST return HTTP
  200, and successful deletion MUST return HTTP 204.
- **FR-011**: The system MUST return errors using one JSON shape with a stable error code and
  a meaningful message. Error responses MUST NOT expose stack traces, secret values, or
  internal filesystem paths.
- **FR-012**: The system MUST NOT require authentication and MUST NOT provide notifications,
  multi-user support, or cloud database storage in this version.

### Non-Functional Requirements

- **NFR-001**: The system MUST store data in local JSON files; no cloud database or remote
  persistence service may be required.
- **NFR-002**: For a test collection of 1,000 tasks, list, filter, and sort requests MUST
  complete within one second in at least 95 of 100 measured requests on the documented test
  machine.
- **NFR-003**: Invalid values MUST be rejected before task state changes; a rejected request
  MUST leave the task collection unchanged.
- **NFR-004**: A saved task MUST remain available with all fields unchanged after a clean
  application restart.
- **NFR-005**: Automated CI MUST run pytest with at least 80% line coverage, Ruff lint and
  format checks, Bandit, pip-audit, and a secret scan on the supported Python version.

### Acceptance Criteria

- **AC-001 (FR-001, FR-010)**: Creating a task with a 1-character title succeeds; an empty title, a title
  containing only whitespace, and a 201-character title each return HTTP 422.
- **AC-002 (FR-001, FR-002)**: A created task has a unique ID, UTC ISO 8601 creation date, Pending status,
  Medium priority when omitted, empty description when omitted, and no tags when omitted.
- **AC-003 (FR-001, FR-010)**: Creating a task with 20 valid tags succeeds; 21 tags or any blank or
  33-character tag returns HTTP 422. Repeated tags, including case-only variants, in a single
  request appear once in the stored task, retaining the first spelling.
- **AC-004 (FR-001, FR-010)**: A 5,000-character description after trimming is accepted; a 5,001-character description after trimming and a
  priority outside High, Medium, and Low each return HTTP 422.
- **AC-005 (FR-004, FR-010)**: Updating title, description, priority, or tags changes only the supplied
  editable fields. Empty updates and attempts to change ID or creation date are rejected with HTTP 422.
- **AC-006 (FR-003, FR-004, FR-006, FR-010)**: Retrieval returns HTTP 200 for existing tasks;
  unknown IDs return HTTP 404 for retrieval, update, completion, reopening, and deletion.
- **AC-007 (FR-005, FR-010)**: Deleting an existing task returns HTTP 204 and subsequent retrieval returns
  HTTP 404.
- **AC-008 (FR-006, FR-010)**: Marking a Pending task completed returns HTTP 200 with Completed status; marking
  it completed again returns HTTP 200 with the same status.
- **AC-009 (FR-003, FR-007, FR-010)**: Listing without filters returns all existing tasks. Filtering by one tag returns
  exactly tasks containing that tag, regardless of
  tag casing. Filtering by multiple tags returns tasks matching at least one requested tag.
- **AC-010 (FR-008)**: Sorting returns every High-priority task before Medium and every Medium before
  Low; ties follow the defined creation-date and ID order. Combined filter and sort results
  meet both conditions.
- **AC-011 (FR-009, NFR-004)**: A task created or updated before an application restart can be retrieved after
  restart with every field unchanged.
- **AC-012 (FR-010, FR-011, NFR-003)**: Every invalid request returns HTTP 422 in the documented error shape and leaves
  task data unchanged. Missing task errors use HTTP 404 in the same error shape.
- **AC-013 (FR-009, NFR-001)**: With no data file, startup provides an empty list. With malformed data, the API
  returns HTTP 500 in the documented error shape and leaves the malformed file unchanged.
- **AC-014 (FR-012)**: The v1 product can be used without authentication and does not include
  notification, multi-user, or cloud-database capabilities.
- **AC-015 (NFR-002)**: On the documented test machine and 1,000-task dataset, at least 95 of 100 list,
  filter, and sort requests finish in under one second.
- **AC-016 (FR-006, FR-010)**: Reopening a Completed task returns HTTP 200 with Pending status;
  reopening it again returns HTTP 200 with Pending status.
- **AC-017 (FR-004)**: Two concurrent updates to different fields of one task preserve both
  changes. If both update the same field, the value from the last serialized update is
  returned and persisted.
- **AC-018 (NFR-005)**: CI runs the pytest coverage gate, Ruff lint and format checks, Bandit,
  pip-audit, and the secret scan; the workflow fails if any check fails.

### Key Entities *(include if feature involves data)*

- **Task**: A single item of work with a system-assigned unique ID, required title, optional
  description, priority (High, Medium, or Low), zero or more tags, status (Pending or
  Completed), and immutable creation date.
- **Priority**: One of the ordered values High, Medium, and Low.
- **Tag**: A non-empty label of up to 32 characters used to categorize and filter tasks.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (FR-001-FR-008)**: Users can complete each supported task operation—create, list,
  retrieve, update, delete, complete, reopen, filter, and sort—with the documented result in
  100% of acceptance tests.
- **SC-002 (FR-009, NFR-004)**: 100% of tasks created before an application restart remain retrievable afterward
  with every field unchanged.
- **SC-003 (FR-010, NFR-003)**: 100% of invalid-input tests receive the documented validation error and leave
  task data unchanged.
- **SC-004 (NFR-002)**: At least 95 of 100 list, filter, and sort operations on a 1,000-task collection
  complete within one second on the documented test machine.
- **SC-005 (NFR-005)**: Every required CI quality check completes successfully before changes
  are accepted.

## Assumptions

- The API serves a single local task collection; users and access control are out of scope.
- IDs are generated by the system as UUIDs, and creation dates are stored in UTC.
- Title length is 1-200 characters after trimming; description length is 0-5,000 characters after trimming.
- A task may have 0-20 unique tags, each 1-32 characters after trimming; uniqueness ignores case and retains the first spelling.
- Updates are partial. Status changes only through the mark-completed and reopen operations,
  which transition tasks between Pending and Completed in either direction.
- Multiple requested tags use “match any” semantics, tag matching ignores case, sorting
  places High priority first, and users can reopen Completed tasks as Pending.
- Missing local data files initialize an empty collection; malformed data files are reported
  and preserved rather than silently discarded.
- Performance is evaluated on 1,000 tasks using the test machine documented with the results.
