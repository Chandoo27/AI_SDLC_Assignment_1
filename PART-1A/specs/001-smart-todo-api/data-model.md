# Data Model

## Task

The Task aggregate is the only persisted domain entity.

| Field | Type | Required | Validation / behavior |
|---|---|---:|---|
| `id` | UUID string | yes | Generated on create; immutable |
| `title` | string | yes | Trimmed; 1-200 characters |
| `description` | string | no | Trimmed or empty; 0-5,000 characters after trimming |
| `priority` | enum | no | `High`, `Medium`, or `Low`; default `Medium` |
| `tags` | string[] | no | 0-20 unique items after case-insensitive de-duplication; each trimmed, 1-32 characters; first spelling retained |
| `status` | enum | yes | `Pending` or `Completed`; default `Pending`; only status actions change it |
| `createdAt` | UTC ISO 8601 string | yes | Generated on create; immutable |

## TaskCreate

- `title`: required
- `description`: optional, defaults to `""`
- `priority`: optional, defaults to `Medium`
- `tags`: optional, defaults to `[]`

## TaskUpdate

- `title`: optional
- `description`: optional
- `priority`: optional
- `tags`: optional
- `id` and `createdAt` are not fields in the accepted request model
- Unknown supplied fields are rejected
- At least one editable field must be provided

## StatusTransition

- Complete: `Pending -> Completed`; `Completed -> Completed`
- Reopen: `Completed -> Pending`; `Pending -> Pending`

## Ordering

1. Priority rank: High, Medium, Low
2. `createdAt` ascending
3. `id` ascending lexical order

## Persistence Format

The configured JSON file contains a top-level task array.

```json
[
  {
    "id": "uuid",
    "title": "Example",
    "description": "",
    "priority": "Medium",
    "tags": [],
    "status": "Pending",
    "createdAt": "2026-11-19T13:30:00Z"
  }
]
```

Missing files initialize an empty collection. Malformed JSON or unreadable/mismatched data is a
server error and does not overwrite or remove the original file.
