const express = require('express');
const router = express.Router();
const authController = require('../controllers/authController');
const { authenticateToken } = require('../middleware/authMiddleware');

// Public endpoints
router.post('/register', authController.handleRegister);
router.post('/login', authController.handleLogin);

// Protected endpoints
router.get('/profile', authenticateToken, authController.handleProfile);

module.exports = router;
