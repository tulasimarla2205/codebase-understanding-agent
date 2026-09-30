# Sample Auth Microservice

A Node.js / Express microservice providing token-based authentication and user registration.

## Architecture & Flow
1. **Entry Point (`src/index.js`)**: Initializes Express server, attaches middleware, and mounts `/api/auth` routes.
2. **Routing (`src/routes/authRoutes.js`)**: Maps POST `/register`, POST `/login`, and GET `/profile` endpoints to controller actions.
3. **Controller (`src/controllers/authController.js`)**: Validates incoming payload and invokes `authService`.
4. **Service (`src/services/authService.js`)**: Has business logic for password hashing via `bcryptjs` and token signing via `jsonwebtoken`.
5. **Middleware (`src/middleware/authMiddleware.js`)**: Intercepts requests, validates Bearer JWT token, and attaches `req.user`.

## Running
```bash
npm install
npm start
```
