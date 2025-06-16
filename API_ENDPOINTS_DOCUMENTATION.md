# Athlethium Training App - API Endpoints Documentation

## Overview

This document provides comprehensive details about all API endpoints available in the Athlethium Training App. The API is built using AWS API Gateway with Lambda functions and uses AWS Cognito for authentication.

**Base URL**: `https://api.athlethium.com`

**Authentication**: All endpoints (except webhooks and OAuth callbacks) require AWS Cognito authentication using JWT tokens.

## Table of Contents

1. [Authentication](#authentication)
2. [User Details](#user-details)
3. [Metrics](#metrics)
4. [Schedule](#schedule)
5. [Training Sessions](#training-sessions)
6. [Training Algorithm](#training-algorithm)
7. [Partner Integrations](#partner-integrations)
8. [Chat System](#chat-system)
9. [Error Responses](#error-responses)
10. [Data Models](#data-models)

---

## Authentication

All API requests must include a valid JWT token in the Authorization header:

```
Authorization: Bearer <jwt_token>
```

The token is obtained through AWS Cognito authentication and contains user information including the `sub` (user ID) claim.

---

## User Details

### Get User Details
**Endpoint**: `GET /details/get`

**Description**: Retrieves user profile information and account details.

**Authentication**: Required

**Request Parameters**: None (user identified from JWT token)

**Response**:
```json
{
  "statusCode": 200,
  "body": {
    "userId": "uuid",
    "email": "user@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "dateOfBirth": "1990-01-01",
    "gender": "male",
    "weight": 70.5,
    "height": 175,
    "fitnessLevel": "intermediate",
    "goals": ["weight_loss", "endurance"],
    "preferences": {
      "units": "metric",
      "timezone": "UTC"
    },
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-15T10:30:00Z"
  }
}
```

### Update User Details
**Endpoint**: `PUT /details/update`

**Description**: Updates user profile information.

**Authentication**: Required

**Request Body**:
```json
{
  "firstName": "John",
  "lastName": "Doe",
  "dateOfBirth": "1990-01-01",
  "gender": "male",
  "weight": 72.0,
  "height": 175,
  "fitnessLevel": "advanced",
  "goals": ["strength", "endurance"],
  "preferences": {
    "units": "metric",
    "timezone": "Europe/London"
  }
}
```

**Response**:
```json
{
  "statusCode": 200,
  "body": {
    "message": "User details updated successfully",
    "updatedFields": ["weight", "fitnessLevel", "goals", "preferences"]
  }
}
```

### Delete User Details
**Endpoint**: `DELETE /details/delete`

**Description**: Deletes user account and all associated data.

**Authentication**: Required

**Request Parameters**: None

**Response**:
```json
{
  "statusCode": 200,
  "body": {
    "message": "User account deleted successfully"
  }
}
```

---

## Metrics

### Get User Metrics
**Endpoint**: `GET /metrics/get`

**Description**: Retrieves training metrics including CTL (Chronic Training Load), ATL (Acute Training Load), TSB (Training Stress Balance), and fitness trends.

**Authentication**: Required

**Query Parameters**:
- `date` (optional): Date in YYYY-MM-DD format (defaults to current date)
- `period` (optional): Time period for metrics (7d, 30d, 90d) - defaults to 30d

**Response**:
```json
{
  "statusCode": 200,
  "body": {
    "date": "2024-01-15",
    "metrics": {
      "ctl": 45.2,
      "atl": 38.7,
      "tsb": 6.5,
      "fitness": 78.3,
      "fatigue": 32.1,
      "form": 46.2
    },
    "weeklyTrend": {
      "totalTSS": 287,
      "avgIntensity": 0.82,
      "totalDuration": 420,
      "workoutCount": 6
    },
    "sportBreakdown": {
      "cycling": {
        "tss": 156,
        "duration": 240,
        "count": 3
      },
      "running": {
        "tss": 98,
        "duration": 120,
        "count": 2
      },
      "swimming": {
        "tss": 33,
        "duration": 60,
        "count": 1
      }
    }
  }
}
```

### Update User Metrics
**Endpoint**: `PUT /metrics/update`

**Description**: Updates daily metrics data (typically called by training algorithm).

**Authentication**: Required

**Request Body**:
```json
{
  "date": "2024-01-15",
  "metrics": {
    "ctl": 45.2,
    "atl": 38.7,
    "tsb": 6.5,
    "fitness": 78.3,
    "fatigue": 32.1,
    "form": 46.2
  }
}
```

**Response**:
```json
{
  "statusCode": 200,
  "body": {
    "message": "Metrics updated successfully",
    "date": "2024-01-15"
  }
}
```

---

## Schedule

### Get User Schedule
**Endpoint**: `GET /schedule/get`

**Description**: Retrieves training schedule and planned workouts.

**Authentication**: Required

**Query Parameters**:
- `startDate` (optional): Start date in YYYY-MM-DD format
- `endDate` (optional): End date in YYYY-MM-DD format
- `sport` (optional): Filter by sport (cycling, running, swimming, strength, yoga)

**Response**:
```json
{
  "statusCode": 200,
  "body": {
    "schedule": [
      {
        "date": "2024-01-15",
        "workouts": [
          {
            "workoutId": "uuid",
            "sport": "cycling",
            "type": "endurance",
            "duration": 60,
            "intensity": 0.75,
            "tss": 65,
            "description": "Zone 2 base ride",
            "status": "planned"
          }
        ]
      },
      {
        "date": "2024-01-16",
        "workouts": [
          {
            "workoutId": "uuid",
            "sport": "running",
            "type": "intervals",
            "duration": 45,
            "intensity": 0.90,
            "tss": 58,
            "description": "5x 1km intervals",
            "status": "planned"
          }
        ]
      }
    ],
    "summary": {
      "totalWorkouts": 12,
      "totalTSS": 687,
      "totalDuration": 540,
      "sportDistribution": {
        "cycling": 5,
        "running": 4,
        "swimming": 2,
        "strength": 1
      }
    }
  }
}
```

### Update User Schedule
**Endpoint**: `PUT /schedule/update`

**Description**: Updates training schedule with new or modified workouts.

**Authentication**: Required

**Request Body**:
```json
{
  "date": "2024-01-15",
  "workouts": [
    {
      "workoutId": "uuid",
      "sport": "cycling",
      "type": "endurance",
      "duration": 90,
      "intensity": 0.70,
      "tss": 78,
      "description": "Long base ride",
      "status": "planned"
    }
  ]
}
```

**Response**:
```json
{
  "statusCode": 200,
  "body": {
    "message": "Schedule updated successfully",
    "date": "2024-01-15",
    "updatedWorkouts": 1
  }
}
```

---

## Training Sessions

### Add Training Session
**Endpoint**: `POST /session/add`

**Description**: Creates a new training session/workout.

**Authentication**: Required

**Request Body**:
```json
{
  "sport": "cycling",
  "type": "endurance",
  "date": "2024-01-15",
  "startTime": "08:00",
  "duration": 90,
  "plannedIntensity": 0.75,
  "plannedTSS": 85,
  "description": "Morning base ride",
  "notes": "Felt good, maintained steady effort"
}
```

**Response**:
```json
{
  "statusCode": 200,
  "body": {
    "message": "Training session created successfully",
    "workoutId": "uuid",
    "session": {
      "workoutId": "uuid",
      "userId": "uuid",
      "sport": "cycling",
      "type": "endurance",
      "date": "2024-01-15",
      "startTime": "08:00",
      "duration": 90,
      "plannedIntensity": 0.75,
      "plannedTSS": 85,
      "completed": false,
      "createdAt": "2024-01-15T06:30:00Z"
    }
  }
}
```

### Get Training Session
**Endpoint**: `GET /session/get`

**Description**: Retrieves details of a specific training session.

**Authentication**: Required

**Request Body**:
```json
{
  "workoutId": "uuid"
}
```

**Response**:
```json
{
  "statusCode": 200,
  "body": {
    "workout": {
      "workoutId": "uuid",
      "userId": "uuid",
      "sport": "cycling",
      "type": "endurance",
      "date": "2024-01-15",
      "startTime": "08:00",
      "duration": 90,
      "plannedIntensity": 0.75,
      "plannedTSS": 85,
      "actualIntensity": 0.78,
      "actualTSS": 88,
      "completed": true,
      "description": "Morning base ride",
      "notes": "Felt good, maintained steady effort",
      "metrics": {
        "avgHeartRate": 145,
        "maxHeartRate": 162,
        "avgPower": 225,
        "maxPower": 320,
        "calories": 650
      },
      "createdAt": "2024-01-15T06:30:00Z",
      "completedAt": "2024-01-15T10:00:00Z"
    }
  }
}
```

### Update Training Session
**Endpoint**: `PUT /session/update`

**Description**: Updates an existing training session with actual workout data.

**Authentication**: Required

**Request Body**:
```json
{
  "workoutId": "uuid",
  "actualDuration": 95,
  "actualIntensity": 0.78,
  "actualTSS": 88,
  "completed": true,
  "notes": "Great session, pushed a bit harder than planned",
  "metrics": {
    "avgHeartRate": 145,
    "maxHeartRate": 162,
    "avgPower": 225,
    "maxPower": 320,
    "calories": 650,
    "distance": 45.2
  }
}
```

**Response**:
```json
{
  "statusCode": 200,
  "body": {
    "message": "Training session updated successfully",
    "workoutId": "uuid",
    "updatedFields": ["actualDuration", "actualIntensity", "actualTSS", "completed", "notes", "metrics"]
  }
}
```

### Delete Training Session
**Endpoint**: `DELETE /session/delete`

**Description**: Deletes a training session.

**Authentication**: Required

**Request Body**:
```json
{
  "workoutId": "uuid"
}
```

**Response**:
```json
{
  "statusCode": 200,
  "body": {
    "message": "Training session deleted successfully",
    "workoutId": "uuid"
  }
}
```

---

## Training Algorithm

### Get User Training
**Endpoint**: `GET /training/get`

**Description**: Retrieves training plans and recommendations.

**Authentication**: Required

**Response**:
```json
{
  "statusCode": 200,
  "body": {
    "currentPlan": {
      "name": "Base Building Phase",
      "startDate": "2024-01-01",
      "endDate": "2024-02-28",
      "phase": "base",
      "weeklyTSS": 350,
      "focus": ["aerobic_base", "endurance"]
    },
    "recommendations": [
      {
        "date": "2024-01-16",
        "workout": {
          "sport": "cycling",
          "type": "tempo",
          "duration": 75,
          "intensity": 0.85,
          "tss": 78,
          "description": "Tempo intervals - 3x 15min @ FTP"
        },
        "reasoning": "Building aerobic power while maintaining base fitness"
      }
    ],
    "adaptations": {
      "lastUpdated": "2024-01-15T02:00:00Z",
      "changes": [
        "Reduced intensity due to accumulated fatigue",
        "Added recovery day on Wednesday"
      ]
    }
  }
}
```

### Run Training Algorithm
**Endpoint**: `POST /training/run`

**Description**: Manually triggers the training algorithm to generate new recommendations (normally runs automatically daily at 2am UTC).

**Authentication**: Required

**Request Body**:
```json
{
  "forceUpdate": true,
  "targetDate": "2024-01-15"
}
```

**Response**:
```json
{
  "statusCode": 200,
  "body": {
    "message": "Training algorithm executed successfully",
    "executionTime": "2024-01-15T10:30:00Z",
    "usersProcessed": 1,
    "workoutsGenerated": 7,
    "adaptationsMade": 2
  }
}
```

---

## Partner Integrations

*Note: These endpoints are currently under development and not yet implemented.*

### Strava Integration

#### Initiate Strava OAuth
**Endpoint**: `POST /partner/strava/auth/authorize`
**Status**: Planned

#### Strava OAuth Callback
**Endpoint**: `POST /partner/strava/auth/callback`
**Status**: Planned

#### Refresh Strava Token
**Endpoint**: `POST /partner/strava/auth/refresh`
**Status**: Planned

#### Deauthorize Strava
**Endpoint**: `POST /partner/strava/auth/deauthorize`
**Status**: Planned

#### Strava Webhook Handler
**Endpoint**: `POST /partner/strava/webhooks`
**Status**: Planned
**Authentication**: None (webhook endpoint)

### Wahoo Integration

#### Wahoo Webhook Handler
**Endpoint**: `POST /partner/wahoo/webhooks`
**Status**: Planned
**Authentication**: None (webhook endpoint)

### Garmin Integration

*Endpoints to be defined*

---

## Chat System

*Note: These endpoints are currently under development and not yet implemented.*

### Get Chats
**Endpoint**: `GET /chats`
**Status**: Planned

### Get Chat History
**Endpoint**: `GET /chats/history`
**Status**: Planned

### Send Chat Message
**Endpoint**: `POST /chats/send`
**Status**: Planned

---

## Error Responses

All endpoints return consistent error response format:

### 400 Bad Request
```json
{
  "statusCode": 400,
  "body": {
    "error": "Invalid request parameters",
    "details": "workoutId is required in request body"
  }
}
```

### 401 Unauthorized
```json
{
  "statusCode": 401,
  "body": {
    "error": "Unauthorized",
    "details": "Invalid or missing authentication token"
  }
}
```

### 403 Forbidden
```json
{
  "statusCode": 403,
  "body": {
    "error": "Forbidden",
    "details": "Access denied for this resource"
  }
}
```

### 404 Not Found
```json
{
  "statusCode": 404,
  "body": {
    "error": "Resource not found",
    "details": "Workout with specified ID does not exist"
  }
}
```

### 500 Internal Server Error
```json
{
  "statusCode": 500,
  "body": {
    "error": "Internal server error",
    "details": "An unexpected error occurred while processing the request"
  }
}
```

---

## Data Models

### User Profile
```json
{
  "userId": "string (uuid)",
  "email": "string",
  "firstName": "string",
  "lastName": "string",
  "dateOfBirth": "string (YYYY-MM-DD)",
  "gender": "string (male|female|other)",
  "weight": "number (kg)",
  "height": "number (cm)",
  "fitnessLevel": "string (beginner|intermediate|advanced)",
  "goals": "array of strings",
  "preferences": {
    "units": "string (metric|imperial)",
    "timezone": "string"
  },
  "createdAt": "string (ISO 8601)",
  "updatedAt": "string (ISO 8601)"
}
```

### Training Session
```json
{
  "workoutId": "string (uuid)",
  "userId": "string (uuid)",
  "sport": "string (cycling|running|swimming|strength|yoga)",
  "type": "string (endurance|intervals|tempo|recovery|race)",
  "date": "string (YYYY-MM-DD)",
  "startTime": "string (HH:MM)",
  "duration": "number (minutes)",
  "plannedIntensity": "number (0-1)",
  "plannedTSS": "number",
  "actualIntensity": "number (0-1)",
  "actualTSS": "number",
  "completed": "boolean",
  "description": "string",
  "notes": "string",
  "metrics": {
    "avgHeartRate": "number (bpm)",
    "maxHeartRate": "number (bpm)",
    "avgPower": "number (watts)",
    "maxPower": "number (watts)",
    "calories": "number",
    "distance": "number (km)"
  },
  "createdAt": "string (ISO 8601)",
  "completedAt": "string (ISO 8601)"
}
```

### Training Metrics
```json
{
  "date": "string (YYYY-MM-DD)",
  "userId": "string (uuid)",
  "ctl": "number (Chronic Training Load)",
  "atl": "number (Acute Training Load)",
  "tsb": "number (Training Stress Balance)",
  "fitness": "number (0-100)",
  "fatigue": "number (0-100)",
  "form": "number (-100 to 100)"
}
```

### Sports Supported
- `cycling`: Road cycling, mountain biking, indoor cycling
- `running`: Road running, trail running, treadmill
- `swimming`: Pool swimming, open water swimming
- `strength`: Weight training, bodyweight exercises
- `yoga`: Various yoga practices

### Workout Types
- `endurance`: Long, steady efforts at moderate intensity
- `intervals`: High-intensity intervals with recovery periods
- `tempo`: Sustained efforts at moderate-high intensity
- `recovery`: Easy, low-intensity sessions
- `race`: Competition or race-simulation efforts

---

## Rate Limits

- **General API calls**: 1000 requests per hour per user
- **Training algorithm**: 10 requests per hour per user
- **Webhook endpoints**: 10,000 requests per hour (across all users)

## API Versioning

Current API version: `v1`

All endpoints are currently unversioned but future versions will use path versioning:
- `https://api.athlethium.com/v1/details/get`
- `https://api.athlethium.com/v2/details/get`

## Support

For API support, please contact: `api-support@athlethium.com`

## Changelog

### Version 1.0.0 (Current)
- Initial API release
- Core endpoints for user management, training sessions, metrics, and scheduling
- AWS Cognito authentication integration
- Training algorithm automation

### Planned Features
- Partner integrations (Strava, Garmin, Wahoo)
- AI-powered chat system
- Real-time notifications
- Advanced analytics endpoints
- Mobile app-specific optimizations
