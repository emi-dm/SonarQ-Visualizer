# Security Notes

## Threat Model (Summary)

This application is designed for local or trusted environments. It does not include multi-user authentication or server-side token storage. The primary security considerations are token exposure, transport security, and XSS prevention.

## Token Handling

- Tokens are stored in browser localStorage.
- Tokens are never persisted in the backend database.
- The backend does not log tokens, even in debug mode.

## Transport Security

- SonarQube connections should use HTTPS.
- If HTTP is used, the UI should warn the user (non-production only).

## Content Security Policy (CSP)

The backend sets CSP headers to reduce XSS risk. The policy allows self-hosted scripts and styles, and inline styles when needed for the current frontend.

## Operational Guidance

- Use trusted browsers and devices.
- Avoid running untrusted scripts on the same origin.
- Rotate SonarQube tokens periodically.
- Prefer running behind a local reverse proxy with HTTPS if exposing the app on a network.
