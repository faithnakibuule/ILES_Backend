# JWT Token Structure in ILES

When a user logs in, the API returns two tokens:

## Access Token
- **Expires in:** 5 minutes (default, configurable)
- **Use:** Send in every API request header as `Authorization: Bearer <token>`
- **Contains (decoded payload):**
  - `user_id` — the user's database ID
  - `email` — user's email address
  - `role` — one of: student, workplace_supervisor, academic_supervisor, admin
  - `full_name` — user's display name
  - `exp` — expiry timestamp

## Refresh Token
- **Expires in:** 1 day (default)
- **Use:** Send to `/api/auth/token/refresh/` to get a new access token when the old one expires

## How to test in Postman
1. Call the Login endpoint → copy the `access` token from the response
2. In subsequent requests, go to the "Authorization" tab → select "Bearer Token" → paste the token