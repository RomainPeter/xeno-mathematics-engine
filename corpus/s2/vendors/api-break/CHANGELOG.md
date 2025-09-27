# Changelog

## [2.0.0] - 2024-01-01

### BREAKING CHANGES
- **POST /api/v2/users**: Added required `email_verification_token` parameter
  - Old clients using `/api/v1/users` will continue to work
  - New clients must include `email_verification_token` in requests to `/api/v2/users`

### Added
- Email verification token validation
- API versioning support
- Backward compatibility tests

### Changed
- Endpoint path changed from `/api/v1/users` to `/api/v2/users`
- Request validation now requires `email_verification_token`

### Migration Guide
To migrate from v1 to v2:
1. Update endpoint URL from `/api/v1/users` to `/api/v2/users`
2. Include `email_verification_token` in request payload
3. Update client code to handle new response format

## [1.0.0] - 2023-12-01

### Added
- Initial API implementation
- User creation endpoint
- Basic validation
