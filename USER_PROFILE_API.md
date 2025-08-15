# User Profile API Documentation

This document describes the user profile endpoints available in the TaskFlow application.

## Authentication

All user profile endpoints require authentication via Token Authentication. Include the token in the Authorization header:

```
Authorization: Token your_token_here
```

## Endpoints

### 1. Get User Data
**GET** `/api/auth/user-data/`

Retrieves complete user data including profile information.

**Response:**
```json
{
    "message": "User data retrieved successfully",
    "data": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "date_joined": "2024-01-15T10:30:00Z",
        "last_login": "2024-01-15T15:45:00Z",
        "is_active": true,
        "full_name": "John Doe",
        "profile_picture_url": "/media/profile_pictures/john_profile.jpg",
        "profile": {
            "bio": "Software developer passionate about Django",
            "phone_number": "+1234567890",
            "birth_date": "1990-05-15",
            "location": "New York, NY",
            "website": "https://johndoe.dev",
            "profile_picture": "/media/profile_pictures/john_profile.jpg",
            "is_profile_public": true,
            "show_email": false
        }
    }
}
```

### 2. Update User Data
**PUT/PATCH** `/api/auth/user-update/`

Updates user basic information and profile data.

**Request Body (all fields optional for PATCH):**
```json
{
    "email": "newemail@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "bio": "Updated bio text",
    "phone_number": "+1234567890",
    "birth_date": "1990-05-15",
    "location": "Los Angeles, CA",
    "website": "https://johndoe.dev",
    "is_profile_public": true,
    "show_email": false
}
```

**Note:** For profile picture updates, use `multipart/form-data` content type and include the `profile_picture` field as a file upload.

**Response:**
```json
{
    "message": "User data updated successfully",
    "data": {
        // Same structure as GET /user-data/ response
    }
}
```

### 3. Legacy Profile Endpoint (Backward Compatibility)
**GET/PUT/PATCH** `/api/auth/profile/`

Original profile endpoint with basic user information only.

## Usage Examples

### Get User Data
```bash
curl -X GET http://localhost:8000/api/auth/user-data/ \
  -H "Authorization: Token your_token_here"
```

### Update User Profile (Partial Update)
```bash
curl -X PATCH http://localhost:8000/api/auth/user-update/ \
  -H "Authorization: Token your_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jane",
    "bio": "Updated bio text",
    "location": "San Francisco, CA"
  }'
```

### Update Profile Picture
```bash
curl -X PATCH http://localhost:8000/api/auth/user-update/ \
  -H "Authorization: Token your_token_here" \
  -F "profile_picture=@/path/to/image.jpg"
```

### Complete Profile Update (PUT)
```bash
curl -X PUT http://localhost:8000/api/auth/user-update/ \
  -H "Authorization: Token your_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "jane@example.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "bio": "Full-stack developer",
    "phone_number": "+9876543210",
    "birth_date": "1992-08-20",
    "location": "Seattle, WA",
    "website": "https://janesmith.dev",
    "is_profile_public": true,
    "show_email": true
  }'
```

## Field Validation

- **email**: Must be a valid email address and unique across all users
- **phone_number**: Maximum 15 characters
- **bio**: Maximum 500 characters
- **location**: Maximum 100 characters
- **website**: Must be a valid URL format
- **birth_date**: Must be in YYYY-MM-DD format
- **profile_picture**: Supported formats: JPG, PNG, GIF, WebP

## Error Responses

### 400 Bad Request
```json
{
    "email": ["A user with this email already exists."],
    "bio": ["Ensure this field has no more than 500 characters."]
}
```

### 401 Unauthorized
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
    "detail": "You do not have permission to perform this action."
}
```

## Profile Privacy Settings

- **is_profile_public**: Controls whether other users can view the profile
- **show_email**: Controls whether the email address is displayed in public profile views

## Default Values

When a user is created, a UserProfile is automatically created with these default values:
- **is_profile_public**: `true`
- **show_email**: `false`
- All other fields are empty/null

## File Upload Notes

- Profile pictures are uploaded to `/media/profile_pictures/`
- If no profile picture is uploaded, `/static/images/default-avatar.png` is used as the default
- When updating via API, existing profile pictures are replaced by new uploads
- The `profile_picture_url` field in responses provides the full URL to the image
